"""
======================================================================
(A) FILE PATH & IMPORT PATH
depths/cli/app.py  →  import path: depths.cli.app
======================================================================

======================================================================
(B) FILE OVERVIEW (concept & significance in v0.1.2)
FastAPI service that exposes the Depths OTLP/HTTP ingestion surface and a
minimal query API. Responsibilities:
  • Accept OTLP JSON or protobuf for traces/logs/metrics and forward to
    DepthsLogger (which orchestrates Producer + Aggregator + Shipper).
  • Provide health and simple read endpoints backed by DepthsLogger readers.
  • Own the app lifecycle (start logger on boot; auto-flush on shutdown).

This is the main “edge” for v0.1.2: it receives telemetry and stores it
into per-day Delta tables locally (and eventually ships sealed days to S3).
======================================================================

======================================================================
(C) IMPORTS & GLOBALS (what & why)
FastAPI, Request/Response/Headers/Query  → HTTP server & validation
polars as pl                              → LazyFrame → DataFrame collection for /api/* queries
json, gzip, os                            → decoding, compression handling, instance env
DepthsLogger, DepthsLoggerOptions, S3Config → core runtime & S3 wiring
google.protobuf… (optional)               → OTLP protobuf (falls back to JSON if unavailable)

Globals:
  _PB_OK      → whether protobuf deps are importable
  _LOGGER     → process-wide singleton DepthsLogger (created lazily)
  app         → FastAPI instance (with lifespan manager)
======================================================================
"""

from __future__ import annotations

import gzip
import json
import os
from typing import Optional, Tuple, Iterable, List

import polars as pl
from fastapi import FastAPI, Request, Response, Header, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from depths.core.config import S3Config, DepthsLoggerOptions
from depths.core.logger import DepthsLogger

# Protobuf support
try:
    from google.protobuf.json_format import MessageToDict
    from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
        ExportTraceServiceRequest,
        ExportTraceServiceResponse,
    )
    from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import (
        ExportMetricsServiceRequest,
        ExportMetricsServiceResponse,
    )
    from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import (
        ExportLogsServiceRequest,
        ExportLogsServiceResponse,
    )
    _PB_OK = True
except ImportError:
    _PB_OK = False
    
# ---- Singleton logger wiring -------------------------------------------------

_LOGGER: Optional[DepthsLogger] = None



def _get_instance_settings() -> Tuple[str, str]:
    """
    Resolve Depths instance identity and data directory from the environment.

    Overview (v0.1.2 role):
        Centralizes how the service decides where to stage/write data on disk.
        Used by the singleton logger constructor to ensure consistent layout.

    Returns:
        (instance_id, instance_dir_abs): instance_id from DEPTHS_INSTANCE_ID
        (default 'default'), and absolute instance_dir from DEPTHS_INSTANCE_DIR
        (default './depths_data' resolved to an absolute path).
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Keep defaults stable; the CLI injects these env vars for background runs.
    # - Do not validate existence here; the logger ensures/creates directories.

    instance_id = os.environ.get("DEPTHS_INSTANCE_ID", "default")
    instance_dir = os.environ.get("DEPTHS_INSTANCE_DIR", os.path.abspath("./depths_data"))
    return instance_id, instance_dir


def _get_logger() -> DepthsLogger:
    """
    Return the process-wide DepthsLogger singleton (construct if missing).

    Overview (v0.1.2 role):
        Wires in S3 (if env is present) and standard DepthsLoggerOptions, then
        starts background services per options. All endpoints use this singleton.

    Returns:
        DepthsLogger instance.

    Raises:
        (None directly) — S3Config.from_env errors are swallowed to allow
        local-only operation when S3 isn't configured.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Lazily initialized to avoid side effects during module import.
    # - Options are currently defaulted; evolve later to read persisted configs.
    # - S3 optional; local-only mode if not configured

    global _LOGGER
    if _LOGGER is None:
        instance_id, instance_dir = _get_instance_settings()
        s3 = None
        try:
            s3 = S3Config.from_env()
        except Exception:
            s3 = None  
        _LOGGER = DepthsLogger(
            instance_id=instance_id,
            instance_dir=instance_dir,
            s3=s3,
            options=DepthsLoggerOptions(),
        )
    return _LOGGER

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan manager that starts the logger on startup and
    gracefully flushes buffers on shutdown.

    Overview (v0.1.2 role):
        Ensures the Aggregators are running before any traffic arrives and that
        pending batches are flushed (with a bounded wait) on process exit.

    Args:
        app: FastAPI instance (unused, required by FastAPI).

    Yields:
        None (control returns to FastAPI to serve requests).

    Exceptions:
        Any start/stop exceptions are caught to keep the server responsive.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Uses DepthsLogger.astop(flush="auto") which applies a small wait envelope
    #   to encourage a final quiet/age-triggered flush before returning.

    lg = _get_logger()
    try:
        lg.start()  
    except Exception:
        pass
    try:
        yield
    finally:
        try:
            await lg.astop(flush="auto")  
        except Exception:
            pass

