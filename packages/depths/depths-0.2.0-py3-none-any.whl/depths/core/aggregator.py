"""
======================================================================
(A) FILE PATH & IMPORT PATH
depths/core/aggregator.py  →  import path: depths.core.aggregator
======================================================================

======================================================================
(B) FILE OVERVIEW (concept & significance in v0.1.2)
Threaded, no-async aggregator that drains validated events from a
Producer buffer, batches them into typed Polars DataFrames, and writes
them to Delta tables (local or S3 URIs). It runs two threads:
  • Poller: decides WHEN to flush (age/near-full/quiet triggers)
  • Writer: decides WHERE/WHAT to persist (serial Delta appends)

Why this matters in v0.1.2:
  - Provides backpressure & durability boundaries between ingestion
    (Producer) and storage (Delta).
  - Ensures schema-typed DataFrames per EventSchema and stable
    partitioning for downstream readers and shipping.
  - Captures the *target table path at enqueue-time* so UTC-day
    rollovers don’t mis-route late batches.
======================================================================

======================================================================
(C) IMPORTS & GLOBALS (what & why)
os, time, threading, queue     → filesystem prep, clock/monotonic, threads, bounded queues
polars as pl                    → typed DataFrames for Delta writes
LogProducer, LogEvent           → upstream buffer & event row shape
LogAggregatorConfig, AggregatorMetrics → flush policy & runtime counters
create_delta, insert_delta      → Delta I/O helpers (init + append)

Globals in this module:
  (none) — all state is instance-bound; writer queue is per-aggregator.
======================================================================
"""

from __future__ import annotations
import os, time, threading, queue
from typing import Optional, List, Dict, Tuple

import polars as pl

from depths.core.producer import LogProducer, LogEvent
from depths.core.config import LogAggregatorConfig, AggregatorMetrics
from depths.io.delta import create_delta, insert_delta

