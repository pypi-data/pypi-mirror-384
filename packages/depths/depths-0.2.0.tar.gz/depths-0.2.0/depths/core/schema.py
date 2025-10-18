
"""
Typed schemas and additive deltas for OTel tables.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping, Set, Tuple, Literal, Optional
import datetime as _dt
import polars as pl

_PY_SCALARS = (str, int, float, bool, bytes)

def _is_scalar_pytype(t: type) -> bool:
    return t in _PY_SCALARS

def _is_list_spec(spec: object) -> bool:
    return (
        isinstance(spec, tuple)
        and len(spec) == 2
        and spec[0] == "list"
        and _is_scalar_pytype(spec[1])
    )

_PL_TO_PY = {
    pl.Utf8: str,
    pl.Int64: int,
    pl.Int32: int,
    pl.Float64: float,
    pl.Float32: float,
    pl.Boolean: bool,
    pl.Binary: bytes,
}

def _as_py_dtype(x: object) -> object:
    """Normalize dtype to Python schema form (scalar or ('list', scalar))."""
    if _is_list_spec(x):
        return x
    if _is_scalar_pytype(x):
        return x
    if x in _PL_TO_PY:
        return _PL_TO_PY[x]
    if isinstance(x, pl.datatypes.List):
        inner = getattr(x, "inner", None)
        if inner in _PL_TO_PY:
            return ("list", _PL_TO_PY[inner])
    raise TypeError(f"Unsupported dtype in schema: {x!r}")

def _py_to_pl_dtype(x: object) -> pl.DataType:
    """Convert Python schema dtype to a Polars dtype."""
    if _is_scalar_pytype(x):
        return {str: pl.Utf8, int: pl.Int64, float: pl.Float64, bool: pl.Boolean, bytes: pl.Binary}[x]  # type: ignore[index]
    if _is_list_spec(x):
        inner_py = x[1]  # type: ignore[index]
        return pl.List(_py_to_pl_dtype(inner_py))
    if x in _PL_TO_PY:
        return x  # type: ignore[return-value]
    raise TypeError(f"Cannot convert to Polars dtype: {x!r}")

def _py_to_delta_type(x: object) -> str:
    """Convert Python schema dtype to a Delta type string."""
    if _is_scalar_pytype(x):
        return {str: "STRING", int: "BIGINT", float: "DOUBLE", bool: "BOOLEAN", bytes: "BINARY"}[x]  # type: ignore[index]
    if _is_list_spec(x):
        return f"ARRAY<{_py_to_delta_type(x[1])}>"  # type: ignore[index]
    raise TypeError(f"Cannot convert to Delta type: {x!r}")

@dataclass(frozen=True)
class EventSchema:
    """
    Declarative contract for a concrete table.
    """

    fields: Dict[str, object]
    required: Set[str] = field(default_factory=set)
    defaults: Dict[str, Any] = field(default_factory=dict)
    computed: Dict[str, Callable[[Mapping[str, Any]], Any]] = field(default_factory=dict)
    extra_policy: Literal["error", "strip", "keep"] = "strip"
    autocoerce: bool = True
    json_fields: Set[str] = field(default_factory=set)
    enforce_date_from_ts: Tuple[str, str] | None = None
    schema_version: int = 1

    def polars_schema(self) -> Dict[str, pl.DataType]:
        """Return a Polars dtype mapping suitable for DataFrames."""
        return {name: _py_to_pl_dtype(dtype) for name, dtype in self.fields.items()}

    def delta_schema_strings(self) -> Dict[str, str]:
        """Return Delta type strings for table creation paths."""
        return {name: _py_to_delta_type(dtype) for name, dtype in self.fields.items()}

@dataclass
class SchemaDelta:
    """
    Additive patch to extend an EventSchema.
    """

    fields: Dict[str, object]
    required: Set[str] = field(default_factory=set)
    defaults: Dict[str, Any] = field(default_factory=dict)
    json_fields: Set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        norm: Dict[str, object] = {}
        for name, spec in self.fields.items():
            py = _as_py_dtype(spec)
            if _is_scalar_pytype(py) or _is_list_spec(py):
                norm[name] = py
            else:
                raise TypeError(f"SchemaDelta field '{name}' has unsupported dtype: {spec!r}")
        self.fields = norm  # type: ignore[assignment]

def _ns_to_ms(ns: int) -> int:
    """Convert nanoseconds since epoch to milliseconds."""
    return int(ns // 1_000_000)

def _ms_to_date(ms: int) -> str:
    """Convert epoch milliseconds to UTC date string YYYY-MM-DD."""
    return _dt.datetime.fromtimestamp(ms / 1000, tz=_dt.timezone.utc).strftime("%Y-%m-%d")

def compose_schema(base: EventSchema, delta: SchemaDelta) -> EventSchema:
    """Return a new EventSchema with the delta applied."""
    return EventSchema(
        fields={**base.fields, **delta.fields},
        required=set(base.required) | set(delta.required),
        defaults={**base.defaults, **delta.defaults},
        computed={**base.computed},
        extra_policy=base.extra_policy,
        autocoerce=base.autocoerce,
        json_fields=set(base.json_fields) | set(delta.json_fields),
        enforce_date_from_ts=base.enforce_date_from_ts,
        schema_version=base.schema_version,
    )

_ALL_TABLE_KEYS: Tuple[str, ...] = (
    "spans", "span_events", "span_links", "logs", "metrics_points", "metrics_hist"
)

def apply_addons(
    schemas: Dict[str, EventSchema],
    addons_map: Optional[Dict[str, list[SchemaDelta]]],
) -> Dict[str, EventSchema]:
    """Compose selected deltas onto the provided base schemas."""
    out = dict(schemas)
    if not addons_map:
        return out
    for table_key, deltas in addons_map.items():
        if table_key not in out:
            continue
        es = out[table_key]
        seen = set(es.fields.keys())
        for d in (deltas or []):
            dupes = [c for c in d.fields.keys() if c in seen]
            if dupes:
                raise ValueError(f"SchemaDelta redefines existing column(s) for '{table_key}': {dupes}")
            es = compose_schema(es, d)
            seen |= set(d.fields.keys())
        out[table_key] = es
    return out

RESOURCE_SCOPE_BASE: Dict[str, object] = {
    "project_id": str,
    "schema_version": int,
    "service_name": str,
    "service_namespace": str,
    "service_instance_id": str,
    "service_version": str,
    "deployment_env": str,
    "resource_attrs_json": str,
    "scope_name": str,
    "scope_version": str,
    "scope_attrs_json": str,
    "event_ts": int,
    "event_date": str,
}

SPAN_SCHEMA = EventSchema(
    fields={
        **RESOURCE_SCOPE_BASE,
        "trace_id": str,
        "span_id": str,
        "parent_span_id": str,
        "name": str,
        "kind": str,
        "start_time_unix_nano": int,
        "end_time_unix_nano": int,
        "duration_ms": float,
        "status_code": str,
        "status_message": str,
        "dropped_events_count": int,
        "dropped_links_count": int,
        "span_attrs_json": str,
        "session_id": str,
        "session_previous_id": str,
        "user_id": str,
        "user_name": str,
        "user_roles_json": str,
    },
    required={
        "project_id","schema_version","trace_id","span_id","name",
        "start_time_unix_nano","end_time_unix_nano","event_ts","event_date",
    },
    defaults={
        "schema_version": 1,
        "dropped_events_count": 0, "dropped_links_count": 0,
        "service_name": "unknown",
        "service_namespace":"", "service_instance_id":"", "service_version":"", "deployment_env":"",
        "scope_name":"", "scope_version":"", "resource_attrs_json":"{}", "scope_attrs_json":"{}",
        "status_code":"UNSET", "status_message":"", "kind":"INTERNAL",
        "parent_span_id":"", "span_attrs_json":"{}",
        "session_id": "",
        "session_previous_id": "",
        "user_id": "",
        "user_name": "",
        "user_roles_json": "[]",
    },
    computed={
        "event_ts": lambda d: _ns_to_ms(int(d.get("start_time_unix_nano", 0))),
        "event_date": lambda d: _ms_to_date(_ns_to_ms(int(d.get("start_time_unix_nano", 0)))),
        "duration_ms": lambda d: max(0.0, (int(d.get("end_time_unix_nano", 0)) - int(d.get("start_time_unix_nano", 0))) / 1_000_000.0),
    },
    json_fields={"resource_attrs_json","scope_attrs_json","span_attrs_json"},
    enforce_date_from_ts=("event_ts", "event_date"),
    schema_version=1,
)

SPAN_EVENT_SCHEMA = EventSchema(
    fields={
        **RESOURCE_SCOPE_BASE,
        "trace_id": str,
        "span_id": str,
        "time_unix_nano": int,
        "name": str,
        "event_attrs_json": str,
        "session_id": str,
        "session_previous_id": str,
        "user_id": str,
        "user_name": str,
        "user_roles_json": str,
    },
    required={"project_id","schema_version","trace_id","span_id","time_unix_nano","event_ts","event_date"},
    defaults={
        "schema_version": 1,
        "name":"", "event_attrs_json":"{}",
        "service_name": "unknown",
        "service_namespace":"", "service_instance_id":"", "service_version":"", "deployment_env":"",
        "scope_name":"", "scope_version":"", "resource_attrs_json":"{}", "scope_attrs_json":"{}",
        "session_id": "",
        "session_previous_id": "",
        "user_id": "",
        "user_name": "",
        "user_roles_json": "[]",
    },
    computed={
        "event_ts": lambda d: _ns_to_ms(int(d.get("time_unix_nano", 0))),
        "event_date": lambda d: _ms_to_date(_ns_to_ms(int(d.get("time_unix_nano", 0)))),
    },
    json_fields={"resource_attrs_json","scope_attrs_json","event_attrs_json"},
    enforce_date_from_ts=("event_ts", "event_date"),
    schema_version=1,
)

SPAN_LINK_SCHEMA = EventSchema(
    fields={
        **RESOURCE_SCOPE_BASE,
        "trace_id": str,
        "span_id": str,
        "linked_trace_id": str,
        "linked_span_id": str,
        "link_attrs_json": str,
        "session_id": str,
        "session_previous_id": str,
        "user_id": str,
        "user_name": str,
        "user_roles_json": str,
    },
    required={"project_id","schema_version","trace_id","span_id","linked_trace_id","linked_span_id","event_ts","event_date"},
    defaults={
        "schema_version": 1,
        "link_attrs_json":"{}",
        "service_name": "unknown",
        "service_namespace":"", "service_instance_id":"", "service_version":"", "deployment_env":"",
        "scope_name":"", "scope_version":"", "resource_attrs_json":"{}", "scope_attrs_json":"{}",
        "session_id": "",
        "session_previous_id": "",
        "user_id": "",
        "user_name": "",
        "user_roles_json": "[]",
    },
    computed={},
    json_fields={"resource_attrs_json","scope_attrs_json","link_attrs_json"},
    enforce_date_from_ts=("event_ts", "event_date"),
    schema_version=1,
)

LOG_SCHEMA = EventSchema(
    fields={
        **RESOURCE_SCOPE_BASE,
        "time_unix_nano": int,
        "observed_time_unix_nano": int,
        "severity_text": str,
        "severity_number": int,
        "body": str,
        "log_attrs_json": str,
        "trace_id": str,
        "span_id": str,
        "session_id": str,
        "session_previous_id": str,
        "user_id": str,
        "user_name": str,
        "user_roles_json": str,
    },
    required={"project_id","schema_version","event_ts","event_date"},
    defaults={
        "schema_version": 1,
        "observed_time_unix_nano": 0, "severity_text":"", "severity_number":0,
        "service_name": "unknown",
        "service_namespace":"", "service_instance_id":"", "service_version":"", "deployment_env":"",
        "scope_name":"", "scope_version":"", "resource_attrs_json":"{}", "scope_attrs_json":"{}",
        "log_attrs_json":"{}", "trace_id":"", "span_id":"",
        "session_id": "",
        "session_previous_id": "",
        "user_id": "",
        "user_name": "",
        "user_roles_json": "[]",
    },
    computed={
        "event_ts": lambda d: _ns_to_ms(int(d.get("time_unix_nano", 0))),
        "event_date": lambda d: _ms_to_date(_ns_to_ms(int(d.get("time_unix_nano", 0)))),
    },
    json_fields={"resource_attrs_json","scope_attrs_json","log_attrs_json"},
    enforce_date_from_ts=("event_ts", "event_date"),
    schema_version=1,
)

METRIC_POINT_SCHEMA = EventSchema(
    fields={
        **RESOURCE_SCOPE_BASE,
        "instrument_name": str,
        "instrument_type": str,
        "unit": str,
        "aggregation_temporality": str,
        "is_monotonic": bool,
        "time_unix_nano": int,
        "start_time_unix_nano": int,
        "value": float,
        "point_attrs_json": str,
        "exemplars_json": str,
        "session_id": str,
        "session_previous_id": str,
        "user_id": str,
        "user_name": str,
        "user_roles_json": str,
    },
    required={"project_id","schema_version","instrument_name","instrument_type","time_unix_nano","value","event_ts","event_date"},
    defaults={
        "schema_version": 1,
        "unit":"", "aggregation_temporality":"UNSPECIFIED", "is_monotonic": False,
        "start_time_unix_nano": 0, "point_attrs_json":"{}", "exemplars_json":"[]",
        "service_name": "unknown",
        "service_namespace":"", "service_instance_id":"", "service_version":"", "deployment_env":"",
        "scope_name":"", "scope_version":"", "resource_attrs_json":"{}", "scope_attrs_json": "{}",
        "session_id": "",
        "session_previous_id": "",
        "user_id": "",
        "user_name": "",
        "user_roles_json": "[]",
    },
    computed={
        "event_ts": lambda d: _ns_to_ms(int(d.get("time_unix_nano", 0))),
        "event_date": lambda d: _ms_to_date(_ns_to_ms(int(d.get("time_unix_nano", 0)))),
    },
    json_fields={"resource_attrs_json","scope_attrs_json","point_attrs_json","exemplars_json"},
    enforce_date_from_ts=("event_ts","event_date"),
    schema_version=1,
)

METRIC_HIST_SCHEMA = EventSchema(
    fields={
        **RESOURCE_SCOPE_BASE,
        "instrument_name": str,
        "instrument_type": str,
        "unit": str,
        "aggregation_temporality": str,
        "time_unix_nano": int,
        "start_time_unix_nano": int,
        "count": int,
        "sum": float,
        "min": float,
        "max": float,
        "bounds_json": str,
        "counts_json": str,
        "exp_zero_count": int,
        "exp_scale": int,
        "exp_positive_json": str,
        "exp_negative_json": str,
        "quantiles_json": str,
        "point_attrs_json": str,
        "exemplars_json": str,
        "session_id": str,
        "session_previous_id": str,
        "user_id": str,
        "user_name": str,
        "user_roles_json": str,
    },
    required={"project_id","schema_version","instrument_name","instrument_type","time_unix_nano","count","event_ts","event_date"},
    defaults={
        "schema_version": 1,
        "unit":"", "aggregation_temporality":"UNSPECIFIED",
        "start_time_unix_nano": 0, "sum": 0.0, "min": 0.0, "max": 0.0,
        "bounds_json":"[]", "counts_json":"[]",
        "exp_zero_count":0, "exp_scale":0,
        "exp_positive_json":"{}", "exp_negative_json":"{}",
        "quantiles_json":"[]", "point_attrs_json":"{}", "exemplars_json":"[]",
        "service_name": "unknown",
        "service_namespace":"", "service_instance_id":"", "service_version":"", "deployment_env":"",
        "scope_name":"", "scope_version":"", "resource_attrs_json":"{}", "scope_attrs_json":"{}",
        "session_id": "",
        "session_previous_id": "",
        "user_id": "",
        "user_name": "",
        "user_roles_json": "[]",
    },
    computed={
        "event_ts": lambda d: _ns_to_ms(int(d.get("time_unix_nano", 0))),
        "event_date": lambda d: _ms_to_date(_ns_to_ms(int(d.get("time_unix_nano", 0)))),
    },
    json_fields={
        "resource_attrs_json","scope_attrs_json","bounds_json","counts_json",
        "exp_positive_json","exp_negative_json","quantiles_json","point_attrs_json","exemplars_json"
    },
    enforce_date_from_ts=("event_ts","event_date"),
    schema_version=1,
)
