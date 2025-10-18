"""
Lean OTLP → Depths row mappers.

This module translates decoded OTLP payloads (traces/logs/metrics) into
row dicts shaped for the six Depths OTel tables. Attribute handling is
schema-driven and uniform:

- Resource, scope and event attributes are converted from dot namespaces
  to snake_case by swapping "." → "_" only.
- If a snake_case key exists in the effective EventSchema for the target
  table, it is promoted into that top‑level column.
- All remaining attributes are kept in the appropriate "*_attrs_json"
  field as a Python dict (Producer serializes to JSON).

Built‑in and user‑defined SchemaDelta objects are treated identically;
the mapper composes them with the base table schemas using `apply_addons`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Optional, Mapping
import json
import datetime as _dt

from depths.core.schema import (
    EventSchema,
    SchemaDelta,
    apply_addons,
    SPAN_SCHEMA,
    SPAN_EVENT_SCHEMA,
    SPAN_LINK_SCHEMA,
    LOG_SCHEMA,
    METRIC_POINT_SCHEMA,
    METRIC_HIST_SCHEMA,
)


def _ns_to_ms(ns: int) -> int:
    """Convert nanoseconds since UNIX epoch to milliseconds."""
    return int(ns // 1_000_000)


def _ms_to_date(ms: int) -> str:
    """Convert epoch milliseconds to a UTC date string (YYYY-MM-DD)."""
    return _dt.datetime.fromtimestamp(ms / 1000, tz=_dt.timezone.utc).strftime("%Y-%m-%d")


def _any_value_to_py(v: Dict[str, Any]) -> Any:
    """Convert an OTLP AnyValue into a natural Python value."""
    if v is None:
        return None
    if "stringValue" in v:
        return v["stringValue"]
    if "boolValue" in v:
        return bool(v["boolValue"])
    if "intValue" in v:
        return int(v["intValue"])
    if "doubleValue" in v:
        return float(v["doubleValue"])
    if "bytesValue" in v:
        return v["bytesValue"]
    if "arrayValue" in v:
        arr = v["arrayValue"].get("values", []) or []
        return [_any_value_to_py(x) for x in arr]
    if "kvlistValue" in v:
        kvs = v["kvlistValue"].get("values", []) or []
        out: Dict[str, Any] = {}
        for it in kvs:
            out[it.get("key", "")] = _any_value_to_py(it.get("value"))
        return out
    return v


def _attributes_to_dict(attrs: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Convert an OTLP KeyValue list to a plain dict."""
    out: Dict[str, Any] = {}
    if not attrs:
        return out
    for kv in attrs:
        k = kv.get("key", "")
        if not k:
            continue
        v = _any_value_to_py(kv.get("value"))
        out[k] = v
    return out


def _stringify_body(body: Dict[str, Any]) -> str:
    """Convert LogRecord.body (AnyValue) to a deterministic string."""
    py = _any_value_to_py(body) if body is not None else ""
    if isinstance(py, str):
        return py
    try:
        return json.dumps(py, separators=(",", ":"))
    except Exception:
        return str(py)


def _lower_hex_or_empty(s: Optional[str]) -> str:
    """Normalize a hex identifier to lowercase; empty if missing."""
    return (s or "").strip().lower()


def _snake_from_attr_key(k: str) -> str:
    """Convert a dot-namespaced attribute key to snake_case using '_' for dots."""
    return k.replace(".", "_")


def _promote_attrs_to_row(attrs: Mapping[str, Any], schema: EventSchema, row: Dict[str, Any]) -> Dict[str, Any]:
    """Promote attribute keys into top-level columns when present in schema; return unmatched attrs."""
    unmatched: Dict[str, Any] = {}
    field_names = set(schema.fields.keys())
    for k, v in (attrs or {}).items():
        sk = _snake_from_attr_key(k)
        if sk in field_names:
            row[sk] = v
        else:
            unmatched[k] = v
    return unmatched


