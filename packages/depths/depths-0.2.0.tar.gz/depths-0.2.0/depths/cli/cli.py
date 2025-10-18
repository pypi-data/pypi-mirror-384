"""
Depths command-line interface.

Commands:
  • init    → create a new instance layout and baseline configs
  • start   → run uvicorn serving depths.cli.app:app (foreground/background)
  • stop    → terminate a background server via stored PID
  • status  → show health from the running server
  • view    → read recent rows from a chosen OTel table

Notes:
    This version removes add-on handling from the CLI. Schema customization
    is provided through programmatic configuration, not CLI flags.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path
from contextlib import contextmanager
import multiprocessing as mp
from typing import Optional, Dict, List

import polars as pl
import typer
import httpx
import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from depths.core.config import S3Config, DepthsLoggerOptions
from depths.core.logger import DepthsLogger

app = typer.Typer(help="Depths CLI")

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 4318

def _instance_paths(instance_id: str, instance_dir: Path) -> Dict[str, Path]:
    """
    Compute canonical paths for an instance and ensure config directory exists.

    Returns a dict with keys: 'root', 'cfg', 'pid', 'log'.
    """
    inst_root = (instance_dir / instance_id).resolve()
    cfg_dir = inst_root / "configs"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    pid_file = cfg_dir / "server.pid"
    log_file = inst_root / "server.log"
    return {"root": inst_root, "cfg": cfg_dir, "pid": pid_file, "log": log_file}

@contextmanager
def _status(msg: str = "Please wait..."):
    """
    Display a transient progress spinner.
    """
    console = Console()
    try:
        with console.status(msg, spinner="dots"):
            yield
    except Exception:
        typer.echo(msg)
        yield

def _init_process(instance_id: str, instance_dir: str) -> None:
    """
    Perform the heavy bootstrap in a clean child process.
    """
    try:
        s3 = S3Config.from_env()
    except Exception:
        s3 = None

    DepthsLogger(
        instance_id=instance_id,
        instance_dir=str(instance_dir),
        s3=s3,
        options=DepthsLoggerOptions(init_early_terminate=True),
    )

@app.command("init")
def init(
    instance_id: str = typer.Option("default", "--instance-id", "-I", help="Unique ID for this instance"),
    instance_dir: Path = typer.Option(Path("./depths_data"), "--dir", "-D", help="Root directory for local data"),
) -> None:
    """
    Initialize a new Depths instance on disk.
    """
    instance_dir = instance_dir.resolve()
    inst_root = instance_dir / instance_id
    if inst_root.exists():
        typer.echo(f"Instance '{instance_id}' already exists at {inst_root}", err=True)
        raise typer.Exit(code=1)

    _instance_paths(instance_id, instance_dir)

    ctx = mp.get_context("spawn")
    proc = ctx.Process(
        target=_init_process,
        args=(instance_id, str(instance_dir)),
        name="depths-init",
        daemon=False,
    )

    with _status("Creating instance layout and baseline configs..."):
        proc.start()
        proc.join()

    if proc.exitcode != 0:
        typer.echo(
            f"Initialization failed (exit code {proc.exitcode}). "
            f"Check logs under {inst_root}.",
            err=True,
        )
        raise typer.Exit(code=proc.exitcode or 1)

    typer.echo(f"Initialized depths instance '{instance_id}' at {inst_root}")
    try:
        sys.stdout.flush()
    except Exception:
        pass

@app.command("start")
def start(
    instance_id: str = typer.Option("default", "--instance-id","-I", help="Instance to start"),
    instance_dir: Path = typer.Option(Path("./depths_data"), "--dir","-D", help="Root directory for instance data"),
    host: str = typer.Option(DEFAULT_HOST, "--host","-H", help="Bind host for OTLP/HTTP"),
    port: int = typer.Option(DEFAULT_PORT, "--port","-P", help="Bind port for OTLP/HTTP"),
    reload: bool = typer.Option(False, "--reload", "-R", help="Auto-reload server on code changes"),
    foreground: bool = typer.Option(False, "--foreground", "-F", help="Run in foreground with logs in terminal"),
) -> None:
    """
    Start the OTLP/HTTP server (depths.cli.app:app) via uvicorn.
    """
    instance_dir = instance_dir.resolve()

    if not (instance_dir / instance_id).exists():
        typer.echo(
            f"Instance '{instance_id}' does not exist at {(instance_dir / instance_id)}. "
            f"Run 'depths init -I {instance_id}' first.",
            err=True,
        )
        raise typer.Exit(code=1)

    paths = _instance_paths(instance_id, instance_dir)

    os.environ["DEPTHS_INSTANCE_ID"] = instance_id
    os.environ["DEPTHS_INSTANCE_DIR"] = str(instance_dir)

    if foreground:
        import uvicorn
        typer.echo(f"Starting depths server for '{instance_id}' on http://{host}:{port} (foreground)...")
        uvicorn.run(
            "depths.cli.app:app",
            host=host,
            port=port,
            log_level="info",
            reload=reload,
        )
        return

    if reload:
        typer.echo("`--reload` is only supported with `--foreground` to ensure correct PID handling.", err=True)
        raise typer.Exit(code=2)

    if paths["pid"].exists():
        typer.echo(f"Server already running (pid file {paths['pid']}).", err=True)
        raise typer.Exit(code=1)

    env = os.environ.copy()
    cmd = [
        sys.executable, "-m", "uvicorn", "depths.cli.app:app",
        "--host", host, "--port", str(port),
        "--log-level", "info",
    ]

    logf = open(paths["log"], "a", encoding="utf-8")
    proc = subprocess.Popen(cmd, env=env, stdout=logf, stderr=logf, close_fds=True)

    serving_pid = proc.pid
    try:
        import time
        time.sleep(0.35)
        try:
            import psutil  # type: ignore
            p = psutil.Process(proc.pid)
            kids = p.children(recursive=True)
            if kids:
                serving_pid = kids[-1].pid
        except Exception:
            pass
    finally:
        paths["pid"].write_text(str(serving_pid))

    typer.echo(f"Started depths server for '{instance_id}' on http://{host}:{port} (pid={serving_pid}). Logs: {paths['log']}")

@app.command("view")
def view(
    instance_id: str = typer.Option("default", "--instance-id", "-I", help="Instance to read from"),
    instance_dir: Path = typer.Option(Path("./depths_data"), "--dir", "-D", help="Root directory for instance data"),
    storage: str = typer.Option("auto", "--storage", "-S", help="Storage backend to read from: auto | local | s3"),
    rows: int = typer.Option(10, "--rows", "-n", min=1, help="Show the latest N rows by event_ts"),
    table: str | None = typer.Option(None, "--table", "-t", help="One of: spans | span_events | span_links | logs | metrics_points | metrics_hist"),
    select: List[str] | None = typer.Option(None, "--select", "-s", help="Column to include (repeatable). Example: -s trace_id -s span_id"),
    date_from: str | None = typer.Option(None, "--date-from", help="Start UTC date YYYY-MM-DD (inclusive)"),
    date_to: str | None = typer.Option(None, "--date-to", help="End UTC date YYYY-MM-DD (inclusive)"),
) -> None:
    """
    View the latest N persisted rows from an OTel table.
    """
    allowed = {
        "1": "spans",
        "2": "span_events",
        "3": "span_links",
        "4": "logs",
        "5": "metrics_points",
        "6": "metrics_hist",
        "spans": "spans",
        "span_events": "span_events",
        "span_links": "span_links",
        "logs": "logs",
        "metrics_points": "metrics_points",
        "metrics_hist": "metrics_hist",
    }
    pretty_names = {
        "spans": "Spans",
        "span_events": "Span Events",
        "span_links": "Span Links",
        "logs": "Logs",
        "metrics_points": "Metric Points",
        "metrics_hist": "Metric Histograms",
    }

    inst_root = instance_dir / instance_id
    if not inst_root.exists():
        typer.echo(f"Instance '{instance_id}' not found at {inst_root}", err=True)
        raise typer.Exit(code=1)

    if table:
        key = table.strip().lower()
        sel = allowed.get(key)
        if not sel:
            typer.echo("Invalid --table. Choose one of: spans | span_events | span_links | logs | metrics_points | metrics_hist", err=True)
            raise typer.Exit(code=2)
        table_name = sel
    else:
        typer.echo("Select OTel table to view:")
        for i, key in enumerate(["spans","span_events","span_links","logs","metrics_points","metrics_hist"], start=1):
            typer.echo(f"  {i}. {pretty_names[key]}")
        choice = typer.prompt("Enter a number (1-6)", default=1)
        sel = allowed.get(str(choice).strip())
        if not sel:
            typer.echo("Invalid selection.", err=True)
            raise typer.Exit(code=2)
        table_name = sel

    with _status("Fetching telemetry rows..."):
        try:
            s3 = None
            try:
                s3 = S3Config.from_env()
            except Exception:
                s3 = None
            opts = DepthsLoggerOptions(
                auto_start=False,
                install_signal_handlers=False,
                lazy_start_on_first_log=False,
                atexit_hook=False,
                shipper_enabled=False,
            )
            logger = DepthsLogger(instance_id=instance_id, instance_dir=str(instance_dir), s3=s3, options=opts)
        except Exception as e:
            typer.echo(f"Failed to construct DepthsLogger: {e}", err=True)
            raise typer.Exit(code=3)

        try:
            lf = getattr(logger, f"{table_name}_lazy")(date_from=date_from, date_to=date_to, storage=storage)
            lf = lf.sort("event_ts", descending=True).limit(int(rows))
            if select:
                lf = lf.select([pl.col(c) for c in select])
            df = lf.collect()
        except Exception as e:
            typer.echo(f"Failed to read {table_name}: {e}", err=True)
            raise typer.Exit(code=4)

    if df.height == 0:
        typer.echo(f"No rows found in {pretty_names[table_name]} for the selected range.")
        raise typer.Exit(code=0)

    typer.echo(f"{pretty_names[table_name]} · latest {min(rows, df.height)} rows (event_ts desc)")
    typer.echo(str(df))

@app.command("status")
def status(
    host: str = typer.Option("127.0.0.1", "--host", "-H", help="Host of the running depths server"),
    port: int = typer.Option(4318, "--port", "-P", help="Port of the running depths server"),
    timeout: float = typer.Option(5.0, "--timeout", "-T", help="HTTP timeout in seconds"),
) -> None:
    """
    Show a colorized health snapshot of the running depths server.
    """
    url = f"http://{host}:{port}/healthz"
    console = Console()

    with _status("Fetching live health stats..."):
        try:
            resp = httpx.get(url, timeout=timeout)
            resp.raise_for_status()
        except httpx.TimeoutException as e:
            console.print(f"[bold red]Timed out[/bold red] connecting to {url} after {timeout}s: {e}")
            raise typer.Exit(code=3)
        except httpx.RequestError as e:
            console.print(f"[bold red]Request error[/bold red] contacting {url}: {e}")
            raise typer.Exit(code=3)
        except httpx.HTTPStatusError as e:
            console.print(f"[bold red]HTTP {e.response.status_code}[/bold red] from {url}")
            raise typer.Exit(code=3)

        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            console.print(f"[bold red]Invalid JSON[/bold red] from {url}: {e}")
            raise typer.Exit(code=3)

        ok = bool(data.get("ok"))
        logger = data.get("logger") or {}

        started = bool(logger.get("started", False))
        overall_ok = started
        for _name, m in (logger.get("aggregators") or {}).items():
            if not m.get("delta_init_ok", False) or m.get("delta_last_error"):
                overall_ok = False
                break

        inst = logger.get("instance_id", "unknown")
        day = logger.get("current_day_utc", "unknown")
        header = Text.assemble(
            ("Depths ", "bold"),
            ("status  ", "dim"),
            (f"http://{host}:{port}", "cyan"),
            "\n",
            ("instance: ", "dim"), (str(inst), "bold"),
            ("   day: ", "dim"), (str(day), "bold"),
            ("   started: ", "dim"), (str(bool(started)), "bold green" if started else "bold red"),
        )

    console.print(Panel(header, title="[bold]Health[/bold]", border_style="green" if overall_ok else "red"))

    prod = logger.get("producers") or {}
    if isinstance(prod, dict) and prod:
        t = Table(title="Producers", expand=True)
        t.add_column("Table", style="bold")
        t.add_column("Accepted", justify="right")
        t.add_column("Schema↓", justify="right")
        t.add_column("Payload↓", justify="right")
        t.add_column("Date↓", justify="right")
        t.add_column("Dropped", justify="right")
        t.add_column("Queue", justify="right")
        t.add_column("Oldest Age (s)", justify="right")
        for name, m in sorted(prod.items()):
            qsize = int(m.get("queue_size") or 0)
            dropped = int(m.get("dropped_capacity") or 0)
            q_style = "red" if qsize > 0 else "green"
            d_style = "red" if dropped > 0 else "green"
            t.add_row(
                name,
                str(m.get("accepted", 0)),
                str(m.get("rejected_schema", 0)),
                str(m.get("rejected_payload_json", 0)),
                str(m.get("rejected_date_mismatch", 0)),
                f"[{d_style}]{dropped}[/{d_style}]",
                f"[{q_style}]{qsize}[/{q_style}]",
                f"{m.get('oldest_age_seconds', '0')}",
            )
        console.print(t)
    else:
        console.print("[yellow]No producer metrics available[/yellow]")

    aggs = logger.get("aggregators") or {}
    if isinstance(aggs, dict) and aggs:
        t = Table(title="Aggregators", expand=True)
        t.add_column("Table", style="bold")
        t.add_column("Flushes", justify="right")
        t.add_column("Sched Total", justify="right")
        t.add_column("Persisted", justify="right")
        t.add_column("Last Flush Rows", justify="right")
        t.add_column("Last Commit (s)", justify="right")
        t.add_column("Writer Q", justify="right")
        t.add_column("Delta OK", justify="center")
        t.add_column("Last Error", justify="left")
        t.add_column("Table Path", overflow="fold")

        for name, m in sorted(aggs.items()):
            wq = int(m.get("writer_queue_size") or 0)
            ok_flag = bool(m.get("delta_init_ok"))
            err = m.get("delta_last_error")
            wq_style = "red" if wq > 0 else "green"
            ok_style = "green" if ok_flag else "red"
            err_cell = f"[red]{err}[/red]" if err else "[green]-[/green]"
            t.add_row(
                name,
                str(m.get("flushes", 0)),
                str(m.get("rows_scheduled_total", 0)),
                str(m.get("rows_persisted_total", 0)),
                str(m.get("rows_last_flush", 0)),
                str(m.get("last_commit_seconds", "")),
                f"[{wq_style}]{wq}[/{wq_style}]",
                f"[{ok_style}]{ok_flag}[/{ok_style}]",
                err_cell,
                str(m.get("table_path", "")),
            )
        console.print(t)
    else:
        console.print("[yellow]No aggregator metrics available[/yellow]")

    if not overall_ok:
        raise typer.Exit(code=4)

@app.command("stop")
def stop(
    instance_id: str = typer.Option("default", "--instance-id", "-I", help="Instance to stop"),
    instance_dir: Path = typer.Option(Path("./depths_data"), "--dir", "-D", help="Root directory for instance data"),
    force: bool = typer.Option(False, "--force", "-F", help="Force kill if graceful stop fails"),
) -> None:
    """
    Stop a background server using the stored PID.
    """
    instance_dir = instance_dir.resolve()
    paths = _instance_paths(instance_id, instance_dir)

    if not paths["pid"].exists():
        typer.echo("No pid file found; server not running?", err=True)
        raise typer.Exit(code=1)

    try:
        pid = int(paths["pid"].read_text().strip())
    except Exception:
        typer.echo("Invalid pid file.", err=True)
        raise typer.Exit(code=1)

    try:
        try:
            import psutil  # type: ignore
            procs = []
            try:
                p = psutil.Process(pid)
                procs.append(p)
                procs.extend(p.children(recursive=True))
            except psutil.NoSuchProcess:
                typer.echo("Process not found; cleaning up pid file.")
            else:
                for pr in reversed(procs):
                    try:
                        pr.terminate()
                    except psutil.NoSuchProcess:
                        pass
                gone, alive = psutil.wait_procs(procs, timeout=3.0)
                if alive:
                    for pr in alive:
                        try:
                            pr.kill()
                        except psutil.NoSuchProcess:
                            pass
        except ImportError:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                typer.echo("Process not found; cleaning up pid file.")
            except Exception as e:
                if force:
                    try:
                        os.kill(pid, signal.SIGKILL if hasattr(signal, "SIGKILL") else signal.SIGTERM)
                    except Exception as e2:
                        typer.echo(f"Force kill failed: {e2}", err=True)
                        raise typer.Exit(code=1)
                else:
                    typer.echo(f"Failed to stop process: {e}", err=True)
                    raise typer.Exit(code=1)
    finally:
        try:
            paths["pid"].unlink(missing_ok=True)
        except Exception:
            pass

    typer.echo(f"Stopped depths server for '{instance_id}'.")

if __name__ == "__main__":
    app()
