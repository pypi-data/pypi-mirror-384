"""
The primary facade for Depths ingestion and local analytics. It wires core
pipelines (producer → aggregator → shipper) and attaches read/sidecar views:
RealtimeTap and the generalized Stats sidecar introduced in v0.2.0.

Highlights:
  • Ergonomic public API to record OTel-shaped rows (spans/logs/metrics).
  • RealtimeTap: in-memory tail reads and SSE streaming.
  • Stats (v0.2.0): developer-chosen rollups per (project_id, table, column, window),
    with window choices in {"1m","5m","15m","30m","1h","1d"} mapped internally to minutes.

Public helpers (selected):
  • stats_add_category(project_id, otel_table, column, windows)
      Start tracking categorical histograms for a string column at one or more windows.
  • stats_add_numeric(project_id, otel_table, column, windows)
      Start tracking numeric measures (count/min/max/mean/std/sum) for an int/float column.
  • stats_remove(project_id, otel_table, column, window)
      Stop a previously added tracking task at the next UTC minute boundary.
  • read_categorical_stats(...) / read_numeric_stats(...)
      Query the local Delta sidecars with optional filters and flexible return modes.

Notes:
  • Stats helpers raise clear errors if the Stats sidecar is disabled or the
    schema/column/type check fails.
  • Window string shorthands are converted to minutes for internal use.
"""

from __future__ import annotations

import atexit, asyncio, signal, threading, time, re, queue
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple, Literal, Iterable, List

import os
import datetime as _dt
import polars as pl

from depths.core.schema import (
    EventSchema,
    SPAN_SCHEMA, SPAN_EVENT_SCHEMA, SPAN_LINK_SCHEMA,
    LOG_SCHEMA, METRIC_POINT_SCHEMA, METRIC_HIST_SCHEMA,
    apply_addons
)
from depths.core.config import (
    DepthsLoggerOptions, LogProducerConfig, LogAggregatorConfig,
    _save_json, _load_json, S3Config,
    StatsConfig, RealtimeReadConfig,
)
from depths.core.views import Stats, RealtimeTap
from depths.core.producer import LogProducer
from depths.core.aggregator import LogAggregator
from depths.core.shipper import ship_day, ShipperOptions
from depths.core.otlp_mapper import OTLPMapper


_DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def _today_utc_str() -> str:
    """
    Get today’s date in UTC as 'YYYY-MM-DD'.

    Returns:
        ISO date string (UTC) used for staging-day directory names and rollover checks.
    """


    return _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%d")

def _path_startswith(p: str, prefix: str) -> bool:
    """
    Portable check that absolute path `p` is under `prefix`.

    Args:
        p:      Candidate path (file/dir).
        prefix: Directory prefix to test containment against.

    Returns:
        True when p resolves under prefix (case-normalized on Windows).
    """


    p_norm = str(Path(p).resolve())
    pref_norm = str(Path(prefix).resolve())
    if os.name == "nt":
        p_norm = p_norm.lower()
        pref_norm = pref_norm.lower()
    return p_norm.startswith(pref_norm.rstrip("/\\") + os.sep)

