"""
======================================================================
(A) FILE PATH & IMPORT PATH
depths/core/producer.py  →  import path: depths.core.producer
======================================================================

======================================================================
(B) FILE OVERVIEW (concept & significance in v0.1.2)
Single-process, thread-safe producer that validates, normalizes, and
buffers events (LogEvent dicts) against an EventSchema. The Aggregator
drains this bounded queue and persists typed DataFrames to Delta tables.

Responsibilities:
  • Enforce schema contract: defaults → computed → extra policy → required
  • Serialize designated JSON fields deterministically
  • Coerce types (configurable) and check date coherence (UTC)
  • Normalize correlation IDs (trace_id/span_id) & service_name partition safety
  • Apply backpressure/drop policies: block | drop_new | drop_old
  • Maintain lightweight ProducerMetrics and a small audit ring for recent rejects

Why this matters:
  Producer is the *gatekeeper* for the six OTel tables. It ensures clean,
  partition-safe rows so that Aggregator and Delta writes remain predictable.
======================================================================

======================================================================
(C) IMPORTS & GLOBALS (what & why)
threading, queue, time        → lockless counters + bounded queue + age tracking
json, re, logging             → deterministic JSON + validators + debug
polars as pl                  → dtype map for coercion (Utf8/Int*/Float*/Boolean)
LogProducerConfig, ProducerMetrics → policy and counters
EventSchema                   → schema descriptor with defaults/required/computed/json_fields

Globals:
  LogEvent: typing alias for Dict[str, Any] used throughout the pipeline
  DATE_RE:  strict 'YYYY-MM-DD' regex used by UTC day coherence checks
======================================================================
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Tuple, Iterable, List, Callable
import threading, queue, time, json, re, logging
import polars as pl
from depths.core.config import LogProducerConfig, ProducerMetrics
from depths.core.schema import EventSchema

# Doc:
# Canonical event row type accepted by the Producer and emitted to the Aggregator.

# --- DEVELOPER NOTES -----------------------------------------------------
# - Keep as Dict[str, Any]; normalization ensures final values match schema types.

LogEvent = Dict[str, Any]

# Doc:
# Strict validator for event_date strings: UTC day in 'YYYY-MM-DD'.

# --- DEVELOPER NOTES -----------------------------------------------------
# - Used only in date coherence checks; keep in sync with schema expectations.

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class LogProducer:
    """
    Validate and enqueue events according to a concrete EventSchema.

    Overview (v0.1.2 role):
        Acts as the ingestion boundary for a single OTel table. For each input
        mapping it performs: apply defaults → computed fields → extra-field policy
        → required checks → JSON field serialization (+ optional round-trip verify)
        → dtype coercion → service_name/OTLP id normalization → UTC date coherence.
        Accepted rows are placed on a bounded queue honoring the configured
        drop_policy. Aggregator drains the queue based on age/near-full/quiet triggers.

    Key behaviors:
        - Backpressure: 'block' waits on space; 'drop_new' rejects when full;
          'drop_old' evicts one oldest entry to admit the new one.
        - Observability: ProducerMetrics counters and a small ring of recent
          rejection reasons (timestamps) support diagnosis via /healthz.

    Attributes:
        _cfg:        LogProducerConfig currently in force.
        _schema:     EventSchema for the connected OTel table.
        _q:          Bounded Queue[LogEvent] for downstream drain.
        _metrics:    ProducerMetrics updated under a small lock.
        _reject_ring:A ring buffer of (ts, reason) for recent rejects.
        _first_enqueued_at: Wall-clock ts of first item for age calculations.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - No background thread here; thread safety is limited to queue ops and
    #   metric increments. Aggregator performs the actual persistence.
    # - Keep normalization decisions *deterministic* (e.g., JSON separators, lower-hex).

    def __init__(self, config: LogProducerConfig) -> None:
        """
        Initialize a producer with a concrete policy & schema.

        Args:
            config: LogProducerConfig with schema, validation toggles, drop policy,
                    JSON handling, normalization, and audit ring size.

        Side effects:
            - Prepares dtype→coercer mapping for fast per-field checks.
            - Allocates bounded queue and initializes metrics/audit ring.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - _checkers maps pl dtypes (Utf8/Int64/Int32/Float64/Float32/Boolean) to
        #   small coercers for hot-path validation.

        self._cfg = config
        self._schema: EventSchema = config.schema
        self._q: "queue.Queue[LogEvent]" = queue.Queue(maxsize=config.max_queue_size)
        self._metrics = ProducerMetrics()
        self._metrics_lock = threading.Lock()
        self._reject_ring: list[tuple[float, str]] = []
        self._audit_rejects = config.audit_rejects
        self._drop_policy = config.drop_policy
        self._first_enqueued_at: Optional[float] = None

        # Compile Python-type → checker/coercer map (schema fields are Python types)
        # NOTE: list columns are handled dynamically via _coercer_for(...).
        self._scalar_checkers = {
            str: self._coerce_str,
            int: self._coerce_int,
            float: self._coerce_float,
            bool: self._coerce_bool,
            bytes: self._coerce_bytes,  # new in v0.1.4: allow explicit bytes columns in custom addons
        }


    @property
    def buffer(self) -> "queue.Queue[LogEvent]":
        """
        Access the underlying bounded queue (read-only in practice).

        Returns:
            The `queue.Queue[LogEvent]` instance used for downstream draining.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Exposed for Aggregator sizing/inspection; do not mutate externally.

        return self._q

    @property
    def metrics(self) -> ProducerMetrics:
        """
        Access live ingestion counters.

        Returns:
            ProducerMetrics updated under a small lock in hot paths.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Read access is unsynchronized; values are approximate but sufficient.

        return self._metrics

    def queue_size(self) -> int:
        """
        Current number of items in the queue.

        Returns:
            Integer depth of the bounded buffer.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Used by Aggregator to compute near-full triggers.

        return self._q.qsize()

    def oldest_age_seconds(self) -> Optional[float]:
        """
        Age (seconds) of the oldest queued item, if any.

        Returns:
            Seconds since the first enqueue, or None if the queue is empty.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Drives age-based flush triggers in the Aggregator’s poller.

        if self._first_enqueued_at is None or self._q.qsize() == 0:
            return None
        return time.time() - self._first_enqueued_at

    def recent_rejections(self) -> list[tuple[float, str]]:
        """
        Return the recent rejections audit ring.

        Returns:
            List of (unix_ts_seconds, reason) tuples, oldest first.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Size is bounded by config.audit_rejects; used for diagnostics.

        return list(self._reject_ring)

    def ingest(self, event: Mapping[str, Any], *, timeout: Optional[float] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate/normalize a single event and enqueue it subject to drop_policy.

        Overview (v0.1.2 role):
            This is the hot path from the API/Logger into storage. On success it
            increments `accepted` and returns (True, None). On failure it records
            the rejection reason and returns (False, reason).

        Args:
            event:   Mapping of incoming keys/values (will be copied & mutated).
            timeout: Only used when drop_policy='block' (seconds to wait for space).

        Returns:
            (ok, reason). `reason` is None on success, or a short string tag.

        Common reasons:
            'missing_required', 'type_mismatch:<col>:<dtype>',
            'json_field_invalid', 'service_name_empty', 'bad_trace_id', 'bad_span_id',
            'date_field_invalid', 'date_mismatch:<val>!=<utc_date>',
            'queue_full_drop_new' (for drop_new under pressure)
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - We stamp `_first_enqueued_at` when queue transitions from 0→>0.
        # - drop_old evicts one oldest element to make room when full.

        ok, reason, normalized = self._validate_and_normalize(dict(event))
        if not ok:
            self._count_reject(reason)
            self._audit_reject(reason)
            return False, reason

        try:
            if self._drop_policy == "block":
                if self._q.qsize() == 0:
                    self._first_enqueued_at = self._first_enqueued_at or time.time()
                self._q.put(normalized, timeout=timeout)
            elif self._drop_policy == "drop_new":
                if self._q.full():
                    self._inc("dropped_capacity")
                    return False, "queue_full_drop_new"
                if self._q.qsize() == 0:
                    self._first_enqueued_at = self._first_enqueued_at or time.time()
                self._q.put_nowait(normalized)
            elif self._drop_policy == "drop_old":
                if self._q.full():
                    try:
                        self._q.get_nowait()
                    except queue.Empty:
                        pass
                if self._q.qsize() == 0:
                    self._first_enqueued_at = self._first_enqueued_at or time.time()
                self._q.put_nowait(normalized)
            else:
                raise ValueError("unknown drop_policy")
        except queue.Full:
            self._inc("dropped_capacity")
            return False, "queue_full_drop_new"

        self._inc("accepted")
        return True, None

    def drain(self, max_items: Optional[int] = None) -> List[LogEvent]:
        """
        Pop up to `max_items` from the queue without blocking.

        Args:
            max_items: Maximum items to remove; if None, uses current qsize().

        Returns:
            A (possibly empty) list of LogEvent dicts.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Resets `_first_enqueued_at` when the queue becomes empty.

        out: List[LogEvent] = []
        n = self._q.qsize() if max_items is None else max_items
        for _ in range(n):
            try:
                out.append(self._q.get_nowait())
            except queue.Empty:
                break
        if self._q.qsize() == 0:
            self._first_enqueued_at = None
        return out

    def clear(self) -> None:
        """
        Remove all items from the queue (best-effort) and reset age tracking.

        Returns:
            None
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Used during shutdown or test resets; ignores queue.Empty races.

        while True:
            try:
                self._q.get_nowait()
            except queue.Empty:
                break
        self._first_enqueued_at = None

    def _inc(self, field: str) -> None:
        """
        Atomically increment a single ProducerMetrics counter.

        Args:
            field: Name of the counter on ProducerMetrics to increment.

        Returns:
            None
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Small critical section to avoid torn increments across threads.

        with self._metrics_lock:
            setattr(self._metrics, field, getattr(self._metrics, field) + 1)

    def _audit_reject(self, reason: str) -> None:
        """
        Append a rejection reason to the audit ring with a timestamp.

        Args:
            reason: Short string tag describing the failure.

        Returns:
            None
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Bound the ring to `audit_rejects`; drop oldest when full.

        if self._audit_rejects <= 0:
            return
        self._reject_ring.append((time.time(), reason))
        if len(self._reject_ring) > self._audit_rejects:
            self._reject_ring.pop(0)

    def _count_reject(self, reason: Optional[str]) -> None:
        """
        Increment the appropriate rejection counter based on reason.

        Args:
            reason: The string tag returned by validation/normalization.

        Returns:
            None
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Buckets: json_field_invalid → rejected_payload_json;
        #            date_mismatch*     → rejected_date_mismatch;
        #            else               → rejected_schema.

        if reason == "json_field_invalid":
            with self._metrics_lock:
                self._metrics.rejected_payload_json += 1
        elif reason and reason.startswith("date_mismatch"):
            with self._metrics_lock:
                self._metrics.rejected_date_mismatch += 1
        else:
            with self._metrics_lock:
                self._metrics.rejected_schema += 1

    def _validate_and_normalize(self, d: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any] | None]:
        """
        Core pipeline: transform `d` into a schema-conformant row.

        Steps (in order):
            1) Defaults: fill from EventSchema.defaults (includes schema_version).
            1.5) OTLP timestamp fallback: if time_unix_nano exists in schema but
                is missing/zero, choose a best candidate (observed/start) or
                arrival time (ns).
            2) Computed fields: EventSchema.computed[k](row) → row[k].
            3) Extra policy: error | strip | keep unexpected keys.
            4) Required check: ensure presence of EventSchema.required.
            5) JSON fields: serialize to compact JSON (and optional round-trip verify).
            6) Type coercion: use dtype→coercer map (Utf8/Int/Float/Bool).
            6.5) Normalization:
                • service_name: default/require per config.normalize_service_name
                • trace_id/span_id: lower-hex; optionally enforce 32/16 lengths
            7) Date coherence: if schema.enforce_date_from_ts=(ts_ms_field,date_field),
            ensure date_field matches UTC day derived from ts_ms_field.

        Args:
            d: Mutable dict copy of the incoming event.

        Returns:
            (True, None, normalized_row) on success;
            (False, reason, None) on validation failure.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Keep reason tags short & stable; API surfaces them in partialSuccess.
        # - Avoid float math in time conversions; operate on ints only.

        s = self._schema
        cfg = self._cfg
        fields = s.fields

        for k, v in s.defaults.items():
            d.setdefault(k, v)

        if "time_unix_nano" in fields:
            def _as_int_ns(x) -> int:
                try: return int(x or 0)
                except Exception: return 0
            tns = _as_int_ns(d.get("time_unix_nano"))
            if tns <= 0:
                candidates = []
                if "observed_time_unix_nano" in fields:
                    candidates.append(_as_int_ns(d.get("observed_time_unix_nano")))
                if "start_time_unix_nano" in fields:
                    candidates.append(_as_int_ns(d.get("start_time_unix_nano")))
                tns = next((c for c in candidates if c > 0), 0)
                if tns <= 0:
                    tns = int(time.time() * 1_000_000_000)
                d["time_unix_nano"] = tns

        for k, fn in s.computed.items():
            try:
                d[k] = fn(d)
            except Exception as e:
                return False, f"computed_field_error:{k}", None

        if cfg.enforce_extra_policy:
            extras = set(d.keys()) - set(fields.keys())
            if extras:
                if s.extra_policy == "error":
                    return False, f"extra_fields:{sorted(extras)}", None
                elif s.extra_policy == "strip":
                    for k in extras:
                        d.pop(k, None)
        
        if cfg.validate_required:
            missing = set(s.required) - set(d.keys())
            if missing:
                return False, f"missing_required:{sorted(missing)}", None

        if cfg.serialize_json_fields and s.json_fields:
            for jf in s.json_fields:
                if jf in d and not isinstance(d[jf], str):
                    try:
                        d[jf] = json.dumps(d[jf], separators=(",", ":"))
                    except Exception:
                        return False, "json_field_invalid", None

        if cfg.validate_json_fields and s.json_fields:
            for jf in s.json_fields:
                if jf in d and isinstance(d[jf], str):
                    try:
                        json.loads(d[jf])
                    except Exception:
                        return False, "json_field_invalid", None

        if cfg.validate_types:
            for k, dtype in fields.items():
                if k not in d:
                    continue
                coerce = self._coercer_for(dtype)
                if coerce is None:
                    continue
                ok, val = coerce(d[k], s.autocoerce)
                if not ok:
                    return False, f"type_mismatch:{k}:{dtype}", None
                d[k] = val


        if "service_name" in fields:
            sv = d.get("service_name")
            if cfg.normalize_service_name:
                if sv is None or (isinstance(sv, str) and sv.strip() == ""):
                    d["service_name"] = cfg.default_service_name
            else:
                if sv is None or (isinstance(sv, str) and sv.strip() == ""):
                    return False, "service_name_empty", None

        if "trace_id" in fields and "trace_id" in d and d.get("trace_id"):
            ok, norm = self._normalize_hex_id(d["trace_id"], 32 if cfg.enforce_otlp_id_lengths else None)
            if not ok:
                return False, "bad_trace_id", None
            d["trace_id"] = norm
        if "span_id" in fields and "span_id" in d and d.get("span_id"):
            ok, norm = self._normalize_hex_id(d["span_id"], 16 if cfg.enforce_otlp_id_lengths else None)
            if not ok:
                return False, "bad_span_id", None
            d["span_id"] = norm

        if cfg.validate_date_coherence and s.enforce_date_from_ts:
            ts_field, date_field = s.enforce_date_from_ts
            if ts_field in d:
                ts = d[ts_field]
                if not isinstance(ts, int):
                    return False, "date_check_requires_int_ts", None
                import datetime as _dt
                utc_date = _dt.datetime.fromtimestamp(ts / 1000, tz=_dt.UTC).strftime("%Y-%m-%d")
                val = d.get(date_field)
                if val is None or not isinstance(val, str) or not DATE_RE.match(val):
                    if s.autocoerce:
                        d[date_field] = utc_date
                    else:
                        return False, "date_field_invalid", None
                elif val != utc_date:
                    if s.autocoerce:
                        d[date_field] = utc_date
                    else:
                        return False, f"date_mismatch:{val}!={utc_date}", None

        return True, None, d

    @staticmethod
    def _normalize_hex_id(v: Any, required_len: Optional[int]) -> Tuple[bool, Optional[str]]:
        """
        Normalize a hex identifier: strip spaces, lowercase, and optionally
        enforce exact length.

        Args:
            v:           Candidate value (usually string).
            required_len:Exact length to enforce (e.g., 32 for trace_id), or None.

        Returns:
            (True, normalized_hex) or (False, None).
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Accepts only [0-9a-fA-F]; rejects if non-hex or wrong length (when enforced).

        try:
            s = str(v).strip().lower()
        except Exception:
            return False, None
        if required_len is not None and len(s) != required_len:
            return False, None
        for ch in s:
            o = ord(ch)
            is_hex = (48 <= o <= 57) or (97 <= o <= 102)
            if not is_hex:
                return False, None
        return True, s

    @staticmethod
    def _coerce_str(v: Any, autocoerce: bool) -> Tuple[bool, Any]:
        """
        Ensure a Utf8/str value.

        Args:
            v:          Input value.
            autocoerce: If True, use `str(v)` for non-string inputs.

        Returns:
            (ok, value) where ok=False if coercion is disallowed or fails.
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - None is not auto-coerced to "None"; stays invalid when required.

        if isinstance(v, str): return True, v
        if autocoerce: return True, str(v)
        return False, v

    @staticmethod
    def _coerce_int(v: Any, autocoerce: bool) -> Tuple[bool, Any]:
        """
        Ensure an Int32/Int64 value (avoids bool→int confusion).

        Args:
            v:          Input value.
            autocoerce: If True, attempt `int(v)`.

        Returns:
            (ok, value).
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Treat bool specially: either reject (autocoerce=False) or int(bool) when True.

        if isinstance(v, bool):
            return (False, v) if not autocoerce else (True, int(v))
        if isinstance(v, int): return True, v
        if autocoerce:
            try: return True, int(v)
            except Exception: return False, v
        return False, v

    @staticmethod
    def _coerce_float(v: Any, autocoerce: bool) -> Tuple[bool, Any]:
        """
        Ensure a Float32/Float64 value.

        Args:
            v:          Input value.
            autocoerce: If True, attempt `float(v)`.

        Returns:
            (ok, value).
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - Avoid float("nan") traps in later logic; acceptance here is purely type-level.

        if isinstance(v, float): return True, v
        if isinstance(v, int): return True, float(v)
        if autocoerce:
            try: return True, float(v)
            except Exception: return False, v
        return False, v

    @staticmethod
    def _coerce_bool(v: Any, autocoerce: bool) -> Tuple[bool, Any]:
        """
        Ensure a Boolean value.

        Args:
            v:          Input value.
            autocoerce: If True, coerce using common truthy strings and non-zero numbers.

        Returns:
            (ok, value).
        """
        # --- DEVELOPER NOTES -------------------------------------------------
        # - String truthiness: {"1","true","yes","on"} → True; case-insensitive.

        if isinstance(v, bool): return True, v
        if autocoerce:
            if isinstance(v, (int, float)): return True, bool(v)
            if isinstance(v, str): return True, v.lower() in {"1","true","yes","on"}
        return False, v

    @staticmethod
    def _coerce_bytes(v: Any, autocoerce: bool) -> Tuple[bool, Any]:
        """
        Ensure a bytes value.

        Behavior:
            - bytes/bytearray → bytes(v)
            - when autocoerce=True and v is str → v.encode('utf-8')
        """
        if isinstance(v, (bytes, bytearray)):
            return True, bytes(v)
        if autocoerce and isinstance(v, str):
            try:
                return True, v.encode("utf-8")
            except Exception:
                return False, v
        return False, v

    @staticmethod
    def _coerce_list_value(
        v: Any,
        autocoerce: bool,
        elem_coercer: "Callable[[Any, bool], Tuple[bool, Any]]",
    ) -> Tuple[bool, Any]:
        """
        Ensure a list-of-scalar value, coercing each element with elem_coercer.

        Rules:
          - list → elementwise coerce
          - when autocoerce=True and v is a JSON-encoded string of a list → json.loads then elementwise coerce
          - None is accepted as [] only when autocoerce=True
        """
        if v is None:
            return (True, []) if autocoerce else (False, v)

        seq = None
        if isinstance(v, list):
            seq = v
        elif autocoerce and isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    seq = parsed
            except Exception:
                seq = None

        if seq is None:
            return False, v

        out = []
        for item in seq:
            ok, coerced = elem_coercer(item, autocoerce)
            if not ok:
                return False, v
            out.append(coerced)
        return True, out

    def _coercer_for(self, dtype_spec: object):
        """
        Return a (value, autocoerce)->(ok, coerced) function for a given schema field spec.

        Supports:
          - python scalars: {str,int,float,bool,bytes}
          - list specs encoded as ('list', <scalar_pytype>)
        """
        # Scalar?
        fn = self._scalar_checkers.get(dtype_spec)
        if fn is not None:
            return fn

        # List-of-<scalar>?
        if isinstance(dtype_spec, tuple) and len(dtype_spec) == 2 and dtype_spec[0] == "list":
            inner = dtype_spec[1]
            inner_fn = self._coercer_for(inner)
            if inner_fn is None:
                return None
            return lambda v, autocoerce: self._coerce_list_value(v, autocoerce, inner_fn)

        # Unknown/complex type → no checker (Producer skips)
        return None