app = FastAPI(title="depths OTLP/HTTP", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        
    allow_methods=["*"],       
    allow_headers=["*"],       
    allow_credentials=False,   
    expose_headers=[],         
    max_age=86400,             
)

def _media_type(content_type: Optional[str]) -> str:
    return (content_type or "").split(";")[0].strip().lower()

def _want_jsonish(content_type: Optional[str]) -> bool:
    mt = _media_type(content_type)
    return mt in ("application/json", "text/plain")

def _want_json(content_type: str) -> bool:
    """
    Predicate for OTLP JSON payloads.

    Args:
        content_type: Raw Content-Type header.

    Returns:
        True if the media type equals 'application/json' (ignoring parameters).
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Keep strict; OTLP spec uses 'application/json' and 'application/x-protobuf'.

    return (content_type or "").split(";")[0].strip().lower() == "application/json"


def _want_protobuf(content_type: str) -> bool:
    """
    Predicate for OTLP protobuf payloads.

    Args:
        content_type: Raw Content-Type header.

    Returns:
        True if the media type equals 'application/x-protobuf'.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Gate protobuf processing on _PB_OK; when False we return a 415-compatible
    #   empty response from _empty_response_for(...) to keep clients happy.

    return (content_type or "").split(";")[0].strip().lower() == "application/x-protobuf"


async def _read_body(request: Request) -> bytes:
    """
    Read and (optionally) gunzip the request body.

    Overview (v0.1.2 role):
        OTLP senders often compress payloads. This function normalizes input
        for both JSON and protobuf ingestion paths.

    Args:
        request: FastAPI Request object.

    Returns:
        Decompressed raw bytes.

    Raises:
        HTTPException(400): When 'content-encoding: gzip' is set but decompression fails.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - We only support 'gzip' here; other codings can be added if needed.

    raw = await request.body()
    enc = request.headers.get("content-encoding", "").lower()
    if enc == "gzip":
        try:
            return gzip.decompress(raw)
        except Exception:
            raise HTTPException(status_code=400, detail="gzip_decompress_failed")
    return raw


def _project_from(request: Request, header_override: Optional[str]) -> Optional[str]:
    """
    Determine project_id for ingestion.

    Overview (v0.1.2 role):
        Allows multi-tenancy by checking a sequence of locations:
        explicit override header param, 'x-depths-project-id', 'x-otlp-project-id',
        and 'project_id' query param.

    Args:
        request: FastAPI Request (used for headers and query params).
        header_override: Value from dependency-injected header param.

    Returns:
        project_id string or None if not provided.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - DepthsLogger also has a mapper default; passing None falls back to that.

    return (
        header_override
        or request.headers.get("x-depths-project-id")
        or request.headers.get("x-otlp-project-id")
        or request.query_params.get("project_id")
    )