class DepthsLogger:
    """
    Unified OTel-native, S3-native telemetry logger
    Covering ingestion to eventual persistence on S3.

    Overview (v0.1.3 role):
        Owns one Producer+Aggregator per table under a single “instance”
        directory tree. On construction, prepares today’s UTC day staging
        paths, merges options (persisted vs provided), wires schemas into
        per-table configs, installs atexit/signal hooks, optionally starts
        aggregators and the background shipper, and replays unshipped days.

    Attributes (selected):
        _instance_id:    Logical instance name (namespace for S3 layout).
        _instance_root:  Filesystem root for configs/index/staging.
        _schemas:        Table name → EventSchema mapping.
        _producers/_aggs:Per-table Producer/Aggregator instances.
        _opts:           DepthsLoggerOptions effective configuration.
        _current_day:    Current UTC day string. Rollover retargets aggregators.
        _mapper:         Stateless OTLP JSON → rows mapper.
        _shipper_*:      Background shipping queue/thread coordination.
    """


    @staticmethod
    def _instance_dirs(root: Path) -> Dict[str, Path]:
        """
        Compute canonical subpaths under an instance root.

        Args:
            root: Base directory for this Depths instance.

        Returns:
            Mapping with keys:
                root, configs, index_dir, index_json, index_jsonl, staging_days, stats_dir
        """


        return {
            "root": root,
            "configs": root / "configs",
            "index_dir": root / "index",
            "index_json": root / "index" / "day.json",
            "index_jsonl": root / "index" / "days.jsonl",
            "staging_days": root / "staging" / "days",
            "stats_dir": root / "stats",
        }

    @staticmethod
    def _ensure_dirs(root: Path) -> Dict[str, Path]:
        """
        Create required directories and initialize index files if missing.

        Args:
            root: Instance root.

        Returns:
            Same mapping as `_instance_dirs`, guaranteed to exist on disk.
        """


        d = DepthsLogger._instance_dirs(root)
        for k in ("configs", "index_dir", "staging_days", "stats_dir"):
            d[k].mkdir(parents=True, exist_ok=True)
        if not d["index_json"].exists():
            d["index_json"].write_text("[]")
        if not d["index_jsonl"].exists():
            d["index_jsonl"].write_text("")
        return d

    @staticmethod
    def _local_day_path(root: Path, day: str) -> str:
        """
        Build the absolute local path to a UTC day’s root directory.

        Args:
            root: Instance root.
            day:  'YYYY-MM-DD' UTC day.

        Returns:
            Absolute string path to '<root>/staging/days/<day>'.
        """


        return str(DepthsLogger._instance_dirs(root)["staging_days"] / day)

    @staticmethod
    def _otel_table_path(day_root: str, sub: str) -> str:
        """
        Resolve a per-table Delta path under a UTC day root.

        Args:
            day_root: Absolute day directory.
            sub:      Table subpath ('spans', 'logs', ...).

        Returns:
            '<day_root>/otel/<sub>' path string.
        """


        return str(Path(day_root) / "otel" / sub)

    @staticmethod
    def _like_expr(col: str, pattern: str | None) -> pl.Expr | None:
        """
        Literal substring predicate builder for Polars.

        Args:
            col:     Column name.
            pattern: Substring to look for (no regex). None → no predicate.

        Returns:
            A Polars expression or None.
        """


        if not pattern:
            return None
        return pl.col(col).cast(pl.Utf8).str.contains(pattern, literal=True)

    @staticmethod
    def _eq_expr(col: str, value) -> pl.Expr | None:
        """
        Equality predicate builder for Polars.

        Args:
            col:   Column name.
            value: Value to compare; None → no predicate.

        Returns:
            Polars expression or None.
        """


        if value is None:
            return None
        return pl.col(col) == value

    @staticmethod
    def _ge_expr(col: str, value) -> pl.Expr | None:
        """
        Greater-or-equal predicate builder for Polars.

        Args:
            col:   Column name.
            value: Lower bound; None → no predicate.

        Returns:
            Polars expression or None.
        """


        if value is None:
            return None
        return pl.col(col) >= value

    @staticmethod
    def _time_range_expr(col: str, ms_from: int | None, ms_to: int | None) -> pl.Expr | None:
        """
        Build an inclusive time-window predicate (epoch ms).

        Args:
            col:     Column name holding epoch milliseconds.
            ms_from: Inclusive start in ms; None to omit.
            ms_to:   Inclusive end in ms; None to omit.

        Returns:
            Conjunction expression or None if both bounds are None.
        """


        conds: list[pl.Expr] = []
        if ms_from is not None:
            conds.append(pl.col(col) >= int(ms_from))
        if ms_to is not None:
            conds.append(pl.col(col) <= int(ms_to))
        if not conds:
            return None
        expr = conds[0]
        for c in conds[1:]:
            expr = expr & c
        return expr

    def __init__(
        self,
        *,
        instance_id: str = "default",
        instance_dir: str = "./depths_logs",
        s3: S3Config | None = None,
        options: DepthsLoggerOptions | None = None,
    ) -> None:
        """
        Construct a DepthsLogger instance and wire all dependencies.

        Behavior (summary):
            1) Resolve instance root (optionally reusing on-disk instance.json).
            2) Ensure directory layout and bootstrap index files.
            3) Load/merge/persist options.json (disk ⟷ provided).
            4) Build six EventSchemas (with add-ons if selected) and per-table Producer+Aggregator.
            5) Prepare UTC-day staging root and mark current day.
            6) Wire sidecars (StatsRollup & RealtimeTap) from typed configs.
            7) Install atexit/signal handlers as configured.
            8) Optionally autostart aggregators + rollup, and start shipper; enqueue past days.
            9) Optionally add session and user identity storage

        Args:
            instance_id:  Logical instance namespace.
            instance_dir: Base directory to contain the instance.
            s3:           S3Config for shipping & S3 readers (optional).
            options:      Overrides for DepthsLoggerOptions (merged with saved).
        """


        self._opts = options or DepthsLoggerOptions()
        self._instance_id = instance_id
        self._instance_root = (Path(instance_dir).expanduser() / instance_id)

        inst_path = (self._instance_root / "configs" / "instance.json")
        on_disk_inst = _load_json(inst_path)
        if on_disk_inst:
            self._instance_id = on_disk_inst.get("instance_id", instance_id)
            root_str = on_disk_inst.get("instance_root") or str(self._instance_root)
            self._instance_root = Path(root_str)

        self._s3: S3Config | None = s3
        paths = self._ensure_dirs(self._instance_root)
        if not on_disk_inst:
            _save_json(
                paths["configs"] / "instance.json",
                {"instance_id": self._instance_id, "instance_root": str(self._instance_root), "version": 3},
            )

        saved_opts = DepthsLoggerOptions.load_from_dir(paths["configs"])
        if options is None:
            effective_opts = saved_opts or DepthsLoggerOptions()
        else:
            if saved_opts is None:
                effective_opts = options
            else:
                merged = saved_opts.to_dict()
                new = options.to_dict()
                for k, v in new.items():
                    if k == "addons" and (v is None or (isinstance(v, dict) and not v)):
                        continue
                    if v is not None:
                        merged[k] = v
                effective_opts = DepthsLoggerOptions.from_dict(merged)
        effective_opts.save_to_dir(paths["configs"])
        self._opts = effective_opts

        self._schemas: Dict[str, EventSchema] = {
            "spans": SPAN_SCHEMA,
            "span_events": SPAN_EVENT_SCHEMA,
            "span_links": SPAN_LINK_SCHEMA,
            "logs": LOG_SCHEMA,
            "metrics_points": METRIC_POINT_SCHEMA,
            "metrics_hist": METRIC_HIST_SCHEMA,
        }
        self._schemas = apply_addons(self._schemas, self._opts.addons or {})

        today = _today_utc_str()
        self._current_day = today
        day_root = self._local_day_path(self._instance_root, today)
        Path(day_root).mkdir(parents=True, exist_ok=True)

        base_prod_cfg: LogProducerConfig = (self._opts.producer_config or LogProducerConfig())
        base_agg_cfg: LogAggregatorConfig = (self._opts.aggregator_config or LogAggregatorConfig())

        self._producers: Dict[str, LogProducer] = {}
        self._aggs: Dict[str, LogAggregator] = {}

        for name, schema in self._schemas.items():
            table_path = self._otel_table_path(day_root, name)
            prod_cfg = base_prod_cfg.override(schema=schema)
            agg_cfg = base_agg_cfg.override(schema=schema, table_path=table_path)
            prod = LogProducer(prod_cfg)
            agg = LogAggregator(prod, agg_cfg)
            self._producers[name] = prod
            self._aggs[name] = agg


        stats_cfg: StatsConfig = (self._opts.stats or StatsConfig())
        rt_cfg: RealtimeReadConfig = (self._opts.realtime_read or RealtimeReadConfig())

        self._stats = Stats(self._instance_root, stats_cfg, schemas=self._schemas)
        self._realtime = RealtimeTap(rt_cfg)

        self._stats_enabled = bool(stats_cfg.enabled)
        self._realtime_enabled = bool(rt_cfg.enabled)


        self._started = False
        self._lock = threading.RLock()
        self._mapper = OTLPMapper(
            add_session_context=self._opts.add_session_context,
            add_user_context=self._opts.add_user_context,
            addons_map=self._opts.addons
        )

        if self._opts.init_early_terminate:
            return

        self._shipper_stop = threading.Event()
        self._ship_queue: "queue.Queue[str]" = queue.Queue(maxsize=64)
        self._shipper_thread: Optional[threading.Thread] = None

        if self._opts.atexit_hook:
            atexit.register(self._atexit_stop)
        if self._opts.install_signal_handlers:
            self._install_signal_handlers()

        if self._opts.auto_start:
            self.start()
        if self._opts.shipper_enabled:
            self._start_shipper()
            self._enqueue_past_days()


    def start(self) -> None:
        """
        Start all table aggregators and sidecars (idempotent).

        Returns:
            None
        """


        with self._lock:
            if self._started:
                return
            for agg in self._aggs.values():
                agg.start()
            if self._stats_enabled:
                self._stats.start()
            self._started = True

    def stop(self, *, flush: Literal["auto","all","none"] = "auto") -> None:
        """
        Stop aggregators, the stats rollup thread, and the background shipper.

        Args:
            flush: 'none' to stop immediately,
                'auto' to wait briefly for a final quiet/age flush,
                'all' behaves like 'auto' (v0.1 uses same path).

        Side effects:
            - Joins threads with small bounded waits; best-effort shutdown.
        """


        with self._lock:
            if not self._started:

                if self._stats_enabled:
                    try: self._stats.stop(flush_remaining=True)
                    except Exception: pass
                self._stop_shipper()
                return

            for agg in self._aggs.values():
                if flush == "none":
                    agg.stop(flush_remaining=False)
                else:
                    wait = max(agg._cfg.quiet_flush_s or 0.0, agg._cfg.max_age_s or 0.0)
                    wait = min(self._opts.max_auto_flush_wait_s, wait)
                    if wait > 0:
                        time.sleep(wait)
                    agg.stop(flush_remaining=True)

            if self._stats_enabled:
                try: self._stats.stop(flush_remaining=True)
                except Exception: pass

            self._started = False

        self._stop_shipper()

    async def astop(self, *, flush: Literal["auto","all","none"] = "auto") -> None:
        """
        Async-friendly wrapper to stop via a worker thread.

        Args:
            flush: See `stop`.

        Returns:
            None
        """


        await asyncio.to_thread(self.stop, flush=flush)

    def _start_shipper(self) -> None:
        """
        Start the background shipper thread if not already running.

        Returns:
            None
        """


        if self._shipper_thread and self._shipper_thread.is_alive():
            return
        self._shipper_stop.clear()
        t = threading.Thread(target=self._shipper_loop, name="depths-shipper", daemon=True)
        t.start()
        self._shipper_thread = t

    def _stop_shipper(self) -> None:
        """
        Stop the background shipper thread and join briefly.

        Returns:
            None
        """


        self._shipper_stop.set()
        try:
            self._ship_queue.put_nowait("__STOP__")
        except Exception:
            pass
        if self._shipper_thread and self._shipper_thread.is_alive():
            self._shipper_thread.join(timeout=10.0)

    def _enqueue_past_days(self) -> None:
        """
        Scan local staging/days and enqueue all past days for shipping.

        Returns:
            None
        """


        days_root = self._instance_dirs(self._instance_root)["staging_days"]
        if not days_root.exists():
            return
        today = _today_utc_str()
        for p in sorted(days_root.iterdir()):
            if p.is_dir() and p.name < today and _DAY_RE.match(p.name):
                self.enqueue_ship(p.name)

    def enqueue_ship(self, day: str) -> None:
        """
        Request shipping for a given UTC day (no-op if invalid/unavailable).

        Args:
            day: 'YYYY-MM-DD' string. Must not be the current day.

        Returns:
            None
        """


        if not self._s3 or not _DAY_RE.match(day):
            return
        if day == self._current_day:
            return
        try:
            self._ship_queue.put_nowait(day)
        except queue.Full:
            pass

    def ship_now(self, day: str) -> Dict:
        """
        Synchronously ship a completed UTC day (seal → upload → verify → cleanup).

        Args:
            day: Past day in 'YYYY-MM-DD'. Current day is rejected.

        Returns:
            Compact result dict with local/remote rows and status.

        Raises:
            ValueError: If S3 isn’t configured, day invalid, or day is current.
        """


        if not self._s3:
            raise ValueError("No S3 configured")
        if not _DAY_RE.match(day):
            raise ValueError("Invalid day format")
        if day == self._current_day:
            raise ValueError("Won't ship the current day")
        local_day_path = self._local_day_path(self._instance_root, day)
        return ship_day(
            instance_id=self._instance_id,
            instance_root=str(self._instance_root),
            day=day,
            local_day_path=local_day_path,
            s3=self._s3,
            opts=ShipperOptions(
                verify_grace_s=self._opts.verify_grace_s,
                verify_timeout_s=self._opts.verify_timeout_s,
                upload_max_workers=self._opts.upload_max_workers,
            ),
        )

    def _shipper_loop(self) -> None:
        """
        Background shipper worker: drains day-requests and ships them.

        Behavior:
            - Waits for all writer queues to drain and no aggregator targeting
            the day’s path, then calls `ship_day(...)`.

        Returns:
            None
        """


        while not self._shipper_stop.is_set():
            try:
                day = self._ship_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if day == "__STOP__":
                break
            if not isinstance(day, str) or not _DAY_RE.match(day) or not self._s3:
                continue
            if day == self._current_day:
                continue

            local_day_path = self._local_day_path(self._instance_root, day)
            while True:
                all_empty = all(agg.metrics.writer_queue_size == 0 for agg in self._aggs.values())
                none_targeting = all(not _path_startswith(agg.table_path, local_day_path) for agg in self._aggs.values())
                if all_empty and none_targeting:
                    break
                if self._shipper_stop.is_set():
                    return
                time.sleep(0.25)

            try:
                ship_day(
                    instance_id=self._instance_id,
                    instance_root=str(self._instance_root),
                    day=day,
                    local_day_path=local_day_path,
                    s3=self._s3,
                    opts=ShipperOptions(
                        verify_grace_s=self._opts.verify_grace_s,
                        verify_timeout_s=self._opts.verify_timeout_s,
                        upload_max_workers=self._opts.upload_max_workers,
                    ),
                )
            finally:
                self._ship_queue.task_done()

    def _maybe_rollover_utc(self) -> None:
        """
        Detect UTC day change and retarget all aggregators to the new day.

        Behavior:
            - Creates the new day root, retargets each aggregator to its
            new '<new_day>/otel/<table>' path (with table init).
            - Optionally enqueues the previous day for shipping after a delay.

        Returns:
            None
        """


        today = _today_utc_str()
        if today == self._current_day:
            return
        old_day = self._current_day
        self._current_day = today
        new_day_root = self._local_day_path(self._instance_root, today)
        Path(new_day_root).mkdir(parents=True, exist_ok=True)

        for name, agg in self._aggs.items():
            new_path = self._otel_table_path(new_day_root, name)
            agg.retarget_table_path(new_path, initialize=True)

        if self._opts.shipper_enabled and _DAY_RE.match(old_day):
            delay = max(0.0, float(self._opts.ship_delay_after_rollover_s))
            threading.Timer(delay, lambda: self.enqueue_ship(old_day)).start()

    def _ensure_started_if_lazy(self) -> None:
        """
        Start aggregators on-demand if lazy-start is enabled.

        Returns:
            None
        """


        if not self._started and self._opts.lazy_start_on_first_log:
            self.start()

    def ingest_span(self, row: Mapping[str, Any]) -> Tuple[bool, Optional[str]]:
        self._ensure_started_if_lazy()
        self._maybe_rollover_utc()
        ok, reason = self._producers["spans"].ingest(row)
        if ok:
            if self._realtime_enabled: self._realtime.push("spans", row)
            if self._stats_enabled:    self._stats.enqueue("spans", row)
        return ok, reason

    def ingest_span_event(self, row: Mapping[str, Any]) -> Tuple[bool, Optional[str]]:
        self._ensure_started_if_lazy()
        self._maybe_rollover_utc()
        ok, reason = self._producers["span_events"].ingest(row)
        if ok:
            if self._realtime_enabled: self._realtime.push("span_events", row)
            if self._stats_enabled:    self._stats.enqueue("span_events", row)
        return ok, reason

    def ingest_span_link(self, row: Mapping[str, Any]) -> Tuple[bool, Optional[str]]:
        self._ensure_started_if_lazy()
        self._maybe_rollover_utc()
        ok, reason = self._producers["span_links"].ingest(row)
        if ok:
            if self._realtime_enabled: self._realtime.push("span_links", row)
            if self._stats_enabled:    self._stats.enqueue("span_links", row)
        return ok, reason

    def ingest_log(self, row: Mapping[str, Any]) -> Tuple[bool, Optional[str]]:
        self._ensure_started_if_lazy()
        self._maybe_rollover_utc()
        ok, reason = self._producers["logs"].ingest(row)
        if ok:
            if self._realtime_enabled: self._realtime.push("logs", row)
            if self._stats_enabled:    self._stats.enqueue("logs", row)
        return ok, reason

    def ingest_metric_point(self, row: Mapping[str, Any]) -> Tuple[bool, Optional[str]]:
        self._ensure_started_if_lazy()
        self._maybe_rollover_utc()
        ok, reason = self._producers["metrics_points"].ingest(row)
        if ok:
            if self._realtime_enabled: self._realtime.push("metrics_points", row)
            if self._stats_enabled:    self._stats.enqueue("metrics_points", row)
        return ok, reason

    def ingest_metric_hist(self, row: Mapping[str, Any]) -> Tuple[bool, Optional[str]]:
        self._ensure_started_if_lazy()
        self._maybe_rollover_utc()
        ok, reason = self._producers["metrics_hist"].ingest(row)
        if ok:
            if self._realtime_enabled: self._realtime.push("metrics_hist", row)
            if self._stats_enabled:    self._stats.enqueue("metrics_hist", row)
        return ok, reason

    def ingest_otlp_traces_json(self, payload: Mapping[str, Any], *, project_id: Optional[str] = None) -> Dict[str, int]:
        """
        Decode already-parsed OTLP Traces payload into rows and ingest them.

        Overview:
            • Projects `payload` to three row lists via OTLPMapper.map_traces(...)
            → (spans, events, links).
            • For each row, calls the corresponding ingest_* method:
                ingest_span, ingest_span_event, ingest_span_link.
            • Aggregates total accepted vs rejected counts across all three categories.
            • Returns summary counts including the raw lengths of each list.

        Args:
            payload: A Mapping representing a decoded OTLP ExportTraceServiceRequest.
            project_id: Optional tenancy override passed through to the mapper.

        Returns:
            Dict with keys:
            {'accepted', 'rejected', 'spans', 'events', 'links'}

        Notes:
            - The per-row ingest_* methods internally handle lazy-start and UTC
            rollover checks; this method does not duplicate those concerns.
            - `dict(payload)` defensively copies to avoid caller-side aliasing.
        """


        spans, events, links = self._mapper.map_traces(dict(payload), project_id=project_id)
        ca = cr = 0
        for r in spans:
            ok, _ = self.ingest_span(r); ca += 1 if ok else 0; cr += 0 if ok else 1
        for r in events:
            ok, _ = self.ingest_span_event(r); ca += 1 if ok else 0; cr += 0 if ok else 1
        for r in links:
            ok, _ = self.ingest_span_link(r); ca += 1 if ok else 0; cr += 0 if ok else 1
        return {"accepted": ca, "rejected": cr, "spans": len(spans), "events": len(events), "links": len(links)}

    def ingest_otlp_logs_json(self, payload: Mapping[str, Any], *, project_id: Optional[str] = None) -> Dict[str, int]:
        """
        Decode already-parsed OTLP Logs payload into rows and ingest them.

        Overview:
            • Uses OTLPMapper.map_logs(...) to produce a list of LOGS rows.
            • Enqueues each row via ingest_log(...), counting successes/failures.
            • Returns a compact summary with accepted/rejected and total rows mapped.

        Args:
            payload: A Mapping representing a decoded OTLP ExportLogsServiceRequest.
            project_id: Optional tenancy override passed through to the mapper.

        Returns:
            Dict with keys: {'accepted', 'rejected', 'logs'}

        Notes:
            - ingest_log(...) performs validation/normalization against LOG_SCHEMA,
            including AnyValue→string handling for `body`, then enqueues.
        """


        rows = self._mapper.map_logs(dict(payload), project_id=project_id)
        ca = cr = 0
        for r in rows:
            ok, _ = self.ingest_log(r); ca += 1 if ok else 0; cr += 0 if ok else 1
        return {"accepted": ca, "rejected": cr, "logs": len(rows)}

    def ingest_otlp_metrics_json(self, payload: Mapping[str, Any], *, project_id: Optional[str] = None) -> Dict[str, int]:
        """
        Decode already-parsed OTLP Metrics payload into rows and ingest them.

        Overview:
            • Uses OTLPMapper.map_metrics(...) to produce two lists:
                points (Gauge/Sum) and hists (Histogram/ExpHistogram/Summary).
            • Enqueues each via ingest_metric_point(...) and ingest_metric_hist(...).
            • Tracks total accepted vs rejected across both families and returns a summary.

        Args:
            payload: A Mapping representing a decoded OTLP ExportMetricsServiceRequest.
            project_id: Optional tenancy override passed through to the mapper.

        Returns:
            Dict with keys: {'accepted', 'rejected', 'points', 'hists'}

        Notes:
            - The hist family collapses multiple OTLP metric types into one table
            (METRIC_HIST) with normalized wide columns.
        """


        points, hists = self._mapper.map_metrics(dict(payload), project_id=project_id)
        ca = cr = 0
        for r in points:
            ok, _ = self.ingest_metric_point(r); ca += 1 if ok else 0; cr += 0 if ok else 1
        for r in hists:
            ok, _ = self.ingest_metric_hist(r); ca += 1 if ok else 0; cr += 0 if ok else 1
        return {"accepted": ca, "rejected": cr, "points": len(points), "hists": len(hists)}


    def internal_log(
        self,
        body: str,
        *,
        severity_text: str = "INFO",
        severity_number: int = 9,
        attrs: Optional[Dict[str, Any]] = None,
        project_id: str = "__depths__",
        service_name: str = "depths-internal",
    ) -> Tuple[bool, Optional[str]]:
        """
        Emit a minimal operational log into the OTel LOGS table.

        Overview:
            • Only active when DepthsLoggerOptions.internal_otel_logs is True.
            • Constructs a row with:
                project_id, schema_version=1, service_name,
                resource_attrs_json (from `attrs`), scope_* (name/version/attrs),
                time_unix_nano & observed_time_unix_nano (both = now in ns, UTC),
                severity_text, severity_number, body (string), log_attrs_json ({}),
                trace_id="", span_id="".
            • Submits via ingest_log(...) and returns its (ok, reason) tuple.

        Args:
            body: Message string.
            severity_text: OTel severity text (default 'INFO').
            severity_number: OTel severity number (default 9).
            attrs: Optional dict merged into resource_attrs_json.
            project_id: Logical tenant for this internal event.
            service_name: Service identity under which this event is recorded.

        Returns:
            Tuple[bool, Optional[str]] from ingest_log.
        """


        if not self._opts.internal_otel_logs:
            return True, None
        now_ns = int(_dt.datetime.now(tz=_dt.UTC).timestamp() * 1_000_000_000)
        row = {
            "project_id": project_id,
            "schema_version": 1,
            "service_name": service_name,
            "resource_attrs_json": attrs or {},
            "scope_name": "depths",
            "scope_version": "v0.1",
            "scope_attrs_json": {},
            "time_unix_nano": now_ns,
            "observed_time_unix_nano": now_ns,
            "severity_text": severity_text,
            "severity_number": int(severity_number),
            "body": str(body),
            "log_attrs_json": {},
            "trace_id": "",
            "span_id": "",
        }
        return self.ingest_log(row)


    def _day_table_sources(
        self,
        start_day: str|None,
        end_day: str|None,
        sub: str,
        *,
        storage: Literal["auto","local","s3"] = "auto",
    ) -> list[tuple[str,str,dict|None]]:
        """Return (day, table_path, s3_opts) for requested range + table subpath."""
        def _iter_days(a: Optional[str], b: Optional[str]) -> list[str]:
            if not a and not b: return [_today_utc_str()]
            if not a: a = b
            if not b: b = a
            da = _dt.date.fromisoformat(a); db = _dt.date.fromisoformat(b)
            if da>db: da,db=db,da
            out=[]; cur=da
            while cur<=db: out.append(cur.isoformat()); cur=cur+_dt.timedelta(days=1)
            return out

        days = _iter_days(start_day, end_day)
        s3_opts = self._s3.to_delta_storage_options() if self._s3 else None
        out=[]
        for d in days:
            local_root = self._local_day_path(self._instance_root, d)
            local_tbl = self._otel_table_path(local_root, sub)
            if storage in {"auto","local"} and Path(local_tbl).exists():
                out.append((d, local_tbl, None))
                continue
            if storage in {"auto","s3"} and self._s3:
                out.append((d, self._s3.day_uri(self._instance_id, d).rstrip("/") + f"/otel/{sub}", s3_opts))
        return out

    def _lazy_for_table(
        self,
        sub: str,
        *,
        date_from: str|None = None,
        date_to: str|None = None,
        storage: Literal["auto","local","s3"] = "auto",
        where: pl.Expr | Iterable[pl.Expr] | None = None
    ) -> pl.LazyFrame:
        from depths.io.delta import read_delta
        lfs: list[pl.LazyFrame] = []
        for _, path, s3opts in self._day_table_sources(date_from, date_to, sub, storage=storage):
            try:
                lf_or_df = read_delta(path, storage_options=s3opts, return_lf=True)
                lf = lf_or_df if isinstance(lf_or_df, pl.LazyFrame) else lf_or_df.lazy()
                lfs.append(lf)
            except Exception:
                continue
        if not lfs:
            return pl.DataFrame(schema=self._schemas[sub].polars_schema()).lazy()
        lf = pl.concat(lfs, how="vertical")
        if where is not None:
            if isinstance(where, pl.Expr):
                lf = lf.filter(where)
            else:
                for w in where:
                    lf = lf.filter(w)
        return lf


    def spans_lazy(self, **kw) -> pl.LazyFrame:
        return self._lazy_for_table("spans", **kw)

    def span_events_lazy(self, **kw) -> pl.LazyFrame:
        return self._lazy_for_table("span_events", **kw)

    def span_links_lazy(self, **kw) -> pl.LazyFrame:
        return self._lazy_for_table("span_links", **kw)

    def logs_lazy(self, **kw) -> pl.LazyFrame:
        return self._lazy_for_table("logs", **kw)

    def metrics_points_lazy(self, **kw) -> pl.LazyFrame:
        return self._lazy_for_table("metrics_points", **kw)

    def metrics_hist_lazy(self, **kw) -> pl.LazyFrame:
        return self._lazy_for_table("metrics_hist", **kw)

    def _finalize_return(
        self,
        lf: pl.LazyFrame,
        *,
        select: list[str] | None,
        max_rows: int | None,
        return_as: Literal["dicts","dataframe","lazy"],
    ) -> pl.LazyFrame | pl.DataFrame | list[dict[str, Any]]:
        """
        Apply latest-N semantics and projection, then return as requested.
        Developer notes:
        - For **latest-N**, we sort by `event_ts` desc then limit BEFORE projection
          so it still works when `event_ts` is not part of `select`.
        - When `return_as="lazy"`, we keep everything lazy (including sort/limit).
        - When materializing, we collect once and use `DataFrame.to_dicts()` for
          Python-native row dicts (Polars' idiomatic "records" form). See docs.
        """
        if max_rows is not None:
            lf = lf.sort("event_ts", descending=True).limit(int(max_rows))
        if select:
            lf = lf.select([pl.col(c) for c in select])
        if return_as == "lazy":
            return lf
        df = lf.collect()
        return df if return_as == "dataframe" else df.to_dicts()

    def _finalize_stats_return(
        self,
        lf: pl.LazyFrame,
        *,
        select: list[str] | None,
        max_rows: int | None,
        return_as: Literal["dicts","dataframe","lazy"],
        sort_by: str = "minute_ts",
        descending: bool = True,
    ) -> pl.LazyFrame | pl.DataFrame | list[dict[str, Any]]:
        """
        Finalize a stats LazyFrame for return to caller.

        Behavior:
        - Sorts by `sort_by` (default: 'minute_ts') and applies an optional
          `limit` when `max_rows` is provided.
        - Optionally projects a subset of columns via `select`.
        - Materializes to Python dicts (default) or a DataFrame, or returns lazy.

        Args:
            lf:         A Polars LazyFrame over the stats tables.
            select:     Optional projected columns.
            max_rows:   Optional cap on rows (applied after sorting).
            return_as:  'dicts' (default), 'dataframe', or 'lazy'.
            sort_by:    Column to sort by before limiting (default: 'minute_ts').
            descending: Whether to sort descending (default: True).

        Returns:
            LazyFrame, DataFrame, or list[dict], matching `return_as`.
        """
        if sort_by:
            lf = lf.sort(sort_by, descending=descending)
        if max_rows is not None:
            lf = lf.limit(int(max_rows))
        if select:
            lf = lf.select([pl.col(c) for c in select])
        if return_as == "lazy":
            return lf
        df = lf.collect()
        return df if return_as == "dataframe" else df.to_dicts()

    def _convert_window_value_string_to_int(
        self,
        value
    )->Literal[1,5,15,30,60,1440]:
        """
        Internal helper to map stat window value from string to integer.
        """
        if value=="1m":
            return 1
        elif value=="5m":
            return 5
        elif value=="15m":
            return 15
        elif value=="30m":
            return 30
        elif value=="1h":
            return 60
        elif value=="1d":
            return 1440
        else:
            raise ValueError("Unknown value")

    def _convert_window(
        self,
        windows: Iterable[Literal["1m","5m","15m","30m","1h","1d"]]
    )->List[Literal[1,5,15,30,60,1440]]:
        """
        Swapping stat windows from ergonomic string inputs to integers for internal use.
        """
        int_windows=[]
        for w in windows:
            int_windows.append(self._convert_window_value_string_to_int(w))

        return int_windows        

    def stats_add_category(
        self,
        *,
        project_id: str,
        otel_table: Literal["spans", "span_events", "span_links","logs", "metrics_points", "metrics_hist"],
        column: str,
        windows: Iterable[Literal["1m","5m","15m","30m","1h","1d"]],
    ) -> None:
        """
        Begin tracking categorical statistics for a string-typed column.

        Args:
            project_id: The ID for the project for which the stat aggregation is to added
            otel_table: The OTel table from which the column is being chosen for stat aggregation
                        Valid choices: "spans", "span_events", "span_links","logs", "metrics_points", "metrics_hist"
            column: Any of the categorical column in the table schema. 
                    Please ensure that the cardinality is reasonable
                    Depths (as of v0.2.0) by default cuts off the cardinality at 200
            windows: List of time intervals for which stat aggregates are desired for the column chosen.
                     Valid values are: "1m","5m","15m","30m","1h","1d".
                     For example, you can pass in ["1m","1h"] if you want stat
                     aggregation for each minute and each hour.


        What it does:
        - Registers one tracking task per `window` in `windows` for the given
          (project_id, otel_table, column). Supported windows (minutes): 1, 5,
          15, 30, 60, 1440. Each task rolls per-minute buckets and periodically
          flushes to Delta with partitions:
              project_id/window/otel_table/column
        - Validation: The column must exist as a top-level field on the given
          OTel table and be string-typed (as per the composed EventSchema with
          add-ons applied). If validation fails, a ValueError is raised.
        - Activation boundary: New tasks become active on the next UTC minute
          boundary to preserve clean windowing and avoid partial buckets.
        - Category memory cap: At most `StatsConfig.max_categories` unique
          categories are kept per (task, bucket). Additional categories are
          silently ignored (by design) to prevent unbounded growth.

        Raises:
            RuntimeError: When the Stats sidecar is disabled in options.
            ValueError:   When an invalid table/column/type/window is supplied.
        """
        if not getattr(self, "_stats_enabled", False):
            raise RuntimeError("Stats sidecar is disabled; enable DepthsLoggerOptions.stats.enabled to use it.")

        if otel_table is None:
            raise RuntimeError("Please choose an OTel table")
        if column is None:
            raise RuntimeError("Please choose a column")
        if windows is None:
            raise RuntimeError("Please pick suitable time windows")
        
        windows=self._convert_window(windows)

        self._stats.add_category(project_id=project_id, otel_table=otel_table, column=column, windows=windows)

    def stats_add_numeric(
        self,
        *,
        project_id: str,
        otel_table: Literal["spans", "span_events", "span_links","logs", "metrics_points", "metrics_hist"],
        column: str,
        windows: Iterable[Literal["1m","5m","15m","30m","1h","1d"]],
    ) -> None:
        """
        Begin tracking numeric statistics for an int/float column.

        Args:
            project_id: The ID for the project for which the stat aggregation is to added
            otel_table: The OTel table from which the column is being chosen for stat aggregation
                        Valid choices: "spans", "span_events", "span_links","logs", "metrics_points", "metrics_hist"
            column: Any of the numerical column in the table schema. 
            windows: List of time intervals for which stat aggregates are desired for the column chosen.
                     Valid values are: "1m","5m","15m","30m","1h","1d".
                     For example, you can pass in ["1m","1h"] if you want stat
                     aggregation for each minute and each hour.

        What it does:
        - Registers one tracking task per `window` in `windows` for the given
          (project_id, otel_table, column). Supported windows (minutes): 1, 5,
          15, 30, 60, 1440. Each task rolls per-minute buckets and periodically
          flushes to Delta with partitions:
              project_id/window/otel_table/column
        - Measures stored per bucket (population heuristics):
              event_count, value_min, value_max, value_mean,
              value_std (population), value_sum
        - Validation: The column must exist as a top-level field on the given
          OTel table and be numeric (int/float) as per the composed EventSchema.
        - Activation boundary: New tasks become active on the next UTC minute.

        Raises:
            RuntimeError: When the Stats sidecar is disabled in options.
            ValueError:   When an invalid table/column/type/window is supplied.
        """
        if not getattr(self, "_stats_enabled", False):
            raise RuntimeError("Stats sidecar is disabled; enable DepthsLoggerOptions.stats.enabled to use it.")
        
        if otel_table is None:
            raise RuntimeError("Please choose an OTel table")
        if column is None:
            raise RuntimeError("Please choose a column")
        if windows is None:
            raise RuntimeError("Please pick suitable time windows")
        
        windows=self._convert_window(windows)

        self._stats.add_numeric(project_id=project_id, otel_table=otel_table, column=column, windows=windows)

    def stats_remove(
        self,
        *,
        project_id: str,
        otel_table: Literal["spans", "span_events", "span_links","logs", "metrics_points", "metrics_hist"],
        column: str,
        window: Literal["1m","5m","15m","30m","1h","1d"],
    ) -> None:
        """
        Stop tracking stats for a previously added task.

        Args:
            project_id: The ID for the project for which the stat aggregation is to removed
            otel_table: The OTel table from which the column is being chosen for stat aggregation
                        Valid choices: "spans", "span_events", "span_links","logs", "metrics_points", "metrics_hist"
            column: Any stat aggregated column in the table schema. 
            window: Time interval for which stat aggregates were implemented for the column chosen.
                     Valid values are: "1m","5m","15m","30m","1h","1d".

        What it does:
        - Identifies the tracking task uniquely by (project_id, otel_table,
          column, window) and marks it for removal at the end of the current
          UTC minute; this avoids cutting a bucket mid-window.
        - If the task does not exist, this is a no-op.

        Raises:
            RuntimeError: When the Stats sidecar is disabled in options.
            ValueError:   When the window value is not one of the supported set.
        """
        if not getattr(self, "_stats_enabled", False):
            raise RuntimeError("Stats sidecar is disabled; enable DepthsLoggerOptions.stats.enabled to use it.")
        
        window=self._convert_window_value_string_to_int(window)

        self._stats.remove(project_id=project_id, otel_table=otel_table, column=column, window=window)

    def read_spans(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        project_id: str | None = None,
        service_name: str | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        name: str | None = None,
        name_like: str | None = None,
        status_code: str | None = None,
        kind: str | None = None,
        time_ms_from: int | None = None,
        time_ms_to: int | None = None,
        select: list[str] | None = None,
        max_rows: int | None = None,
        return_as:Literal["dicts","dataframe","lazy"]="dicts",
        storage: Literal["auto","local","s3"] = "auto",
    ) -> pl.LazyFrame:
        """
        Build a pushdown-friendly LazyFrame for SPANS with common predicates.

        Overview:
            • Sources data across a date range from local and/or S3 via spans_lazy(...).
            • Applies equality filters on:
                project_id, service_name, trace_id, span_id, name, status_code, kind.
            • Applies a literal substring filter on `name` when name_like is set
            (no regex; uses .str.contains(..., literal=True)).
            • Applies an inclusive time window on `event_ts` (epoch ms) via _time_range_expr.
            • Optionally projects columns (`select`) and limits rows (`limit`).

        Args:
            date_from/date_to: Inclusive UTC day bounds ('YYYY-MM-DD').
            project_id/service_name/trace_id/span_id/name/name_like/status_code/kind: Optional filters.
            time_ms_from/time_ms_to: Inclusive event_ts bounds in epoch milliseconds.
            select: Optional list of column names to project.
            max_rows: Optional max rows to return (applied lazily).
            return_as: Optional, whether to return as dicts, dataframe or lazyframe with default as dicts for direct usage.
            storage: 'auto' | 'local' | 's3' source selection.

        Returns:
            pl.LazyFrame with predicates composed and applied lazily for pushdown.
        """


        lf = self.spans_lazy(date_from=date_from, date_to=date_to, storage=storage)
        predicates: list[pl.Expr] = []
        for col, val in (
            ("project_id", project_id),
            ("service_name", service_name),
            ("trace_id", trace_id),
            ("span_id", span_id),
            ("name", name),
            ("status_code", status_code),
            ("kind", kind),
       ):
            e = self._eq_expr(col, val)
            if e is not None:
                predicates.append(e)

        e_like = self._like_expr("name", name_like)
        if e_like is not None:
            predicates.append(e_like)

        e_time = self._time_range_expr("event_ts", time_ms_from, time_ms_to)
        if e_time is not None:
            predicates.append(e_time)
        if predicates:
            expr = predicates[0]
            for p in predicates[1:]:
                expr = expr & p
            lf = lf.filter(expr)
        return self._finalize_return(lf, select=select, max_rows=max_rows, return_as=return_as)

    def read_logs(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        project_id: str | None = None,
        service_name: str | None = None,
        severity_ge: int | None = None,
        body_like: str | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        time_ms_from: int | None = None,
        time_ms_to: int | None = None,
        select: list[str] | None = None,
        max_rows: int | None = None,
        return_as:Literal["dicts","dataframe","lazy"]="dicts",
        storage: Literal["auto","local","s3"] = "auto",
    ) -> pl.LazyFrame:
        """
        Build a pushdown-friendly LazyFrame for LOGS with common predicates.

        Overview:
            • Sources rows via logs_lazy(...).
            • Applies equality filters on: project_id, service_name, trace_id, span_id.
            • Applies a >= threshold on severity_number when severity_ge is set.
            • Applies a literal substring filter on `body` when body_like is set.
            • Applies an inclusive time window on `event_ts` (epoch ms).
            • Supports optional projection (`select`) and row limit (`limit`).

        Args:
            date_from/date_to: Inclusive UTC day bounds ('YYYY-MM-DD').
            project_id/service_name/trace_id/span_id: Optional equality filters.
            severity_ge: Minimum severity_number (inclusive).
            body_like: Literal substring to search in `body`.
            time_ms_from/time_ms_to: Inclusive event_ts bounds in epoch milliseconds.
            select: Optional list of column names.
            max_rows: Optional max rows to return (applied lazily).
            return_as: Optional, whether to return as dicts, dataframe or lazyframe with default as dicts for direct usage.
            storage: 'auto' | 'local' | 's3' source selection.

        Returns:
            pl.LazyFrame with all applicable predicates applied lazily.
        """


        lf = self.logs_lazy(date_from=date_from, date_to=date_to, storage=storage)
        predicates: list[pl.Expr] = []
        for col, val in (
            ("project_id", project_id),
            ("service_name", service_name),
            ("trace_id", trace_id),
            ("span_id", span_id),
        ):
            e = self._eq_expr(col, val)
            if e is not None:
                predicates.append(e)
        if severity_ge is not None:
            e = self._ge_expr("severity_number", int(severity_ge))
            if e is not None:
                predicates.append(e)
        e_like = self._like_expr("body", body_like)
        if e_like is not None:
            predicates.append(e_like)
        e_time = self._time_range_expr("event_ts", time_ms_from, time_ms_to)
        if e_time is not None:
            predicates.append(e_time)
        if predicates:
            expr = predicates[0]
            for p in predicates[1:]:
                expr = expr & p
            lf = lf.filter(expr)
        return self._finalize_return(lf, select=select, max_rows=max_rows, return_as=return_as)

    def read_metrics_points(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        project_id: str | None = None,
        service_name: str | None = None,
        instrument_name: str | None = None,
        instrument_type: str | None = None,
        time_ms_from: int | None = None,
        time_ms_to: int | None = None,
        select: list[str] | None = None,
        max_rows: int | None = None,
        return_as:Literal["dicts","dataframe","lazy"]="dicts",
        storage: Literal["auto","local","s3"] = "auto",
    ) -> pl.LazyFrame:
        """
        Build a pushdown-friendly LazyFrame for METRIC_POINT (Gauge/Sum).

        Overview:
            • Sources rows via metrics_points_lazy(...).
            • Applies equality filters on:
                project_id, service_name, instrument_name, instrument_type.
            • Applies an inclusive time window on `event_ts` (epoch ms).
            • Supports optional projection (`select`) and row limit (`limit`).

        Args:
            date_from/date_to: Inclusive UTC day bounds ('YYYY-MM-DD').
            project_id/service_name/instrument_name/instrument_type: Optional equality filters.
            time_ms_from/time_ms_to: Inclusive event_ts bounds in epoch milliseconds.
            select: Optional list of column names.
            max_rows: Optional max rows to return (applied lazily).
            return_as: Optional, whether to return as dicts, dataframe or lazyframe with default as dicts for direct usage.
            storage: 'auto' | 'local' | 's3' source selection.

        Returns:
            pl.LazyFrame with composed lazy predicates.
        """


        lf = self.metrics_points_lazy(date_from=date_from, date_to=date_to, storage=storage)
        predicates: list[pl.Expr] = []
        for col, val in (
            ("project_id", project_id),
            ("service_name", service_name),
            ("instrument_name", instrument_name),
            ("instrument_type", instrument_type),
        ):
            e = self._eq_expr(col, val)
            if e is not None:
                predicates.append(e)
        e_time = self._time_range_expr("event_ts", time_ms_from, time_ms_to)
        if e_time is not None:
            predicates.append(e_time)
        if predicates:
            expr = predicates[0]
            for p in predicates[1:]:
                expr = expr & p
            lf = lf.filter(expr)
        return self._finalize_return(lf, select=select, max_rows=max_rows, return_as=return_as)

    def read_metrics_hist(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        project_id: str | None = None,
        service_name: str | None = None,
        instrument_name: str | None = None,
        instrument_type: str | None = None,
        time_ms_from: int | None = None,
        time_ms_to: int | None = None,
        select: list[str] | None = None,
        max_rows: int | None = None,
        return_as:Literal["dicts","dataframe","lazy"]="dicts",
        storage: Literal["auto","local","s3"] = "auto",
    ) -> pl.LazyFrame:
        """
        Build a pushdown-friendly LazyFrame for METRIC_HIST (Histogram/ExpHistogram/Summary).

        Overview:
            • Sources rows via metrics_hist_lazy(...).
            • Applies equality filters on:
                project_id, service_name, instrument_name, instrument_type.
            • Applies an inclusive time window on `event_ts` (epoch ms).
            • Supports optional projection (`select`) and row limit (`limit`).

        Args:
            date_from/date_to: Inclusive UTC day bounds ('YYYY-MM-DD').
            project_id/service_name/instrument_name/instrument_type: Optional equality filters.
            time_ms_from/time_ms_to: Inclusive event_ts bounds in epoch milliseconds.
            select: Optional list of column names.
            max_rows: Optional max rows to return (applied lazily).
            return_as: Optional, whether to return as dicts, dataframe or lazyframe with default as dicts for direct usage.
            storage: 'auto' | 'local' | 's3' source selection.

        Returns:
            pl.LazyFrame with composed lazy predicates across histogram-like families.
        """


        lf = self.metrics_hist_lazy(date_from=date_from, date_to=date_to, storage=storage)
        predicates: list[pl.Expr] = []
        for col, val in (
            ("project_id", project_id),
            ("service_name", service_name),
            ("instrument_name", instrument_name),
            ("instrument_type", instrument_type),
        ):
            e = self._eq_expr(col, val)
            if e is not None:
                predicates.append(e)
        e_time = self._time_range_expr("event_ts", time_ms_from, time_ms_to)
        if e_time is not None:
            predicates.append(e_time)
        if predicates:
            expr = predicates[0]
            for p in predicates[1:]:
                expr = expr & p
            lf = lf.filter(expr)
        return self._finalize_return(lf, select=select, max_rows=max_rows, return_as=return_as)

    
    def read_categorical_stats(
        self,
        *,
        project_id: str | None = None,
        otel_table: Literal["spans", "span_events", "span_links","logs", "metrics_points", "metrics_hist"] | None = None,
        column: str | None = None,
        window: Literal["1m","5m","15m","30m","1h","1d"] | None = None,
        minute_ts_from: int | None = None,
        minute_ts_to: int | None = None,
        select: list[str] | None = None,
        max_rows: int = 100,
        return_as: Literal["dicts","dataframe","lazy"] = "dicts",
    ) -> pl.LazyFrame | pl.DataFrame | list[dict[str, Any]]:
        """
        Read categorical stats (per-bucket histograms) from the local Delta table.

        Args:
            project_id: The ID for the project for which the stat aggregation is to be queried
            otel_table: The OTel table from which the column is being chosen for stat aggregates querying
                        Valid choices: "spans", "span_events", "span_links","logs", "metrics_points", "metrics_hist"
            column: Any stat aggregated column in the table schema. 
            window: Time interval for which stat aggregates were implemented for the column chosen.
                     Valid values are: "1m","5m","15m","30m","1h","1d".
            minute_ts_from: From when we should fetch the records: UNIX epoch UTC minute
            minute_ts_to: Till when we should fetch the records: UNIX epoch UTC minute
            select: Columns to fetch during the query. Allows you to pick and choose what columns to return.
            max_rows: Maximum number of rows to return. Default is 100.
            return_as: Whether to return as dictionary, dataframe or lazyframe.

        Returns:
            • 'dicts' (default): list[dict]
            • 'dataframe':      pl.DataFrame
            • 'lazy':           pl.LazyFrame

        Notes:
            - Rows carry: project_id, window, otel_table, column, minute_ts,
              categories: list[str], counts: list[int], snapshot_ts, bucket_key.
            - The helper sorts by minute_ts desc when limiting, to surface newest first.
        """
        if not getattr(self, "_stats_enabled", False):
            raise RuntimeError("Stats sidecar is disabled; enable DepthsLoggerOptions.stats.enabled to use it.")
        if window is not None:
            window=self._convert_window_value_string_to_int(window)

        lf = self._stats.lazy_read_categorical_stats(
            project_id=project_id,
            otel_table=otel_table,
            column=column,
            window=window,
            minute_ts_from=minute_ts_from,
            minute_ts_to=minute_ts_to,
            latest_only=True,
        )
        return self._finalize_stats_return(
            lf,
            select=select,
            max_rows=max_rows,
            return_as=return_as,
            sort_by="minute_ts",
            descending=True,
        )

    def read_numeric_stats(
        self,
        *,
        project_id: str | None = None,
        otel_table: Literal["spans", "span_events", "span_links","logs", "metrics_points", "metrics_hist"] | None = None,
        column: str | None = None,
        window: Literal["1m","5m","15m","30m","1h","1d"] | None = None,
        minute_ts_from: int | None = None,
        minute_ts_to: int | None = None,
        select: list[str] | None = None,
        max_rows: int = 100,
        return_as: Literal["dicts","dataframe","lazy"] = "dicts",
    ) -> pl.LazyFrame | pl.DataFrame | list[dict[str, Any]]:
        """
        Read numeric stats (population measures) from the local Delta table.

        Args:
            project_id: The ID for the project for which the stat aggregation is to be queried
            otel_table: The OTel table from which the column is being chosen for stat aggregates querying
                        Valid choices: "spans", "span_events", "span_links","logs", "metrics_points", "metrics_hist"
            column: Any stat aggregated column in the table schema. 
            window: Time interval for which stat aggregates were implemented for the column chosen.
                     Valid values are: "1m","5m","15m","30m","1h","1d".
            minute_ts_from: From when we should fetch the records: UNIX epoch UTC minute
            minute_ts_to: Till when we should fetch the records: UNIX epoch UTC minute
            select: Columns to fetch during the query. Allows you to pick and choose what columns to return.
            max_rows: Maximum number of rows to return. Default is 100.
            return_as: Whether to return as dictionary, dataframe or lazyframe.

        Measures per row:
            event_count, value_min, value_max, value_mean, value_std, value_sum

        Returns:
            • 'dicts' (default): list[dict]
            • 'dataframe':      pl.DataFrame
            • 'lazy':           pl.LazyFrame

        Notes:
            - The helper sorts by minute_ts desc when limiting, to surface newest first.
        """

        if not getattr(self, "_stats_enabled", False):
            raise RuntimeError("Stats sidecar is disabled; enable DepthsLoggerOptions.stats.enabled to use it.")
        
        if window is not None:
            window=self._convert_window_value_string_to_int(window)

        lf = self._stats.lazy_read_numeric_stats(
            project_id=project_id,
            otel_table=otel_table,
            column=column,
            window=window,
            minute_ts_from=minute_ts_from,
            minute_ts_to=minute_ts_to,
            latest_only=True,
        )
        return self._finalize_stats_return(
            lf,
            select=select,
            max_rows=max_rows,
            return_as=return_as,
            sort_by="minute_ts",
            descending=True,
        )

    def read_realtime(
        self,
        signal: str,
        *,
        n: int = 100,
        project_id: str | None = None,
        since_id: int | None = None,
    ) -> list[dict]:
        """
        Pull the newest in-memory items from the realtime tap.

        Args:
            signal: One of 'spans'|'span_events'|'span_links'|'logs'|'metrics_points'|'metrics_hist'.
            n: Max number of items to return (tail semantics).
            project_id: Optional filter by project id.
            since_id: Placeholder for future incremental reads (unused in v0.1.3).

        Returns:
            List of raw dicts (oldest → newest).
        """


        if not getattr(self, "_realtime_enabled", False):
            return []
        return self._realtime.read(signal, n=n, project_id=project_id)


    def metrics(self) -> Dict[str, Any]:
        """
        Snapshot operational metrics for all producers and aggregators.

        Overview (v0.1.1):
            Returns a lightweight, ready-to-serialize dict that combines:
            • Global logger info (instance_id, started, current_day_utc)
            • Per-producer counters & queue stats
            • Per-aggregator flush/write stats and delta status

            This is consumed by the FastAPI /healthz endpoint and the `depths status`
            CLI. Keep it cheap: values are best-effort and unsynchronized.

        Returns:
            Dict with the shape:
            {
            "instance_id": <str>,
            "started": <float epoch seconds>,
            "current_day_utc": <"YYYY-MM-DD">,
            "producers": {
                "<otel_table>": {
                "accepted": <int>,
                "rejected_schema": <int>,
                "rejected_payload_json": <int>,
                "rejected_date_mismatch": <int>,
                "dropped_capacity": <int>,
                "queue_size": <int>,
                "oldest_age_seconds": <float|None>
                },
                ...
            },
            "aggregators": {
                "<otel_table>": {
                "flushes": <int>,
                "rows_scheduled_total": <int>,
                "rows_persisted_total": <int>,
                "writer_queue_size": <int>,
                "last_commit_seconds": <float|None>,
                "delta_init_ok": <bool>,
                "delta_last_error": <str|None>,
                "table_path": <str>
                },
                ...
            }
            }

        # --- DEVELOPER NOTES -------------------------------------------------
        # - IMPORTANT: LogProducer.metrics and LogAggregator.metrics are @property,
        #   not methods. Access them as `obj.metrics`, not `obj.metrics()`.
        # - Avoid heavy locks here; values are approximate by design.
        # - This method’s return type is part of the /healthz contract. Favor
        #   additive changes; keep existing keys stable for the CLI renderer.
        """

        out: Dict[str, Any] = {
            "instance_id": getattr(self, "_instance_id", "unknown"),
            "started": self._started,
            "current_day_utc": self._current_day,
            "producers": {},
            "aggregators": {},
        }

        for name, prod in self._producers.items():
            pm = prod.metrics
            out["producers"][name] = {
                "accepted": pm.accepted,
                "rejected_schema": pm.rejected_schema,
                "rejected_payload_json": pm.rejected_payload_json,
                "rejected_date_mismatch": pm.rejected_date_mismatch,
                "dropped_capacity": pm.dropped_capacity,
                "queue_size": prod.queue_size(),
                "oldest_age_seconds": prod.oldest_age_seconds(),
            }

        for name, agg in self._aggs.items():
            am = agg.metrics
            out["aggregators"][name] = {
                "flushes": am.flushes,
                "rows_scheduled_total": am.rows_scheduled_total,
                "rows_persisted_total": am.rows_persisted_total,
                "writer_queue_size": am.writer_queue_size,
                "last_commit_seconds": am.last_commit_seconds,
                "delta_init_ok": am.delta_init_ok,
                "delta_last_error": am.delta_last_error,
                "table_path": agg.table_path,
            }

        return out


    def _install_signal_handlers(self) -> None:
        """
        Register SIGINT/SIGTERM handlers to attempt a graceful stop.

        Returns:
            None
        """


        def _handler(signum, frame):
            try: self.stop(flush="auto")
            except Exception: pass
        try: signal.signal(signal.SIGINT, _handler)
        except Exception: pass
        try: signal.signal(signal.SIGTERM, _handler)
        except Exception: pass

    def _atexit_stop(self) -> None:
        """
        atexit hook to attempt a final flush and shutdown.

        Returns:
            None
        """


        try: self.stop(flush="auto")
        except Exception: pass
