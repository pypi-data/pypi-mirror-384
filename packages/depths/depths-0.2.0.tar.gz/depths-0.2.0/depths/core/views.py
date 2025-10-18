"""
Runtime sidecars for Depths (v0.2.0).

This module implements two runtime "views" that sit alongside the ingest → aggregate
pipeline and operate entirely in-process:

1) RealtimeTap
   An in-memory, bounded FIFO for live reads. It keeps raw event dicts in three
   family queues (traces, logs, metrics) and provides:
     • push(...) to append new items
     • read(...) to retrieve the newest items
     • sse_iter(...) to stream Server‑Sent Events (SSE)

2) Stats
   A generalized stats sidecar that maintains queryable rollups for developer‑
   selected columns as independent tracking tasks per (project_id, otel_table,
   column, window). Two kinds are supported via separate Delta tables:
     • Categorical (string): category histograms (categories[], counts[])
     • Numeric (int/float):  event_count, value_min/max/mean/std(sum) [population std]

Persistence layout (local Delta Lake):
  <instance_root>/stats/
    ├── registry.json                # declared tracking tasks (restart seed)
    ├── categorical_stats            # Delta table, partitioned by project_id/window/otel_table/column
    └── numeric_stats                # Delta table, partitioned by project_id/window/otel_table/column

Scheduling & correctness:
  • Minute-tick worker; windows allowed: {1, 5, 15, 30, 60, 1440} minutes.
  • New/removed tasks take effect on the *next* UTC minute boundary.
  • Late data tolerance via StatsConfig.allowed_lateness_s; buckets are flushed
    only when fully closed relative to that safety window.
  • Compaction runs every StatsConfig.optimize_frequency flush waves.

All public methods use PEP‑style docstrings (Args/Returns/Raises) for ergonomic use.
"""

from __future__ import annotations

import json
import math
import threading
import time
import hashlib
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, Iterable, Iterator, List, Mapping, Optional

import polars as pl
import datetime as dt

from depths.io.delta import create_delta, insert_delta, optimize
from depths.core.config import RealtimeReadConfig, StatsConfig, _save_json, _load_json