def _csv_list(x: Optional[str]) -> Optional[List[str]]:
    """
    Parse a comma-separated string into a list of non-empty, stripped tokens.

    Args:
        x: Raw comma-separated string or None.

    Returns:
        List of strings or None if input is falsy.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Used by /api/* 'select' query to build a column list.

    if not x:
        return None
    return [s for s in (t.strip() for t in x.split(",")) if s]


def _collect_json(lf: pl.LazyFrame) -> list[dict]:
    """
    Collect a LazyFrame and return JSON-friendly row dicts.

    Overview (v0.1.2 role):
        Shared collector for the query endpoints to keep error handling
        consistent and avoid duplicating Polars interaction.

    Args:
        lf: Polars LazyFrame.

    Returns:
        List of Python dictionaries (Polars converts columns to native types).

    Raises:
        HTTPException(500): if .collect() fails (e.g., I/O/scan errors).
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Avoids returning Polars objects directly; keeps API payloads simple.

    try:
        df = lf.collect()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"query_collect_failed: {e}")
    return df.to_dicts()


def _empty_response_for(content_type: str, signal: str, rejected: int = 0, error_message: Optional[str] = None) -> Response:
    """
    Build an OTLP-compliant empty (or partial-success) response.

    Overview (v0.1.2 role):
        OTLP Export*Service responses are empty on full success; on partial
        success we populate the appropriate 'partialSuccess' fields for the
        given signal (traces/metrics/logs) in JSON or protobuf.

    Args:
        content_type: Request Content-Type to mirror (json/protobuf).
        signal: One of 'traces' | 'metrics' | 'logs'.
        rejected: Count of rejected records (if any).
        error_message: Text to include with partial success.

    Returns:
        FastAPI Response (JSONResponse, protobuf bytes Response, or 415 text).
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - When protobuf libs are unavailable, we return a helpful 415-ish message
    #   via JSON/text to nudge users; JSON path is always available.

    if _want_protobuf(content_type) and _PB_OK:
        if signal == "traces":
            msg = ExportTraceServiceResponse()
            if rejected and error_message is not None:
                ps = msg.partial_success
                ps.rejected_spans = int(rejected)
                ps.error_message = error_message
        elif signal == "metrics":
            msg = ExportMetricsServiceResponse()
            if rejected and error_message is not None:
                ps = msg.partial_success
                ps.rejected_data_points = int(rejected)
                ps.error_message = error_message
        else:
            msg = ExportLogsServiceResponse()
            if rejected and error_message is not None:
                ps = msg.partial_success
                ps.rejected_log_records = int(rejected)
                ps.error_message = error_message
        return Response(content=msg.SerializeToString(), media_type="application/x-protobuf")

    if rejected and error_message is not None:
        if signal == "traces":
            body = {"partialSuccess": {"rejectedSpans": int(rejected), "errorMessage": error_message}}
        elif signal == "metrics":
            body = {"partialSuccess": {"rejectedDataPoints": int(rejected), "errorMessage": error_message}}
        else:
            body = {"partialSuccess": {"rejectedLogRecords": int(rejected), "errorMessage": error_message}}
        return JSONResponse(content=body, media_type="application/json")

    return JSONResponse(content={}, media_type="application/json")

@app.get("/healthz")
async def health():
    """
    Liveness/quick diagnostic endpoint.

    Returns:
        JSON with {'ok': True, 'logger': <metrics dict>} reflecting current
        aggregator states and minimal DepthsLogger process info.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Keep inexpensive; metrics are already aggregated in memory.

    lg = _get_logger()
    m = lg.metrics()
    return {"ok": True, "logger": m}