class LogAggregator:
    """
    Threaded aggregator that bridges Producer → Delta.

    Overview (v0.1.2 role):
        A LogAggregator wraps one LogProducer for a single OTel table. It
        continuously polls the producer buffer and, when any trigger fires,
        batches events into a typed Polars DataFrame (using the table’s
        EventSchema) and enqueues it for the writer thread. The writer
        performs serial `insert_delta(...)` appends to the current table.
        On day rollover, `retarget_table_path(...)` is called so that
        *future* batches go to the new day; already-enqueued batches carry
        their captured destination to avoid mis-routing.

    Threads & queues:
        - Poller thread: age/near-full/quiet-based flush scheduling.
        - Writer thread: single-consumer queue that persists DataFrames.
          Queue items are `(pl.DataFrame, target_table_path)`; a `None`
          sentinel requests writer shutdown.

    Configuration:
        - Behavior is driven by LogAggregatorConfig (poll intervals, near-full
          ratio, batch sizing, strict DataFrame construction, Delta write modes).
        - Partitioning is registered at create-time (`partition_by`) only.

    Metrics:
        AggregatorMetrics tracks flush counts, scheduled/persisted rows,
        last commit timings, writer queue size, and last Delta errors. These
        surface via DepthsLogger.metrics() and /healthz.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - No asyncio: safe to embed in FastAPI/other async hosts without loop coupling.
    # - Writer serializes appends to avoid concurrent-write races in delta-rs.
    # - Capturing table path at enqueue time (v0.1 change) is essential for
    #   correctness during UTC day rollover. See DepthsLogger._maybe_rollover_UTC.

    def __init__(self, producer: LogProducer, config: LogAggregatorConfig) -> None:
        """
        Initialize the aggregator around a Producer and a concrete table config.

        Args:
            producer: The upstream LogProducer to drain from.
            config:   LogAggregatorConfig with schema, batching, and Delta write policy.

        Behavior:
            - Extracts the Polars schema from the injected EventSchema.
            - Prepares partitioning and Delta write options.
            - Computes a near-full threshold from the producer queue maxsize
            (if known) using `near_full_ratio`.
            - Ensures the local table directory exists when writing to filesystem.
            - Allocates a bounded writer queue (backpressure).

        Side effects:
            - Creates directories for non-S3 table paths.
            - Resets metrics and thread handles.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - `_q_maxsize` reflects `producer.buffer.maxsize` when available; when 0
        #   or unknown, near-full trigger is effectively disabled.
        # - `strict_df=True` constructs frames with the exact schema, failing early
        #   on column shape/type mismatches coming from Producer.

        self._cfg = config
        self._producer = producer

        self._schema = config.schema.polars_schema()
        self._partition_by = list(config.partition_by) if config.partition_by else None
        self._delta_write_mode_init = config.delta_write_mode_init
        self._delta_write_mode_flush = config.delta_write_mode_flush
        self._delta_write_options = dict(config.delta_write_options or {})

        self._max_age_s = float(config.max_age_s)
        self._near_full_ratio = float(config.near_full_ratio)
        self._poll_interval_s = float(config.poll_interval_s)
        self._quiet_flush_s = config.quiet_flush_s
        self._min_batch_rows = int(config.min_batch_rows)
        self._max_batch_rows = config.max_batch_rows
        self._strict_df = bool(config.strict_df)

        self._table_path = config.table_path
        if not self._table_path.startswith("s3://"):
            os.makedirs(self._table_path, exist_ok=True)

        self._metrics = AggregatorMetrics()
        self._wq: "queue.Queue[Optional[Tuple[pl.DataFrame, str]]]" = queue.Queue(maxsize=config.writer_queue_maxsize)

        self._stop_flag = threading.Event()
        self._poller_thread: Optional[threading.Thread] = None
        self._writer_thread: Optional[threading.Thread] = None

        self._q_maxsize = getattr(self._producer.buffer, "maxsize", 0) or 0
        self._near_full_threshold = int(self._near_full_ratio * self._q_maxsize) if self._q_maxsize > 0 else None

        self._initialize_table_on_start = config.initialize_table
        self._retarget_lock = threading.RLock()

    @property
    def metrics(self) -> AggregatorMetrics:
        """
        Accessor for live aggregator metrics.

        Returns:
            AggregatorMetrics instance updated by poller/worker code paths.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - This object is mutated by the poller and writer threads; reads are
        #   best-effort and not synchronized (intended for lightweight observability).
        return self._metrics

    @property
    def table_path(self) -> str:
        """
        The *current* target table path for newly scheduled batches.

        Returns:
            Table root path/URI as a string (local path or s3://...).
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Previously scheduled batches may carry an older captured path; only
        #   *future* flushes will use the returned value.
        return self._table_path

    def retarget_table_path(self, new_path: str, initialize: bool = True) -> None:
        """
        Change the destination table path for *future* batches, optionally
        ensuring the new table exists.

        Overview (v0.1.2 role):
            Used during UTC-day rollover. The method updates the live target
            path under a lock and (optionally) creates an empty Delta table
            at the new destination to avoid the writer being first-touch.

        Args:
            new_path: New table root path/URI.
            initialize: If True, create the table with an empty, schema-only frame.

        Returns:
            None
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Directory creation is performed for non-S3 paths.
        # - A best-effort Delta create is attempted; "already exists" errors are
        #   treated as benign and surfaced only via metrics.delta_last_error.

        with self._retarget_lock:
            self._table_path = new_path
            if not new_path.startswith("s3://"):
                os.makedirs(new_path, exist_ok=True)
            if initialize:
                try:
                    empty_df = self._empty_df_with_schema()
                    create_delta(
                        table_path=new_path,
                        data=empty_df,
                        mode=self._delta_write_mode_init,
                        storage_options=None,
                        partition_by=self._partition_by,
                        delta_write_options=self._delta_write_options,
                    )
                    self._metrics.delta_init_ok = True
                except Exception as e:
                    self._metrics.delta_last_error = f"retarget_init_failed:{e!r}"

    def start(self) -> None:
        """
        Start the aggregator’s poller and writer threads.

        Behavior:
            - Optionally creates/initializes the table (schema-only DataFrame) if
            `initialize_table=True`.
            - Clears the stop flag and launches the writer, then the poller.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Writer is started first so the poller can immediately enqueue work.
        # - Table initialization uses `create_delta(..., mode=delta_write_mode_init)`.

        if self._initialize_table_on_start:
            try:
                empty_df = self._empty_df_with_schema()
                create_delta(
                    table_path=self._table_path,
                    data=empty_df,
                    mode=self._delta_write_mode_init,
                    storage_options=None,
                    partition_by=self._partition_by,
                    delta_write_options=self._delta_write_options,
                )
                self._metrics.delta_init_ok = True
            except Exception as e:
                self._metrics.delta_last_error = f"init_failed:{e!r}"

        self._stop_flag.clear()

        self._writer_thread = threading.Thread(target=self._writer_loop, name="log-writer", daemon=True)
        self._writer_thread.start()

        self._poller_thread = threading.Thread(target=self._poller_loop, name="log-poller", daemon=True)
        self._poller_thread.start()

    def stop(self, *, flush_remaining: bool = True, join_timeout: Optional[float] = 10.0) -> None:
        """
        Stop the poller and writer threads, optionally flushing remaining items.

        Args:
            flush_remaining: Drain producer buffer before shutdown.
            join_timeout:    Max seconds to wait on thread joins and queue put.

        Behavior:
            - Signals the poller to stop.
            - If `flush_remaining`, drains all remaining events into the writer queue.
            - Enqueues a `None` sentinel to request writer shutdown.
            - Joins threads within the given timeout.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - If the writer queue is full during sentinel enqueue, we swallow the
        #   `queue.Full` and rely on eventual drain to complete shutdown.

        self._stop_flag.set()

        if flush_remaining:
            self._flush_all_remaining()

        try:
            self._wq.put(None, timeout=join_timeout)
        except queue.Full:
            pass

        if self._poller_thread and self._poller_thread.is_alive():
            self._poller_thread.join(timeout=join_timeout)
        if self._writer_thread and self._writer_thread.is_alive():
            self._writer_thread.join(timeout=join_timeout)

    def _poller_loop(self) -> None:
        """
        Poller thread: decides WHEN to flush from the Producer.

        Triggers:
            - Near-full: producer queue size ≥ near_full_ratio × capacity.
            - Age-based: oldest event age ≥ max_age_s.
            - Quiet flush: queue non-empty but below near-full, and no flush
            for ≥ quiet_flush_s since last schedule.

        Behavior:
            - Repeatedly drains batches (respecting max_batch_rows when set).
            - Constructs typed DataFrames with the configured schema (strict or not).
            - Enqueues `(df, captured_table_path)` to the writer queue.
            - Updates metrics for each scheduled batch.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - `last_flush_mono` and `quiet_flush_s` implement “age since last flush”
        #   rather than “time since last enqueue”; this avoids pathological churn.
        # - When `max_batch_rows` is None, a single drain() is attempted per trigger.
        # - Backoff: sleeps for `poll_interval_s` when no trigger fires or no rows were drained.
        # - Capture target path *now* so rollover later does not affect this batch
                    

        last_flush_mono = time.perf_counter()
        self._metrics.last_flush_mono = last_flush_mono

        while not self._stop_flag.is_set():
            qsize = self._producer.queue_size()
            age = self._producer.oldest_age_seconds()
            now_mono = time.perf_counter()

            near_full = (self._near_full_threshold is not None and qsize >= self._near_full_threshold)
            age_hit = (age is not None) and (age >= self._max_age_s)
            quiet_hit = (
                self._quiet_flush_s is not None
                and 0 < qsize < (self._near_full_threshold or float("inf"))
                and (now_mono - last_flush_mono) >= self._quiet_flush_s
            )

            if near_full or age_hit or quiet_hit:
                drained_any = False
                while True:
                    batch = self._drain_batch()
                    if not batch:
                        break
                    drained_any = True

                    df = pl.DataFrame(batch, schema=self._schema, strict=self._strict_df)
                    target_path = self._table_path
                    self._wq.put((df, target_path))  

                    n = df.height
                    self._metrics.flushes += 1
                    self._metrics.rows_scheduled_total += n
                    self._metrics.rows_last_flush = n
                    self._metrics.last_flush_ts = time.time()
                    last_flush_mono = now_mono
                    self._metrics.last_flush_mono = last_flush_mono
                    self._metrics.writer_queue_size = self._wq.qsize()

                    if self._max_batch_rows is None:
                        break
                if not drained_any:
                    time.sleep(self._poll_interval_s)
            else:
                time.sleep(self._poll_interval_s)

    def _writer_loop(self) -> None:
        """
        Writer thread: serially persists queued DataFrames to Delta.

        Behavior:
            - Blocks on the writer queue, exits on `None` sentinel or stop flag.
            - For each `(df, target_table)`, calls `insert_delta(...)` with flush mode.
            - Records last commit duration and increments persisted row counters.
            - At shutdown, best-effort drains any leftover items (including a final sentinel).

        Error handling:
            - Any exception during append updates `metrics.delta_last_error`
            with a compact error string and continues.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Commit timing uses monotonic `perf_counter()` for stability.
        # - Partitioning is set at table creation; insert ignores it here.
        # - The final “best-effort drain” after breaking the loop reduces the risk
        #   of stranded in-flight batches when the sentinel arrives early.

        while True:
            try:
                item = self._wq.get(timeout=0.5)
            except queue.Empty:
                if self._stop_flag.is_set():
                    break
                continue

            if item is None:
                break

            df, target_table = item
            t0 = time.perf_counter()
            try:
                insert_delta(
                    table_path=target_table,
                    data=df,
                    mode=self._delta_write_mode_flush,
                    storage_options=None,
                    delta_write_options=self._delta_write_options,
                )
                elapsed = time.perf_counter() - t0
                self._metrics.last_commit_seconds = elapsed
                self._metrics.rows_persisted_total += df.height
            except Exception as e:
                self._metrics.delta_last_error = f"append_failed:{e!r}"
            finally:
                self._metrics.writer_queue_size = self._wq.qsize()
                self._wq.task_done()

        while True:
            try:
                it = self._wq.get_nowait()
                if it is None:
                    self._wq.task_done()
                    break
                try:
                    df, target_table = it
                    insert_delta(
                        table_path=target_table,
                        data=df,
                        mode=self._delta_write_mode_flush,
                        storage_options=None,
                        partition_by=None,
                        delta_write_options=self._delta_write_options,
                    )
                    self._metrics.rows_persisted_total += df.height
                except Exception as e:
                    self._metrics.delta_last_error = f"append_failed_shutdown:{e!r}"
                finally:
                    self._wq.task_done()
            except queue.Empty:
                break

    def _flush_all_remaining(self) -> None:
        """
        Drain the Producer buffer completely into the writer queue.

        Behavior:
            - Repeatedly `drain()` the producer (respecting `max_batch_rows`).
            - Enqueue DataFrames until the buffer is empty.
            - Update scheduling-related metrics for each enqueued batch.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - This method does not block on writer completion; it only schedules.
        # - Intended for graceful shutdowns (`stop(flush_remaining=True)`).

        while True:
            batch = self._drain_batch()
            if not batch:
                break
            df = pl.DataFrame(batch, schema=self._schema, strict=self._strict_df)
            target_path = self._table_path
            self._wq.put((df, target_path))
            n = df.height
            self._metrics.flushes += 1
            self._metrics.rows_scheduled_total += n
            self._metrics.rows_last_flush = n
            self._metrics.last_flush_ts = time.time()
            self._metrics.last_flush_mono = time.perf_counter()
            self._metrics.writer_queue_size = self._wq.qsize()

    def _drain_batch(self) -> List[LogEvent]:
        """
        Drain at most `max_batch_rows` events from the Producer.

        Returns:
            List of LogEvent dicts (possibly empty).
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - When `max_batch_rows` is None, defers to `producer.drain()` for “all”.

        if self._max_batch_rows is None:
            return self._producer.drain()
        return self._producer.drain(self._max_batch_rows)

    def _empty_df_with_schema(self) -> pl.DataFrame:
        """
        Construct an empty Polars DataFrame that matches the configured schema.

        Returns:
            A zero-row DataFrame with columns/dtypes aligned to `self._schema`.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Used for initial Delta table creation so the table has a concrete
        #   schema even before the first append.

        cols = {name: pl.Series(name, [], dtype=self._schema[name]) for name in self._schema.keys()}
        return pl.DataFrame(cols)