class RealtimeTap:
    """
    In-memory, bounded FIFO view of raw dicts for real-time reads.

    Overview:
        Organizes incoming events into three family queues:
        • "traces": spans, span_events, span_links
        • "logs":   logs
        • "metrics": metrics_points, metrics_hist

        The tap is append-only; when a family queue reaches its capacity,
        the oldest items are dropped (drop-old policy). This class is read-only
        from the perspective of downstream users: ingestion code calls `push`,
        while UIs/tests call `read` or consume `sse_iter`.

    Args:
        config: RealtimeReadConfig with per-family caps (max_traces/max_logs/max_metrics).

    Public API:
        push(signal, raw) -> None
        read(signal, n=100, project_id=None) -> list[dict]
        sse_iter(signal, project_id=None, heartbeat_s=10, poll_interval_s=1.0) -> Iterator[bytes]
    """

    def __init__(self, config: RealtimeReadConfig) -> None:
        """
        Initialize capped deques and family locks.

        Args:
            config: Typed realtime configuration object.

        Returns:
            None
        """
        self._cfg = config
        self._caps = {
            "traces": int(config.max_traces),
            "logs": int(config.max_logs),
            "metrics": int(config.max_metrics),
        }
        self._qs: Dict[str, Deque[dict]] = {
            "traces": deque(maxlen=self._caps["traces"]),
            "logs": deque(maxlen=self._caps["logs"]),
            "metrics": deque(maxlen=self._caps["metrics"]),
        }
        self._locks = {
            "traces": threading.Lock(),
            "logs": threading.Lock(),
            "metrics": threading.Lock(),
        }

    @staticmethod
    def _fam(signal: str) -> Optional[str]:
        """
        Map an OTLP table name to a realtime family.

        Args:
            signal: Table name: "spans" | "span_events" | "span_links" | "logs" |
                    "metrics_points" | "metrics_hist".

        Returns:
            "traces" | "logs" | "metrics" or None if unsupported.
        """
        s = signal.lower()
        if s in {"spans", "span", "span_events", "span_links"}:
            return "traces"
        if s in {"logs", "log"}:
            return "logs"
        if s in {"metrics", "metric", "metrics_points", "metrics_point", "metrics_hist", "metrics_histogram"}:
            return "metrics"
        return None

    def push(self, signal: str, raw: Mapping[str, Any]) -> None:
        """
        Append a raw telemetry dict to a realtime queue.

        Args:
            signal: Signal name to route to a family.
            raw:    Mapping representing the event to store (copied defensively).

        Returns:
            None
        """
        fam = self._fam(signal)
        if fam is None:
            return
        q = self._qs[fam]
        with self._locks[fam]:
            q.append(dict(raw))

    def read(self, signal: str, n: int = 100, project_id: Optional[str] = None) -> List[dict]:
        """
        Return the newest items from a family queue, optionally filtered by project.

        Args:
            signal:      Signal family selector.
            n:           Maximum items to include (tail semantics).
            project_id:  Optional equality filter on the 'project_id' field.

        Returns:
            List[dict] in chronological order (oldest → newest).
        """
        fam = self._fam(signal)
        if fam is None:
            return []
        q = self._qs[fam]
        with self._locks[fam]:
            items = list(q)[-int(max(0, n)) :]
        if project_id:
            items = [r for r in items if str(r.get("project_id", "")) == project_id]
        return items

    def sse_iter(
        self,
        signal: str,
        *,
        project_id: Optional[str] = None,
        heartbeat_s: int = 10,
        poll_interval_s: float = 1.0,
    ) -> Iterator[bytes]:
        """
        Yield an SSE stream for a realtime family.

        Args:
            signal:         Signal name ("spans", "logs", "metrics_points", ...).
            project_id:     Optional filter limiting rows to a project.
            heartbeat_s:    Interval (seconds) for comment heartbeats.
            poll_interval_s:Polling interval between deque polls.

        Returns:
            Iterator yielding SSE-framed bytes: b"data: <json>\n\n" and b": heartbeat\n\n".
        """
        fam = self._fam(signal)
        if fam is None:
            def _it() -> Iterator[bytes]:
                """Emit a single SSE comment indicating the signal is unsupported."""
                yield b": unsupported signal\n\n"
            return _it()

        last_len = 0
        t0 = time.monotonic()
        initial = self.read(signal, n=self._caps[fam], project_id=project_id)
        for r in initial:
            payload = json.dumps(r, separators=(",", ":")).encode("utf-8")
            yield b"data: " + payload + b"\n\n"
        while True:
            now = time.monotonic()
            if now - t0 >= heartbeat_s:
                yield b": heartbeat\n\n"
                t0 = now
            time.sleep(max(0.0, poll_interval_s))
            with self._locks[fam]:
                cur = list(self._qs[fam])
                new = cur[last_len:]
                last_len = len(cur)
            if project_id:
                new = [r for r in new if str(r.get("project_id", "")) == project_id]
            for r in new:
                payload = json.dumps(r, separators=(",", ":")).encode("utf-8")
                yield b"data: " + payload + b"\n\n"