@app.post("/v1/traces")
async def post_traces(
    request: Request,
    content_type: Optional[str] = Header(default="application/json"),
    x_depths_project_id: Optional[str] = Header(default=None),
):
    """
    OTLP/HTTP traces ingestion endpoint (JSON or protobuf).

    Overview (v0.1.2 role):
        Decodes payload, passes to DepthsLogger.ingest_otlp_traces_json(...),
        and responds with an empty or partial-success ExportTraceServiceResponse.

    Args:
        request: FastAPI Request used to read the body (possibly gzip).
        content_type: 'application/json' or 'application/x-protobuf'.
        x_depths_project_id: Optional per-request project override.

    Returns:
        FastAPI Response appropriate for the content type (JSON/protobuf).
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Rejects due to schema/date checks surface in partialSuccess (rejectedSpans).
    # - Non-JSON/protobuf content types return HTTP 415.

    lg = _get_logger()
    body = await _read_body(request)
    project_id = _project_from(request, x_depths_project_id)

    try:
        if _want_jsonish(content_type):
            payload = json.loads(body.decode("utf-8") or "{}")
        elif _want_protobuf(content_type):
            if not _PB_OK:
                return _empty_response_for(content_type, "traces")  # 415 handled inside
            req = ExportTraceServiceRequest()
            req.ParseFromString(body)
            payload = MessageToDict(req)
        else:
            try:
                payload = json.loads(body.decode("utf-8") or "{}")
            except Exception:
                raise HTTPException(status_code=415, detail="unsupported_content_type")
            
    except Exception:
        raise HTTPException(status_code=400, detail="bad_request_payload")

    res = lg.ingest_otlp_traces_json(payload, project_id=project_id)
    rejected = int(res.get("rejected", 0))
    if rejected > 0:
        return _empty_response_for(
            content_type, "traces", rejected=rejected, error_message="Some spans/events/links were rejected due to schema or date checks."
        )
    return _empty_response_for(content_type, "traces")


@app.post("/v1/logs")
async def post_logs(
    request: Request,
    content_type: Optional[str] = Header(default="application/json"),
    x_depths_project_id: Optional[str] = Header(default=None),
):
    """
    OTLP/HTTP logs ingestion endpoint (JSON or protobuf).

    Args:
        request: FastAPI Request used to read (maybe gzip) body.
        content_type: 'application/json' or 'application/x-protobuf'.
        x_depths_project_id: Optional per-request project override.

    Returns:
        FastAPI Response (empty or partial-success for rejectedLogRecords).
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Body AnyValue is stringified by the mapper for LOGS.body.

    lg = _get_logger()
    body = await _read_body(request)
    project_id = _project_from(request, x_depths_project_id)

    try:
        if _want_jsonish(content_type):
            payload = json.loads(body.decode("utf-8") or "{}")
        elif _want_protobuf(content_type):
            if not _PB_OK:
                return _empty_response_for(content_type, "logs")
            req = ExportLogsServiceRequest()
            req.ParseFromString(body)
            payload = MessageToDict(req)
        else:
            try:
                payload = json.loads(body.decode("utf-8") or "{}")
            except Exception:
                raise HTTPException(status_code=415, detail="unsupported_content_type")
    except Exception:
        raise HTTPException(status_code=400, detail="bad_request_payload")

    res = lg.ingest_otlp_logs_json(payload, project_id=project_id)
    rejected = int(res.get("rejected", 0))
    if rejected > 0:
        return _empty_response_for(
            content_type, "logs", rejected=rejected, error_message="Some log records were rejected due to schema or date checks."
        )
    return _empty_response_for(content_type, "logs")