class OTLPMapper:
    """
    Stateless mapper from decoded OTLP JSON to Depths row dicts.

    The mapper promotes resource, scope, and event attributes into
    first-class columns when the snake_case field exists in the effective
    EventSchema for the destination table. Remaining attributes are kept
    under the corresponding '*_attrs_json' field as Python dicts.
    """

    def __init__(
        self,
        *,
        default_project_id: str = "default",
        default_service_name: str = "unknown",
        add_session_context: bool = False,
        add_user_context: bool = False,
        addons_map: Optional[Dict[str, List[SchemaDelta]]] = None,
    ) -> None:
        """Initialize mapper defaults and effective schemas."""
        self.default_project_id = default_project_id
        self.default_service_name = default_service_name
        self.add_session_context = bool(add_session_context)
        self.add_user_context = bool(add_user_context)

        base = {
            "spans": SPAN_SCHEMA,
            "span_events": SPAN_EVENT_SCHEMA,
            "span_links": SPAN_LINK_SCHEMA,
            "logs": LOG_SCHEMA,
            "metrics_points": METRIC_POINT_SCHEMA,
            "metrics_hist": METRIC_HIST_SCHEMA,
        }
        self._schemas: Dict[str, EventSchema] = apply_addons(base, addons_map or {})

    def _extract_identity(
        self,
        event_attrs: Optional[Dict[str, Any]],
        resource_attrs: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build optional identity fields from event and resource attributes."""
        if not (self.add_session_context or self.add_user_context):
            return {}

        ea = event_attrs or {}
        ra = resource_attrs or {}
        out: Dict[str, Any] = {}

        if self.add_session_context:
            sid = ea.get("session.id", ra.get("session.id", "")) or ""
            spid = ea.get("session.previous_id", ra.get("session.previous_id", "")) or ""
            out["session_id"] = str(sid)
            out["session_previous_id"] = str(spid)

        if self.add_user_context:
            uid = ea.get("user.id", ra.get("user.id", "")) or ""
            uname = ea.get("user.name", ra.get("user.name", "")) or ""
            roles = ea.get("user.roles", ra.get("user.roles"))
            if isinstance(roles, list):
                roles_arr = [str(x) for x in roles]
            elif roles is None:
                roles_arr = []
            else:
                roles_arr = [str(roles)]
            out["user_id"] = str(uid)
            out["user_name"] = str(uname)
            out["user_roles_json"] = json.dumps(roles_arr, separators=(",", ":"))

        return out

    def _resource_scope_base(
        self,
        project_id: Optional[str],
        resource: Dict[str, Any],
        scope: Dict[str, Any],
        schema: EventSchema,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Build the common per-row prefix from Resource and Scope, and return
        the unmatched resource and scope attributes after promotion.
        """
        rattrs = _attributes_to_dict((resource or {}).get("attributes"))
        sattrs = _attributes_to_dict((scope or {}).get("attributes"))

        base: Dict[str, Any] = {
            "project_id": project_id or self.default_project_id,
            "schema_version": 1,
            "service_name": rattrs.get("service.name") or self.default_service_name,
            "service_namespace": rattrs.get("service.namespace", ""),
            "service_instance_id": rattrs.get("service.instance.id", ""),
            "service_version": rattrs.get("service.version", ""),
            "deployment_env": rattrs.get("deployment.environment", ""),
            "scope_name": scope.get("name", "") if scope else "",
            "scope_version": scope.get("version", "") if scope else "",
        }

        unmatched_resource = _promote_attrs_to_row(rattrs, schema, base)
        unmatched_scope = _promote_attrs_to_row(sattrs, schema, base)

        return base, unmatched_resource, unmatched_scope

    def map_traces(self, payload: Dict[str, Any], *, project_id: Optional[str] = None) -> Tuple[List[dict], List[dict], List[dict]]:
        """Map OTLP Traces JSON to rows for spans, span events, and span links."""
        spans_out: List[dict] = []
        events_out: List[dict] = []
        links_out: List[dict] = []

        span_schema = self._schemas["spans"]
        event_schema = self._schemas["span_events"]
        link_schema = self._schemas["span_links"]

        span_start_ms: Dict[Tuple[str, str], int] = {}

        for rs in payload.get("resourceSpans", []) or []:
            resource = rs.get("resource") or {}
            scopes = rs.get("scopeSpans") or rs.get("instrumentationLibrarySpans") or []
            for ss in scopes:
                scope = ss.get("scope") or ss.get("instrumentationLibrary") or {}
                base, r_unmatched, s_unmatched = self._resource_scope_base(project_id, resource, scope, span_schema)
                for sp in ss.get("spans", []) or []:
                    trace_id = _lower_hex_or_empty(sp.get("traceId"))
                    span_id = _lower_hex_or_empty(sp.get("spanId"))
                    parent_span_id = _lower_hex_or_empty(sp.get("parentSpanId"))
                    start_ns = int(sp.get("startTimeUnixNano", 0) or 0)
                    end_ns = int(sp.get("endTimeUnixNano", 0) or 0)
                    start_ms = _ns_to_ms(start_ns)

                    span_attrs = _attributes_to_dict(sp.get("attributes"))
                    row = {
                        **base,
                        "trace_id": trace_id,
                        "span_id": span_id,
                        "parent_span_id": parent_span_id,
                        "name": sp.get("name", "") or "",
                        "kind": sp.get("kind", "") or "",
                        "start_time_unix_nano": start_ns,
                        "end_time_unix_nano": end_ns,
                        "status_code": (sp.get("status") or {}).get("code", "") or "",
                        "status_message": (sp.get("status") or {}).get("message", "") or "",
                        "dropped_events_count": int(sp.get("droppedEventsCount", 0) or 0),
                        "dropped_links_count": int(sp.get("droppedLinksCount", 0) or 0),
                    }

                    unmatched = _promote_attrs_to_row(span_attrs, span_schema, row)
                    row["span_attrs_json"] = unmatched
                    row["resource_attrs_json"] = r_unmatched
                    row["scope_attrs_json"] = s_unmatched

                    ident = self._extract_identity(span_attrs, span_attrs)
                    if ident:
                        row.update(ident)

                    spans_out.append(row)
                    span_start_ms[(trace_id, span_id)] = start_ms

                    for ev in sp.get("events", []) or []:
                        eattrs = _attributes_to_dict(ev.get("attributes"))
                        erow_base, r_unm_e, s_unm_e = self._resource_scope_base(project_id, resource, scope, event_schema)
                        erow = {
                            **erow_base,
                            "trace_id": trace_id,
                            "span_id": span_id,
                            "time_unix_nano": int(ev.get("timeUnixNano", 0) or 0),
                            "name": ev.get("name", "") or "",
                        }
                        eunmatched = _promote_attrs_to_row(eattrs, event_schema, erow)
                        erow["event_attrs_json"] = eunmatched
                        erow["resource_attrs_json"] = r_unm_e
                        erow["scope_attrs_json"] = s_unm_e

                        ident_e = self._extract_identity(eattrs, eattrs)
                        if ident_e:
                            erow.update(ident_e)

                        events_out.append(erow)

                    for lk in sp.get("links", []) or []:
                        lattrs = _attributes_to_dict(lk.get("attributes"))
                        lrow_base, r_unm_l, s_unm_l = self._resource_scope_base(project_id, resource, scope, link_schema)
                        lrow = {
                            **lrow_base,
                            "trace_id": trace_id,
                            "span_id": span_id,
                            "linked_trace_id": _lower_hex_or_empty(lk.get("traceId")),
                            "linked_span_id": _lower_hex_or_empty(lk.get("spanId")),
                            "event_ts": start_ms,
                            "event_date": _ms_to_date(start_ms) if start_ms else "1970-01-01",
                        }
                        lunmatched = _promote_attrs_to_row(lattrs, link_schema, lrow)
                        lrow["link_attrs_json"] = lunmatched
                        lrow["resource_attrs_json"] = r_unm_l
                        lrow["scope_attrs_json"] = s_unm_l

                        ident_l = self._extract_identity(lattrs, lattrs)
                        if ident_l:
                            lrow.update(ident_l)

                        links_out.append(lrow)

        return spans_out, events_out, links_out

    def map_logs(self, payload: Dict[str, Any], *, project_id: Optional[str] = None) -> List[dict]:
        """Map OTLP Logs JSON to LOGS table rows."""
        logs_out: List[dict] = []
        log_schema = self._schemas["logs"]

        for rl in payload.get("resourceLogs", []) or []:
            resource = rl.get("resource") or {}
            scopes = rl.get("scopeLogs") or rl.get("instrumentationLibraryLogs") or []
            for sl in scopes:
                scope = sl.get("scope") or sl.get("instrumentationLibrary") or {}
                base, r_unmatched, s_unmatched = self._resource_scope_base(project_id, resource, scope, log_schema)
                for rec in sl.get("logRecords", []) or []:
                    attrs = _attributes_to_dict(rec.get("attributes"))
                    trace_id = _lower_hex_or_empty(rec.get("traceId"))
                    span_id = _lower_hex_or_empty(rec.get("spanId"))
                    row = {
                        **base,
                        "time_unix_nano": int(rec.get("timeUnixNano", 0) or 0),
                        "observed_time_unix_nano": int(rec.get("observedTimeUnixNano", 0) or 0),
                        "severity_text": rec.get("severityText", "") or "",
                        "severity_number": int(rec.get("severityNumber", 0) or 0),
                        "body": _stringify_body(rec.get("body")),
                        "trace_id": trace_id,
                        "span_id": span_id,
                    }
                    unmatched = _promote_attrs_to_row(attrs, log_schema, row)
                    row["log_attrs_json"] = unmatched
                    row["resource_attrs_json"] = r_unmatched
                    row["scope_attrs_json"] = s_unmatched

                    ident = self._extract_identity(attrs, attrs)
                    if ident:
                        row.update(ident)

                    logs_out.append(row)

        return logs_out

    def map_metrics(self, payload: Dict[str, Any], *, project_id: Optional[str] = None) -> Tuple[List[dict], List[dict]]:
        """Map OTLP Metrics JSON to metric point and metric hist rows."""
        points_out: List[dict] = []
        hists_out: List[dict] = []

        point_schema = self._schemas["metrics_points"]
        hist_schema = self._schemas["metrics_hist"]

        for rm in payload.get("resourceMetrics", []) or []:
            resource = rm.get("resource") or {}
            scopes = rm.get("scopeMetrics") or rm.get("instrumentationLibraryMetrics") or []
            for sm in scopes:
                scope = sm.get("scope") or sm.get("instrumentationLibrary") or {}
                base_point, r_unmatched_p, s_unmatched_p = self._resource_scope_base(project_id, resource, scope, point_schema)
                base_hist, r_unmatched_h, s_unmatched_h = self._resource_scope_base(project_id, resource, scope, hist_schema)
                for m in sm.get("metrics", []) or []:
                    name = m.get("name", "") or ""
                    unit = m.get("unit", "") or ""

                    if "gauge" in m and m["gauge"]:
                        g = m["gauge"]
                        data = g.get("dataPoints", []) or []
                        for dp in data:
                            points_out.append(self._point_row(base_point, point_schema, r_unmatched_p, s_unmatched_p, name, unit, "Gauge", dp, aggregation_temporality="UNSPECIFIED", is_monotonic=False))

                    if "sum" in m and m["sum"]:
                        s = m["sum"]
                        data = s.get("dataPoints", []) or []
                        temporality = s.get("aggregationTemporality", "UNSPECIFIED")
                        mono = bool(s.get("isMonotonic", False))
                        for dp in data:
                            points_out.append(self._point_row(base_point, point_schema, r_unmatched_p, s_unmatched_p, name, unit, "Sum", dp, aggregation_temporality=temporality, is_monotonic=mono))

                    if "histogram" in m and m["histogram"]:
                        h = m["histogram"]
                        data = h.get("dataPoints", []) or []
                        temporality = h.get("aggregationTemporality", "UNSPECIFIED")
                        for dp in data:
                            hists_out.append(self._hist_row(base_hist, hist_schema, r_unmatched_h, s_unmatched_h, name, unit, "Histogram", dp, aggregation_temporality=temporality))

                    if "exponentialHistogram" in m and m["exponentialHistogram"]:
                        eh = m["exponentialHistogram"]
                        data = eh.get("dataPoints", []) or []
                        temporality = eh.get("aggregationTemporality", "UNSPECIFIED")
                        for dp in data:
                            hists_out.append(self._exphist_row(base_hist, hist_schema, r_unmatched_h, s_unmatched_h, name, unit, "ExpHistogram", dp, aggregation_temporality=temporality))

                    if "summary" in m and m["summary"]:
                        summ = m["summary"]
                        data = summ.get("dataPoints", []) or []
                        for dp in data:
                            hists_out.append(self._summary_row(base_hist, hist_schema, r_unmatched_h, s_unmatched_h, name, unit, "Summary", dp, aggregation_temporality="UNSPECIFIED"))

        return points_out, hists_out

    def _point_row(
        self,
        base: Dict[str, Any],
        schema: EventSchema,
        r_unmatched: Dict[str, Any],
        s_unmatched: Dict[str, Any],
        name: str,
        unit: str,
        itype: str,
        dp: Dict[str, Any],
        *,
        aggregation_temporality: str,
        is_monotonic: bool,
    ) -> Dict[str, Any]:
        """Build one METRIC_POINT row for Gauge/Sum datapoints."""
        val = dp.get("asDouble")
        if val is None:
            val = dp.get("asInt")
        if val is None and "value" in dp:
            val = dp["value"]
        if isinstance(val, dict):
            val = val.get("doubleValue", val.get("intValue"))
        value = float(val or 0.0)

        point_attrs = _attributes_to_dict(dp.get("attributes"))
        row = {
            **base,
            "instrument_name": name,
            "instrument_type": itype,
            "unit": unit,
            "aggregation_temporality": aggregation_temporality,
            "is_monotonic": bool(is_monotonic),
            "time_unix_nano": int(dp.get("timeUnixNano", 0) or 0),
            "start_time_unix_nano": int(dp.get("startTimeUnixNano", 0) or 0),
            "value": value,
        }
        unmatched = _promote_attrs_to_row(point_attrs, schema, row)
        row["point_attrs_json"] = unmatched
        row["exemplars_json"] = self._exemplars_to_json(dp.get("exemplars"))
        row["resource_attrs_json"] = r_unmatched
        row["scope_attrs_json"] = s_unmatched

        ident = self._extract_identity(point_attrs, point_attrs)
        if ident:
            row.update(ident)
        return row

    def _hist_row(
        self,
        base: Dict[str, Any],
        schema: EventSchema,
        r_unmatched: Dict[str, Any],
        s_unmatched: Dict[str, Any],
        name: str,
        unit: str,
        itype: str,
        dp: Dict[str, Any],
        *,
        aggregation_temporality: str,
    ) -> Dict[str, Any]:
        """Build one METRIC_HIST row for Histogram datapoints."""
        bounds = dp.get("explicitBounds")
        counts = dp.get("bucketCounts")
        point_attrs = _attributes_to_dict(dp.get("attributes"))
        row = {
            **base,
            "instrument_name": name,
            "instrument_type": itype,
            "unit": unit,
            "aggregation_temporality": aggregation_temporality,
            "time_unix_nano": int(dp.get("timeUnixNano", 0) or 0),
            "start_time_unix_nano": int(dp.get("startTimeUnixNano", 0) or 0),
            "count": int(dp.get("count", 0) or 0),
            "sum": float(dp.get("sum", 0.0) or 0.0),
            "min": float(dp.get("min", 0.0) or 0.0) if dp.get("min") is not None else 0.0,
            "max": float(dp.get("max", 0.0) or 0.0) if dp.get("max") is not None else 0.0,
            "bounds_json": json.dumps(bounds or [], separators=(",", ":")) if bounds is not None else "[]",
            "counts_json": json.dumps(counts or [], separators=(",", ":")) if counts is not None else "[]",
        }
        unmatched = _promote_attrs_to_row(point_attrs, schema, row)
        row["point_attrs_json"] = unmatched
        row["exemplars_json"] = self._exemplars_to_json(dp.get("exemplars"))
        row["resource_attrs_json"] = r_unmatched
        row["scope_attrs_json"] = s_unmatched
        ident = self._extract_identity(point_attrs, point_attrs)
        if ident:
            row.update(ident)
        return row

    def _exphist_row(
        self,
        base: Dict[str, Any],
        schema: EventSchema,
        r_unmatched: Dict[str, Any],
        s_unmatched: Dict[str, Any],
        name: str,
        unit: str,
        itype: str,
        dp: Dict[str, Any],
        *,
        aggregation_temporality: str,
    ) -> Dict[str, Any]:
        """Build one METRIC_HIST row for ExponentialHistogram datapoints."""
        point_attrs = _attributes_to_dict(dp.get("attributes"))
        pos = (dp.get("positive") or {})
        neg = (dp.get("negative") or {})
        row = {
            **base,
            "instrument_name": name,
            "instrument_type": itype,
            "unit": unit,
            "aggregation_temporality": aggregation_temporality,
            "time_unix_nano": int(dp.get("timeUnixNano", 0) or 0),
            "start_time_unix_nano": int(dp.get("startTimeUnixNano", 0) or 0),
            "count": int(dp.get("count", 0) or 0),
            "sum": float(dp.get("sum", 0.0) or 0.0),
            "min": float(dp.get("min", 0.0) or 0.0) if dp.get("min") is not None else 0.0,
            "max": float(dp.get("max", 0.0) or 0.0) if dp.get("max") is not None else 0.0,
            "exp_zero_count": int(dp.get("zeroCount", 0) or 0),
            "exp_scale": int(dp.get("scale", 0) or 0),
            "exp_positive_json": json.dumps(
                {"offset": int(pos.get("offset", 0) or 0), "counts": list(pos.get("bucketCounts", []) or [])},
                separators=(",", ":"),
            ),
            "exp_negative_json": json.dumps(
                {"offset": int(neg.get("offset", 0) or 0), "counts": list(neg.get("bucketCounts", []) or [])},
                separators=(",", ":"),
            ),
        }
        unmatched = _promote_attrs_to_row(point_attrs, schema, row)
        row["point_attrs_json"] = unmatched
        row["exemplars_json"] = self._exemplars_to_json(dp.get("exemplars"))
        row["resource_attrs_json"] = r_unmatched
        row["scope_attrs_json"] = s_unmatched
        ident = self._extract_identity(point_attrs, point_attrs)
        if ident:
            row.update(ident)
        return row

    def _summary_row(
        self,
        base: Dict[str, Any],
        schema: EventSchema,
        r_unmatched: Dict[str, Any],
        s_unmatched: Dict[str, Any],
        name: str,
        unit: str,
        itype: str,
        dp: Dict[str, Any],
        *,
        aggregation_temporality: str,
    ) -> Dict[str, Any]:
        """Build one METRIC_HIST row for Summary datapoints."""
        qv = []
        for it in dp.get("quantileValues", []) or []:
            qv.append({"q": float(it.get("quantile", 0.0) or 0.0), "v": float(it.get("value", 0.0) or 0.0)})
        point_attrs = _attributes_to_dict(dp.get("attributes"))

        row = {
            **base,
            "instrument_name": name,
            "instrument_type": itype,
            "unit": unit,
            "aggregation_temporality": aggregation_temporality,
            "time_unix_nano": int(dp.get("timeUnixNano", 0) or 0),
            "start_time_unix_nano": int(dp.get("startTimeUnixNano", 0) or 0),
            "count": int(dp.get("count", 0) or 0),
            "sum": float(dp.get("sum", 0.0) or 0.0),
            "quantiles_json": json.dumps(qv, separators=(",", ":")),
        }
        unmatched = _promote_attrs_to_row(point_attrs, schema, row)
        row["point_attrs_json"] = unmatched
        row["exemplars_json"] = "[]"
        row["resource_attrs_json"] = r_unmatched
        row["scope_attrs_json"] = s_unmatched
        ident = self._extract_identity(point_attrs, point_attrs)
        if ident:
            row.update(ident)
        return row

    def _exemplars_to_json(self, exs: Optional[List[Dict[str, Any]]]) -> str:
        """Convert exemplars to a compact JSON string."""
        if not exs:
            return "[]"
        out: List[Dict[str, Any]] = []
        for e in exs:
            val = e.get("asDouble")
            if val is None:
                val = e.get("asInt")
            if isinstance(val, dict):
                val = val.get("doubleValue", val.get("intValue"))
            out.append(
                {
                    "time_unix_nano": int(e.get("timeUnixNano", 0) or 0),
                    "value": float(val or 0.0),
                    "trace_id": _lower_hex_or_empty(e.get("traceId")),
                    "span_id": _lower_hex_or_empty(e.get("spanId")),
                    "filtered_attrs": _attributes_to_dict(e.get("filteredAttributes")),
                }
            )
        return json.dumps(out, separators=(",", ":"))