class Stats:
    """
    Generalized stats sidecar (v0.2.0).

    Two independent stat kinds are supported and stored in separate Delta tables:
      • Categorical (value is string): per-bucket category histogram (categories[], counts[])
      • Numeric (value is int/float):  event_count, value_min, value_max, value_mean,
                                       value_std (population), value_sum

    Design:
      • Each (project_id, otel_table, column, window) is an independent tracker.
      • Windows allowed: {1, 5, 15, 30, 60, 1440}. Activation/removal occurs on the *next* UTC minute.
      • Partitions: project_id/window/otel_table/column for both categorical and numeric tables.
      • Registry persisted at <instance_root>/stats/registry.json for restart semantics.
      • Late-data tolerance via allowed_lateness_s; minute scheduler flushes closed buckets.
      • Compaction via optimize() every N flush waves (optimize_frequency).
    """

    _ALLOWED_WINDOWS = {1, 5, 15, 30, 60, 1440}

    def __init__(
        self,
        instance_root: Path | str,
        config: StatsConfig,
        *,
        schemas: Mapping[str, Any],
    ) -> None:
        """
        Construct a Stats sidecar.

        Args:
            instance_root: Instance base directory.
            config:        StatsConfig governing lateness/compaction/category caps.
            schemas:       Mapping of OTel table name → EventSchema (for field validation).

        Returns:
            None
        """
        self._cfg = config
        self._root = Path(instance_root)
        self._stats_dir = self._root / "stats"
        self._cat_table_path = str(self._stats_dir / "categorical_stats")
        self._num_table_path = str(self._stats_dir / "numeric_stats")

        self._allowed_lateness_s = int(config.allowed_lateness_s)
        self._optimize_frequency = max(1, int(config.optimize_frequency))
        self._max_categories = max(1, int(config.max_categories))

        self._schemas = dict(schemas or {})

        self._cat_tasks: set[tuple[str, str, str, int]] = set()
        self._num_tasks: set[tuple[str, str, str, int]] = set()

        self._task_active_after: dict[tuple[str, str, str, int], int] = {}
        self._task_stop_after: dict[tuple[str, str, str, int], int | None] = {}

        self._cat_state: dict[tuple[str, str, str, int], dict[int, dict[str, int]]] = {}
        self._num_state: dict[tuple[str, str, str, int], dict[int, dict[str, float]]] = {}

        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._flush_counter = 0

        self._ensure_tables()
        self._load_registry_seed_tasks()

    def start(self) -> None:
        """
        Start the minute-tick worker (idempotent).

        Returns:
            None
        """
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="Stats", daemon=True)
        self._thread.start()

    def stop(self, flush_remaining: bool = True) -> None:
        """
        Stop the minute-tick worker and optionally flush remaining buckets.

        Args:
            flush_remaining: When True, finalize and persist any open buckets.

        Returns:
            None
        """
        if self._thread is None:
            return
        self._stop.set()
        self._thread.join(timeout=5.0)
        self._thread = None
        if flush_remaining:
            self._flush_ready(final=True)

    @property
    def _registry_path(self) -> Path:
        """Return the on-disk path for the stats registry (JSON)."""
        return self._stats_dir / "registry.json"

    def _load_registry_seed_tasks(self) -> None:
        """
        Load registry.json and seed tasks/states for this process (best effort).

        Returns:
            None
        """
        reg = _load_json(self._registry_path) or {"tasks": []}
        now_min = int(dt.datetime.now(dt.UTC).timestamp() // 60)
        for t in reg.get("tasks", []):
            tup = (str(t["project_id"]), str(t["otel_table"]), str(t["column"]), int(t["window"]))
            kind = str(t.get("kind") or "")
            if kind == "categorical":
                self._cat_tasks.add(tup)
                self._cat_state.setdefault(tup, {})
            elif kind == "numeric":
                self._num_tasks.add(tup)
                self._num_state.setdefault(tup, {})
            else:
                continue
            self._task_active_after[tup] = now_min
            self._task_stop_after[tup] = None

    def _persist_registry(self) -> None:
        """
        Persist the current set of tasks to registry.json.

        Returns:
            None
        """
        tasks: list[dict] = []
        for (p, ot, col, w) in sorted(self._cat_tasks):
            tasks.append({"project_id": p, "otel_table": ot, "column": col, "window": w, "kind": "categorical"})
        for (p, ot, col, w) in sorted(self._num_tasks):
            tasks.append({"project_id": p, "otel_table": ot, "column": col, "window": w, "kind": "numeric"})
        _save_json(self._registry_path, {"tasks": tasks})

    @staticmethod
    def _minute_ts_from_ms(ms: int) -> int:
        """Convert epoch milliseconds to epoch minutes."""
        return int(ms // 60000)

    @staticmethod
    def _bucket_start_minute(minute_ts: int, window: int) -> int:
        """Return the bucket-aligned minute start for a window size."""
        return int((minute_ts // window) * window)

    @staticmethod
    def _now_safe_minute(allowed_lateness_s: int) -> int:
        """
        Compute the latest minute that is safe to finalize given allowed lateness.

        Args:
            allowed_lateness_s: Seconds to subtract from "now" before minute rounding.

        Returns:
            Epoch minute considered safely closed.
        """
        now_ms = int(dt.datetime.now(dt.UTC).timestamp() * 1000)
        return ((now_ms // 1000) - int(allowed_lateness_s)) // 60

    @staticmethod
    def _resolve_event_ts_ms(signal: str, row: Mapping[str, Any]) -> int:
        """
        Resolve an event timestamp in milliseconds from a mapped row.

        Priority:
            1) event_ts (ms)
            2) time_unix_nano / start_time_unix_nano / observed_time_unix_nano / end_time_unix_nano (ns → ms)
            3) current UTC time (ms)

        Args:
            signal: Original signal hint (spans/logs/metrics_points/...).
            row:    Mapped row dict from the OTLP mapper.

        Returns:
            Epoch milliseconds suitable for minute bucketing.
        """
        evt_ms = row.get("event_ts")
        if isinstance(evt_ms, int) and evt_ms > 0:
            return evt_ms
        for k in ("time_unix_nano", "start_time_unix_nano", "observed_time_unix_nano", "end_time_unix_nano"):
            ns = row.get(k)
            if isinstance(ns, int) and ns > 0:
                return ns // 1_000_000
        now_ms = int(dt.datetime.now(dt.UTC).timestamp() * 1000)
        return now_ms

    @staticmethod
    def _is_str_type(pytype: type | tuple | None) -> bool:
        """Return True if the schema field type is a string."""
        return pytype is str

    @staticmethod
    def _is_numeric_type(pytype: type | tuple | None) -> bool:
        """Return True if the schema field type is int or float."""
        return pytype in (int, float)

    def _validate_field(self, otel_table: str, column: str, *, want: str) -> None:
        """
        Validate that a table+column exists in the composed schema and matches the desired kind.

        Args:
            otel_table: OTel table name.
            column:     Top-level column name to validate.
            want:       'categorical' or 'numeric'.

        Raises:
            ValueError: Unknown table or invalid 'want' value.
            TypeError:  Column type mismatch for the requested kind.
        """
        schema = self._schemas.get(otel_table)
        if not schema:
            raise ValueError(f"Unknown otel_table {otel_table!r}; no schema injected")
        pytype = schema.fields.get(column)
        if want == "categorical":
            if not self._is_str_type(pytype):
                raise TypeError(f"Column {column!r} in {otel_table!r} is not a string field")
        elif want == "numeric":
            if not self._is_numeric_type(pytype):
                raise TypeError(f"Column {column!r} in {otel_table!r} is not numeric (int/float)")
        else:
            raise ValueError("want must be 'categorical' or 'numeric'")

    def _clamp_next_minute(self) -> int:
        """Return the next UTC minute (epoch minutes)."""
        now_ms = int(dt.datetime.now(dt.UTC).timestamp() * 1000)
        cur_min = now_ms // 60000
        return int(cur_min + 1)

    def add_category(self, *, project_id: str, otel_table: str, column: str, windows: Iterable[int]) -> None:
        """
        Register one or more categorical trackers for a column.

        Args:
            project_id: Project id for tenancy.
            otel_table: OTel table name.
            column:     String-typed column to track (top-level field).
            windows:    Iterable of window sizes in minutes (allowed: 1,5,15,30,60,1440).

        Returns:
            None

        Raises:
            TypeError/ValueError: When validation fails.
        """
        self._validate_field(otel_table, column, want="categorical")
        next_min = self._clamp_next_minute()
        changed = False
        with self._lock:
            for w in windows:
                w = int(w)
                if w not in self._ALLOWED_WINDOWS:
                    continue
                key = (str(project_id), str(otel_table), str(column), w)
                if key in self._cat_tasks:
                    continue
                self._cat_tasks.add(key)
                self._cat_state.setdefault(key, {})
                self._task_active_after[key] = next_min
                self._task_stop_after[key] = None
                changed = True
        if changed:
            self._persist_registry()

    def add_numeric(self, *, project_id: str, otel_table: str, column: str, windows: Iterable[int]) -> None:
        """
        Register one or more numeric trackers for a column.

        Args:
            project_id: Project id for tenancy.
            otel_table: OTel table name.
            column:     Numeric column to track (int or float, top-level field).
            windows:    Iterable of window sizes in minutes (allowed: 1,5,15,30,60,1440).

        Returns:
            None

        Raises:
            TypeError/ValueError: When validation fails.
        """
        self._validate_field(otel_table, column, want="numeric")
        next_min = self._clamp_next_minute()
        changed = False
        with self._lock:
            for w in windows:
                w = int(w)
                if w not in self._ALLOWED_WINDOWS:
                    continue
                key = (str(project_id), str(otel_table), str(column), w)
                if key in self._num_tasks:
                    continue
                self._num_tasks.add(key)
                self._num_state.setdefault(key, {})
                self._task_active_after[key] = next_min
                self._task_stop_after[key] = None
                changed = True
        if changed:
            self._persist_registry()

    def remove(self, *, project_id: str, otel_table: str, column: str, window: int) -> None:
        """
        Mark a previously registered tracker for removal on the next UTC minute boundary.

        Args:
            project_id: Project id.
            otel_table: OTel table name.
            column:     Column name.
            window:     Window size in minutes.

        Returns:
            None
        """
        key = (str(project_id), str(otel_table), str(column), int(window))
        next_min = self._clamp_next_minute()
        with self._lock:
            if key in self._cat_tasks or key in self._num_tasks:
                self._task_stop_after[key] = next_min

    def enqueue(self, signal: str, row: Mapping[str, Any]) -> None:
        """
        Tee an incoming normalized row into active stat trackers.

        Args:
            signal: OTel table name used during registration.
            row:    Mapped row dictionary.

        Returns:
            None
        """
        project_id = str(row.get("project_id", "default"))
        otel_table = str(signal)
        minute_ts = self._minute_ts_from_ms(self._resolve_event_ts_ms(signal, row))

        with self._lock:
            for (p, ot, col, w) in list(self._cat_tasks):
                if p != project_id or ot != otel_table:
                    continue
                act = self._task_active_after.get((p, ot, col, w), 0)
                stop = self._task_stop_after.get((p, ot, col, w))
                if minute_ts < act or (stop is not None and minute_ts >= stop):
                    continue
                val = row.get(col, None)
                if not (isinstance(val, str) and val != ""):
                    continue
                bucket_min = self._bucket_start_minute(minute_ts, w)
                buckets = self._cat_state[(p, ot, col, w)]
                ctr = buckets.get(bucket_min)
                if ctr is None:
                    ctr = {}
                    buckets[bucket_min] = ctr
                if val in ctr:
                    ctr[val] += 1
                else:
                    if len(ctr) < self._max_categories:
                        ctr[val] = 1

            for (p, ot, col, w) in list(self._num_tasks):
                if p != project_id or ot != otel_table:
                    continue
                act = self._task_active_after.get((p, ot, col, w), 0)
                stop = self._task_stop_after.get((p, ot, col, w))
                if minute_ts < act or (stop is not None and minute_ts >= stop):
                    continue
                v = row.get(col, None)
                if not isinstance(v, (int, float)):
                    continue
                v = float(v)
                bucket_min = self._bucket_start_minute(minute_ts, w)
                buckets = self._num_state[(p, ot, col, w)]
                agg = buckets.get(bucket_min)
                if agg is None:
                    agg = {"count": 0, "sum": 0.0, "sumsq": 0.0, "min": float("inf"), "max": float("-inf")}
                    buckets[bucket_min] = agg
                agg["count"] += 1
                agg["sum"] += v
                agg["sumsq"] += v * v
                if v < agg["min"]:
                    agg["min"] = v
                if v > agg["max"]:
                    agg["max"] = v

    def _run(self) -> None:
        """Minute-tick worker loop that finalizes and flushes ready buckets."""
        last_checked_min = None
        while not self._stop.is_set():
            now_min = int(dt.datetime.now(dt.UTC).timestamp() // 60)
            if now_min != last_checked_min:
                self._flush_ready(final=False)
                last_checked_min = now_min
            self._stop.wait(timeout=1.0)

    def _flush_ready(self, *, final: bool) -> None:
        """
        Materialize closed buckets into Delta tables and run periodic compaction.

        Args:
            final: When True, finalize all remaining buckets regardless of lateness window.

        Returns:
            None
        """
        safe_min = self._now_safe_minute(self._allowed_lateness_s)

        cat_rows: list[dict] = []
        num_rows: list[dict] = []

        with self._lock:
            for key, buckets in list(self._cat_state.items()):
                p, ot, col, w = key
                to_pop = []
                for bstart, ctr in buckets.items():
                    if final or (bstart + w - 1) <= safe_min:
                        if not ctr:
                            to_pop.append(bstart)
                            continue
                        cats = list(ctr.keys())
                        counts = [int(ctr[c]) for c in cats]
                        snap_ts = int(dt.datetime.now(dt.UTC).timestamp() * 1000)
                        bkey_src = (p, w, ot, col, bstart, snap_ts)
                        bucket_key = hashlib.sha1("|".join(map(str, bkey_src)).encode("utf-8")).hexdigest()
                        cat_rows.append(
                            {
                                "project_id": p,
                                "window": int(w),
                                "otel_table": ot,
                                "column": col,
                                "minute_ts": int(bstart),
                                "categories": cats,
                                "counts": counts,
                                "snapshot_ts": snap_ts,
                                "bucket_key": bucket_key,
                            }
                        )
                        to_pop.append(bstart)
                for b in to_pop:
                    buckets.pop(b, None)

            for key, buckets in list(self._num_state.items()):
                p, ot, col, w = key
                to_pop = []
                for bstart, agg in buckets.items():
                    if final or (bstart + w - 1) <= safe_min:
                        cnt = int(agg.get("count", 0))
                        if cnt <= 0:
                            to_pop.append(bstart)
                            continue
                        s = float(agg["sum"])
                        ss = float(agg["sumsq"])
                        mean = s / cnt
                        var = max(ss / cnt - mean * mean, 0.0)
                        mean=round(mean,4)
                        std = round(math.sqrt(var),4)
                        vmin = float(agg["min"]) if math.isfinite(agg["min"]) else None
                        vmax = float(agg["max"]) if math.isfinite(agg["max"]) else None

                        snap_ts = int(dt.datetime.now(dt.UTC).timestamp() * 1000)
                        bkey_src = (p, w, ot, col, bstart, snap_ts)
                        bucket_key = hashlib.sha1("|".join(map(str, bkey_src)).encode("utf-8")).hexdigest()

                        num_rows.append(
                            {
                                "project_id": p,
                                "window": int(w),
                                "otel_table": ot,
                                "column": col,
                                "minute_ts": int(bstart),
                                "event_count": cnt,
                                "value_min": vmin,
                                "value_max": vmax,
                                "value_mean": mean,
                                "value_std": std,
                                "value_sum": s,
                                "snapshot_ts": snap_ts,
                                "bucket_key": bucket_key,
                            }
                        )
                        to_pop.append(bstart)
                for b in to_pop:
                    buckets.pop(b, None)

        if cat_rows:
            cdf = pl.DataFrame(cat_rows, schema=self._cat_schema())
            insert_delta(table_path=self._cat_table_path, data=cdf)

        if num_rows:
            ndf = pl.DataFrame(num_rows, schema=self._num_schema())
            insert_delta(table_path=self._num_table_path, data=ndf)

        if cat_rows or num_rows:
            self._flush_counter += 1
            if self._flush_counter % self._optimize_frequency == 0:
                try:
                    optimize(self._cat_table_path)
                except Exception:
                    pass
                try:
                    optimize(self._num_table_path)
                except Exception:
                    pass

    def lazy_read_categorical_stats(
        self,
        *,
        project_id: Optional[str] = None,
        otel_table: Optional[str] = None,
        column: Optional[str] = None,
        window: Optional[int] = None,
        minute_ts_from: Optional[int] = None,
        minute_ts_to: Optional[int] = None,
        latest_only: bool = True,
    ) -> pl.LazyFrame:
        """
        Construct a lazy query against the categorical stats table with optional filters.

        Args:
            project_id:      Project id filter.
            otel_table:      Table name filter.
            column:          Column name filter.
            window:          Window size in minutes.
            minute_ts_from:  Inclusive lower bound on bucket minute.
            minute_ts_to:    Inclusive upper bound on bucket minute.
            latest_only:     Return only the latest snapshot per (p, w, t, c, minute_ts).

        Returns:
            pl.LazyFrame with deferred filters and grouping.
        """
        lf = pl.scan_delta(self._cat_table_path)
        if project_id:
            lf = lf.filter(pl.col("project_id") == project_id)
        if otel_table:
            lf = lf.filter(pl.col("otel_table") == otel_table)
        if column:
            lf = lf.filter(pl.col("column") == column)
        if window is not None:
            lf = lf.filter(pl.col("window") == int(window))
        if minute_ts_from is not None:
            lf = lf.filter(pl.col("minute_ts") >= int(minute_ts_from))
        if minute_ts_to is not None:
            lf = lf.filter(pl.col("minute_ts") <= int(minute_ts_to))

        if latest_only:
            wcols = [pl.col(c) for c in ("project_id", "window", "otel_table", "column", "minute_ts")]
            lf = lf.sort("snapshot_ts").group_by(wcols).tail(1)
        return lf

    def lazy_read_numeric_stats(
        self,
        *,
        project_id: Optional[str] = None,
        otel_table: Optional[str] = None,
        column: Optional[str] = None,
        window: Optional[int] = None,
        minute_ts_from: Optional[int] = None,
        minute_ts_to: Optional[int] = None,
        latest_only: bool = True,
    ) -> pl.LazyFrame:
        """
        Construct a lazy query against the numeric stats table with optional filters.

        Args:
            project_id:      Project id filter.
            otel_table:      Table name filter.
            column:          Column name filter.
            window:          Window size in minutes.
            minute_ts_from:  Inclusive lower bound on bucket minute.
            minute_ts_to:    Inclusive upper bound on bucket minute.
            latest_only:     Return only the latest snapshot per (p, w, t, c, minute_ts).

        Returns:
            pl.LazyFrame with deferred filters and grouping.
        """
        lf = pl.scan_delta(self._num_table_path)
        if project_id:
            lf = lf.filter(pl.col("project_id") == project_id)
        if otel_table:
            lf = lf.filter(pl.col("otel_table") == otel_table)
        if column:
            lf = lf.filter(pl.col("column") == column)
        if window is not None:
            lf = lf.filter(pl.col("window") == int(window))
        if minute_ts_from is not None:
            lf = lf.filter(pl.col("minute_ts") >= int(minute_ts_from))
        if minute_ts_to is not None:
            lf = lf.filter(pl.col("minute_ts") <= int(minute_ts_to))

        if latest_only:
            wcols = [pl.col(c) for c in ("project_id", "window", "otel_table", "column", "minute_ts")]
            lf = lf.sort("snapshot_ts").group_by(wcols).tail(1)
        return lf

    @staticmethod
    def _cat_schema() -> Dict[str, pl.DataType]:
        """Polars schema for the categorical stats Delta table."""
        return {
            "project_id": pl.Utf8,
            "window": pl.Int64,
            "otel_table": pl.Utf8,
            "column": pl.Utf8,
            "minute_ts": pl.Int64,
            "categories": pl.List(pl.Utf8),
            "counts": pl.List(pl.Int64),
            "snapshot_ts": pl.Int64,
            "bucket_key": pl.Utf8,
        }

    @staticmethod
    def _num_schema() -> Dict[str, pl.DataType]:
        """Polars schema for the numeric stats Delta table."""
        return {
            "project_id": pl.Utf8,
            "window": pl.Int64,
            "otel_table": pl.Utf8,
            "column": pl.Utf8,
            "minute_ts": pl.Int64,
            "event_count": pl.Int64,
            "value_min": pl.Float64,
            "value_max": pl.Float64,
            "value_mean": pl.Float64,
            "value_std": pl.Float64,
            "value_sum": pl.Float64,
            "snapshot_ts": pl.Int64,
            "bucket_key": pl.Utf8,
        }

    def _ensure_tables(self) -> None:
        """
        Create both Delta tables if absent using empty schema-only frames.

        Returns:
            None
        """
        self._stats_dir.mkdir(parents=True, exist_ok=True)

        cempty = pl.DataFrame({k: pl.Series(name=k, values=[], dtype=dtp) for k, dtp in self._cat_schema().items()})
        create_delta(
            table_path=self._cat_table_path,
            data=cempty,
            mode="ignore",
            partition_by=["project_id", "window", "otel_table", "column"],
        )

        nempty = pl.DataFrame({k: pl.Series(name=k, values=[], dtype=dtp) for k, dtp in self._num_schema().items()})
        create_delta(
            table_path=self._num_table_path,
            data=nempty,
            mode="ignore",
            partition_by=["project_id", "window", "otel_table", "column"],
        )