@app.post("/v1/metrics")
async def post_metrics(
    request: Request,
    content_type: Optional[str] = Header(default="application/json"),
    x_depths_project_id: Optional[str] = Header(default=None),
):
    """
    OTLP/HTTP metrics ingestion endpoint (JSON or protobuf).

    Args:
        request: FastAPI Request used to read (maybe gzip) body.
        content_type: 'application/json' or 'application/x-protobuf'.
        x_depths_project_id: Optional per-request project override.

    Returns:
        FastAPI Response (empty or partial-success for rejectedDataPoints).
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Both Metric Points and Hists are handled by the mapper; producer enforces schema.

    lg = _get_logger()
    body = await _read_body(request)
    project_id = _project_from(request, x_depths_project_id)

    try:
        if _want_jsonish(content_type):
            payload = json.loads(body.decode("utf-8") or "{}")
        elif _want_protobuf(content_type):
            if not _PB_OK:
                return _empty_response_for(content_type, "metrics")
            req = ExportMetricsServiceRequest()
            req.ParseFromString(body)
            payload = MessageToDict(req)
        else:
            try:
                payload = json.loads(body.decode("utf-8") or "{}")
            except Exception:
                print("couldnt parse")
                raise HTTPException(status_code=415, detail="unsupported_content_type")
            
    except Exception:
        raise HTTPException(status_code=400, detail="bad_request_payload")

    res = lg.ingest_otlp_metrics_json(payload, project_id=project_id)
    rejected = int(res.get("rejected", 0))
    if rejected > 0:
        return _empty_response_for(
            content_type, "metrics", rejected=rejected, error_message="Some metric points were rejected due to schema or date checks."
        )
    return _empty_response_for(content_type, "metrics")

# ---- Stats registration API (v0.2.0) -----------------------------------------

@app.post("/api/stats/categorical/add")
async def api_stats_categorical_add(
    project_id: str = Query(...),
    otel_table: str = Query(..., pattern="^(spans|span_events|span_links|logs|metrics_points|metrics_hist)$"),
    column: str = Query(...),
    windows: str = Query(..., description="CSV from {1m,5m,15m,30m,1h,1d} (e.g. '1m,5m')"),
):
    """
    Register categorical stats tracking for a string column at one or more windows.

    Behavior:
        - Calls DepthsLogger.stats_add_category(...) which validates the column type
          against the composed schema and activates tracking from the next UTC minute.

    Query Params:
        project_id: Tenant/project id.
        otel_table: One of spans|span_events|span_links|logs|metrics_points|metrics_hist.
        column:     Top-level string column to histogram.
        windows:    CSV list of window shorthands: 1m,5m,15m,30m,1h,1d.

    Returns:
        {"ok": true, "registered": {"project_id", "otel_table", "column", "windows"}}
    """
    lg = _get_logger()
    win_list = _csv_list(windows) or []
    if not win_list:
        raise HTTPException(status_code=400, detail="windows_required")
    try:
        lg.stats_add_category(
            project_id=project_id,
            otel_table=otel_table,
            column=column,
            windows=win_list,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"stats_add_category_failed: {e}")
    return {
        "ok": True,
        "registered": {
            "project_id": project_id,
            "otel_table": otel_table,
            "column": column,
            "windows": win_list,
        },
    }


@app.post("/api/stats/numeric/add")
async def api_stats_numeric_add(
    project_id: str = Query(...),
    otel_table: str = Query(..., pattern="^(spans|span_events|span_links|logs|metrics_points|metrics_hist)$"),
    column: str = Query(...),
    windows: str = Query(..., description="CSV from {1m,5m,15m,30m,1h,1d} (e.g. '1m,5m')"),
):
    """
    Register numeric stats tracking for an int/float column at one or more windows.

    Behavior:
        - Calls DepthsLogger.stats_add_numeric(...). Measures per bucket use population
          semantics: event_count, value_min, value_max, value_mean, value_std, value_sum.
        - Activation is from the next UTC minute.

    Query Params:
        project_id: Tenant/project id.
        otel_table: One of spans|span_events|span_links|logs|metrics_points|metrics_hist.
        column:     Top-level numeric column (int/float).
        windows:    CSV list of window shorthands: 1m,5m,15m,30m,1h,1d.

    Returns:
        {"ok": true, "registered": {"project_id", "otel_table", "column", "windows"}}
    """
    lg = _get_logger()
    win_list = _csv_list(windows) or []
    if not win_list:
        raise HTTPException(status_code=400, detail="windows_required")
    try:
        lg.stats_add_numeric(
            project_id=project_id,
            otel_table=otel_table,
            column=column,
            windows=win_list,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"stats_add_numeric_failed: {e}")
    return {
        "ok": True,
        "registered": {
            "project_id": project_id,
            "otel_table": otel_table,
            "column": column,
            "windows": win_list,
        },
    }


@app.post("/api/stats/remove")
async def api_stats_remove(
    project_id: str = Query(...),
    otel_table: str = Query(..., pattern="^(spans|span_events|span_links|logs|metrics_points|metrics_hist)$"),
    column: str = Query(...),
    window: str = Query(..., description="One of 1m,5m,15m,30m,1h,1d"),
):
    """
    Stop a previously registered stats tracking task at the end of the current UTC minute.

    Query Params:
        project_id: Tenant/project id.
        otel_table: One of spans|span_events|span_links|logs|metrics_points|metrics_hist.
        column:     The tracked column.
        window:     The single window shorthand for the task to remove.

    Returns:
        {"ok": true, "removed": {"project_id","otel_table","column","window"}}
    """
    lg = _get_logger()
    try:
        lg.stats_remove(
            project_id=project_id,
            otel_table=otel_table,
            column=column,
            window=window,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"stats_remove_failed: {e}")
    return {
        "ok": True,
        "removed": {
            "project_id": project_id,
            "otel_table": otel_table,
            "column": column,
            "window": window,
        },
    }

@app.get("/api/spans")
async def api_spans(
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    project_id: Optional[str] = Query(default=None),
    service_name: Optional[str] = Query(default=None),
    trace_id: Optional[str] = Query(default=None),
    span_id: Optional[str] = Query(default=None),
    name: Optional[str] = Query(default=None),
    name_like: Optional[str] = Query(default=None),
    status_code: Optional[str] = Query(default=None),
    kind: Optional[str] = Query(default=None),
    time_ms_from: Optional[int] = Query(default=None),
    time_ms_to: Optional[int] = Query(default=None),
    select: Optional[str] = Query(default=None, description="Comma-separated columns"),
    max_rows: Optional[int] = Query(default=100),
    storage: Optional[str] = Query(default="auto", pattern="^(auto|local|s3)$"),
):
    """
    Query spans with common predicates (lazy scan + pushdown).

    Overview (v0.1.2 role):
        Thin wrapper over DepthsLogger.read_spans(...). Returns JSON rows
        collected from a LazyFrame.

    Returns:
        {'rows': [...], 'count': int}
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Errors during collect surface as HTTP 500 via _collect_json.
    
    lg = _get_logger()
    result = lg.read_spans(
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        service_name=service_name,
        trace_id=trace_id,
        span_id=span_id,
        name=name,
        name_like=name_like,
        status_code=status_code,
        kind=kind,
        time_ms_from=time_ms_from,
        time_ms_to=time_ms_to,
        select=_csv_list(select),
        max_rows=max_rows,
        return_as="dicts",
        storage=storage or "auto",
    )
    return {"rows": result, "count": len(result)}


@app.get("/api/logs")
async def api_logs(
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    project_id: Optional[str] = Query(default=None),
    service_name: Optional[str] = Query(default=None),
    severity_ge: Optional[int] = Query(default=None),
    body_like: Optional[str] = Query(default=None),
    trace_id: Optional[str] = Query(default=None),
    span_id: Optional[str] = Query(default=None),
    time_ms_from: Optional[int] = Query(default=None),
    time_ms_to: Optional[int] = Query(default=None),
    select: Optional[str] = Query(default=None, description="Comma-separated columns"),
    max_rows: Optional[int] = Query(default=100),
    storage: Optional[str] = Query(default="auto", pattern="^(auto|local|s3)$"),
):
    """
    Query logs with common predicates (lazy scan + pushdown).

    Overview (v0.1.2 role):
        Wrapper over DepthsLogger.read_logs(...). Returns JSON rows
        collected from a LazyFrame.

    
    Returns:
        {'rows': [...], 'count': int}
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - severity_ge maps to 'severity_number >= ...' in the lazy filter.
    
    lg = _get_logger()
    result = lg.read_logs(
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        service_name=service_name,
        severity_ge=severity_ge,
        body_like=body_like,
        trace_id=trace_id,
        span_id=span_id,
        time_ms_from=time_ms_from,
        time_ms_to=time_ms_to,
        select=_csv_list(select),
        max_rows=max_rows,
        return_as="dicts",
        storage=storage or "auto",
    )
    return {"rows": result, "count": len(result)}


@app.get("/api/metrics/points")
async def api_metrics_points(
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    project_id: Optional[str] = Query(default=None),
    service_name: Optional[str] = Query(default=None),
    instrument_name: Optional[str] = Query(default=None),
    instrument_type: Optional[str] = Query(default=None),
    time_ms_from: Optional[int] = Query(default=None),
    time_ms_to: Optional[int] = Query(default=None),
    select: Optional[str] = Query(default=None, description="Comma-separated columns"),
    max_rows: Optional[int] = Query(default=100),
    storage: Optional[str] = Query(default="auto", pattern="^(auto|local|s3)$"),
):
    """
    Query metric points (Gauge/Sum).

    Overview (v0.1.2 role):
        Wrapper over DepthsLogger.read_metrics_points(...).

    Returns:
        {'rows': [...], 'count': int}
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Keep payload sizes small: default limit=100.

    lg = _get_logger()
    result = lg.read_metrics_points(
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        service_name=service_name,
        instrument_name=instrument_name,
        instrument_type=instrument_type,
        time_ms_from=time_ms_from,
        time_ms_to=time_ms_to,
        select=_csv_list(select),
        max_rows=max_rows,
        return_as="dicts",
        storage=storage or "auto",
    )
    return {"rows": result, "count": len(result)}


@app.get("/api/metrics/hist")
async def api_metrics_hist(
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    project_id: Optional[str] = Query(default=None),
    service_name: Optional[str] = Query(default=None),
    instrument_name: Optional[str] = Query(default=None),
    instrument_type: Optional[str] = Query(default=None),
    time_ms_from: Optional[int] = Query(default=None),
    time_ms_to: Optional[int] = Query(default=None),
    select: Optional[str] = Query(default=None, description="Comma-separated columns"),
    max_rows: Optional[int] = Query(default=100),
    storage: Optional[str] = Query(default="auto", pattern="^(auto|local|s3)$"),
):
    """
    Query histogram-like metrics (Histogram/ExpHistogram/Summary).

    Overview (v0.1.2 role):
        Wrapper over DepthsLogger.read_metrics_hist(...).

    Returns:
        {'rows': [...], 'count': int}
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Bounds/counts/quantiles are JSON strings in the table schema.

    lg = _get_logger()
    result = lg.read_metrics_hist(
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        service_name=service_name,
        instrument_name=instrument_name,
        instrument_type=instrument_type,
        time_ms_from=time_ms_from,
        time_ms_to=time_ms_to,
        select=_csv_list(select),
        max_rows=max_rows,
        return_as="dicts",
        storage=storage or "auto",
    )
    return {"rows": result, "count": len(result)}

@app.get("/api/stats/categorical")
async def api_stats_categorical(
    project_id: Optional[str] = Query(default=None),
    otel_table: Optional[str] = Query(default=None),
    column: Optional[str] = Query(default=None),
    window: Optional[str] = Query(default=None, description="1m|5m|15m|30m|1h|1d"),
    minute_ts_from: Optional[int] = Query(default=None),
    minute_ts_to: Optional[int] = Query(default=None),
    select: Optional[str] = Query(default=None, description="comma-separated list of columns"),
    max_rows: int = Query(default=100, ge=1, le=10_000)
):
    """Read categorical stats from the Stats sidecar (categories[], counts[] per bucket)."""
    lg = _get_logger()
    select_cols = _csv_list(select)
    lf = lg.read_categorical_stats(
        project_id=project_id,
        otel_table=otel_table,
        column=column,
        window=window,
        minute_ts_from=minute_ts_from,
        minute_ts_to=minute_ts_to,
        select=select_cols,
        max_rows=max_rows,
        return_as="lazy",
    )
    return _collect_json(lf)


@app.get("/api/stats/numeric")
async def api_stats_numeric(
    project_id: Optional[str] = Query(default=None),
    otel_table: Optional[str] = Query(default=None),
    column: Optional[str] = Query(default=None),
    window: Optional[str] = Query(default=None, description="1m|5m|15m|30m|1h|1d"),
    minute_ts_from: Optional[int] = Query(default=None),
    minute_ts_to: Optional[int] = Query(default=None),
    select: Optional[str] = Query(default=None, description="comma-separated list of columns"),
    max_rows: int = Query(default=100, ge=1, le=10_000)
):
    """Read numeric stats from the Stats sidecar (count/min/max/mean/std/sum per bucket)."""
    lg = _get_logger()
    select_cols = _csv_list(select)
    lf = lg.read_numeric_stats(
        project_id=project_id,
        otel_table=otel_table,
        column=column,
        window=window,
        minute_ts_from=minute_ts_from,
        minute_ts_to=minute_ts_to,
        select=select_cols,
        max_rows=max_rows,
        return_as="lazy",
    )
    return _collect_json(lf)


@app.get("/rt/{signal}")
async def rt_stream(
    signal: str,
    project_id: Optional[str] = Query(default=None),
    n: Optional[int] = Query(default=200, description="Initial burst size (best-effort)"),
    heartbeat_s: Optional[int] = Query(default=10, description="Heartbeat interval seconds"),
):
    """
    Real-time Server-Sent Events (SSE) stream of newest telemetry.

    Overview (v0.1.2 role):
        Streams a one-way feed of the latest in-memory telemetry maintained by
        RealtimeTap. The stream begins with an initial burst (best-effort) and
        then continues with incremental updates and periodic heartbeats.

    Caveat:
        This is a *real-time* view; some events may not persist to storage.

    Args:
        signal: One of 'traces' | 'logs' | 'metrics' (family-level).
        project_id: Optional filter (server-side) on project.
        n: Initial tail size hint (best-effort; does not exceed internal caps).
        heartbeat_s: Interval for comment heartbeats to keep the connection alive.

    Returns:
        StreamingResponse with 'text/event-stream' media type.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Endpoint accepts family-level tokens ('traces'|'logs'|'metrics'). We map
    #   these to canonical tokens understood by RealtimeTap for deque selection:
    #     'traces'  → 'spans'          (covers spans/events/links in the same family)
    #     'logs'    → 'logs'
    #     'metrics' → 'metrics_points' (family includes hist as well)
    # - We emit an initial burst explicitly, then delegate to RealtimeTap.sse_iter(...).
    #   To avoid duplication, we skip the same number of 'data:' events from the
    #   sidecar iterator before yielding through.

    fam = signal.lower().strip()
    fam_map = {"traces": "spans", "logs": "logs", "metrics": "metrics_points"}
    canon = fam_map.get(fam, fam)

    lg = _get_logger()
    initial = lg.read_realtime(canon, n=max(0, int(n or 0)), project_id=project_id)
    skip = len(initial)
    hb = max(1, int(heartbeat_s or 10))

    def _gen():
        # Initial burst
        for r in initial:
            payload = json.dumps(r, separators=(",", ":")).encode("utf-8")
            yield b"data: " + payload + b"\n\n"
        # Delegate to the sidecar iterator; drop the first `skip` data events to
        # avoid duplicates from the iterator's initial replay.
        it = lg._realtime.sse_iter(canon, project_id=project_id, heartbeat_s=hb)  # noqa: SLF001 (internal ok here)
        dropped = 0
        for chunk in it:
            if skip and chunk.startswith(b"data: "):
                dropped += 1
                if dropped <= skip:
                    continue
            yield chunk

    headers = {
        "Cache-Control": "no-cache",
        "X-Depths-Realtime": "non-persisted-events-possible",
    }
    return StreamingResponse(_gen(), media_type="text/event-stream", headers=headers)
