
"""
Typed configuration objects for Depths’ runtime. Centralizes all knobs for
ingestion, background sidecars, and read paths so callers can bootstrap a
DepthsLogger instance with sensible defaults and minimal ceremony.

Some key configurations are:
- DepthsLoggerOptions: The key configuration option to control the DepthsLogger itself
- LogProducerConfig: Configuration for in-memory queues where the signals get ingested upon arrival
- LogAggregatorConfig: The poller+writer confifguration, that extracts signals from in-memory queue and periodically persists them on disk
- S3Config: Controls the S3/S3-compatible object store CRUD configuration
- StatsConfig: Controls the generalized Stats sidecar (v0.2.0): lateness tolerance, optimize cadence, and categorical cap to prevent memory blow-ups.

Design notes:
  • All configs are typed and immutable-at-callers (dataclass-like semantics).
  • Sensible defaults mean most users won’t touch StatsConfig directly; they
    opt in/out and select tracked columns in code via DepthsLogger helpers.
    
"""

from __future__ import annotations
from dataclasses import dataclass, field, replace, asdict
from typing import Dict, List, Optional, Literal, Any
import json
import os
import posixpath
from pathlib import Path
import polars as pl

from depths.core.schema import EventSchema, LOG_SCHEMA, SchemaDelta


_PYTYPE_TO_TOKEN: Dict[type, str] = {
    str: "str",
    int: "int",
    float: "float",
    bool: "bool",
    bytes: "bytes",
}
_TOKEN_TO_PYTYPE: Dict[str, type] = {v: k for (k, v) in _PYTYPE_TO_TOKEN.items()}

def _encode_dtype(spec: object) -> object:
    """
    Convert a SchemaDelta field dtype spec into a JSON-safe token.
    - scalar types -> "str" | "int" | "float" | "bool" | "bytes"
    - list specs   -> ["list", <token>]
    """
    if isinstance(spec, tuple) and len(spec) == 2 and spec[0] == "list":
        inner = spec[1]
        if inner not in _PYTYPE_TO_TOKEN:
            raise TypeError(f"Unsupported list inner type for SchemaDelta: {inner!r}")
        return ["list", _PYTYPE_TO_TOKEN[inner]]
    if isinstance(spec, type) and spec in _PYTYPE_TO_TOKEN:
        return _PYTYPE_TO_TOKEN[spec]
    raise TypeError(f"Unsupported dtype spec for SchemaDelta: {spec!r}")

def _decode_dtype(token: object) -> object:
    """
    Reverse of _encode_dtype.
    - "str"/"int"/"float"/"bool"/"bytes" -> Python type
    - ["list", <token>]                  -> ('list', Python type)
    """
    if isinstance(token, list) and len(token) == 2 and token[0] == "list":
        inner_tok = token[1]
        if inner_tok not in _TOKEN_TO_PYTYPE:
            raise TypeError(f"Unknown list inner token in SchemaDelta: {inner_tok!r}")
        return ("list", _TOKEN_TO_PYTYPE[inner_tok])
    if isinstance(token, str) and token in _TOKEN_TO_PYTYPE:
        return _TOKEN_TO_PYTYPE[token]
    raise TypeError(f"Unsupported dtype token for SchemaDelta: {token!r}")

def _schema_delta_to_dict(d: SchemaDelta) -> dict:
    """
    Serialize a SchemaDelta to a JSON-friendly dict.
    """
    return {
        "fields": {k: _encode_dtype(v) for k, v in (d.fields or {}).items()},
        "required": sorted(list(d.required or set())),
        "defaults": dict(d.defaults or {}),
        "json_fields": sorted(list(d.json_fields or set())),
    }

def _schema_delta_from_dict(obj: dict) -> SchemaDelta:
    """Rehydrate SchemaDelta from a JSON dict produced by _schema_delta_to_dict."""
    fields = {k: _decode_dtype(v) for k, v in (obj.get("fields") or {}).items()}
    required = set(obj.get("required") or [])
    defaults = dict(obj.get("defaults") or {})
    json_fields = set(obj.get("json_fields") or [])
    return SchemaDelta(
        fields=fields,
        required=required,
        defaults=defaults,
        json_fields=json_fields,
    )

def _save_json(path: Path, obj: dict) -> None:
    """
    Atomically persist a JSON-serializable mapping to disk.

    Overview (v0.2.0 role):
        Used by options/manifests across Depths to store small control-plane
        records (e.g., options.json, shipping index snapshots) without risking
        partial writes.

    Args:
        path: Destination file path.
        obj:  JSON-serializable dict to write.

    Returns:
        None

    Raises:
        OSError: On write/rename failures (bubble up to caller).
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True))
    tmp.replace(path)

def _load_json(path: Path) -> dict | None:
    """
    Load a small JSON file from disk.

    Overview (v0.2.0 role):
        Complements `_save_json` for reading options/manifests. Missing files
        are common on first-run and return None.

    Args:
        path: Source file path.

    Returns:
        Parsed dict, or None if the file does not exist.

    Raises:
        json.JSONDecodeError: If the file exists but is invalid JSON.
        OSError: Other I/O errors are surfaced to the caller.
    """

    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return None

# ------------------------- v0.2.0: Stats (new) -------------------------

@dataclass(frozen=True)
class StatsConfig:
    """
    Generalized Stats sidecar settings (v0.2.0).

    Overview:
        Controls the background stats worker that tracks developer-chosen
        columns as independent tasks per (project_id, otel_table, column, window).
        Two kinds are supported via separate tables/queues: categorical & numeric.

    Fields:
        enabled: Whether Stats is active.
        allowed_lateness_s: Grace (in seconds) to tolerate late events before finalizing a bucket.
        optimize_frequency: Run Delta OPTIMIZE after this many flush waves.
        max_categories: Upper bound on unique categories per (task, bucket). New categories
                        beyond this cap are silently ignored.
    """

    enabled: bool = True
    allowed_lateness_s: int = 15
    optimize_frequency: int = 12
    max_categories: int = 200

    @classmethod
    def from_env(cls, env: dict | None = None) -> "StatsConfig":
        """
        Build a config from environment variables (placeholder hook).

        Args:
            env: Mapping of env vars (unused for now).

        Returns:
            StatsConfig with defaults.
        """
        return cls()

    def to_dict(self) -> dict:
        """
        Serialize to a portable dict.

        Returns:
            Dict capturing all fields.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "StatsConfig":
        """
        Rehydrate from a dict produced by `to_dict`.

        Args:
            d: Portable dict.

        Returns:
            StatsConfig with defaults for missing keys.
        """
        base = cls()
        dd = dict(d or {})
        return replace(base, **{k: v for k, v in dd.items() if hasattr(base, k)})


# ------------------------- Logger options -------------------------

@dataclass(frozen=True)
class DepthsLoggerOptions:
    """
    High-level runtime knobs for the unified DepthsLogger.

    Overview (v0.2.0):
        Orchestrates lifecycle, background shipper, buffering, and the sidecars:
        - Stats (categorical & numeric generalized stats)
        - RealtimeTap (live read)
        Serialized to <instance>/configs/options.json.

    Fields:
        init_early_terminate: End __init__ early after on-disk scaffolding.
        auto_start: Start aggregators on construction.
        install_signal_handlers: Trap SIGINT/SIGTERM to stop cleanly.
        lazy_start_on_first_log: Start on first ingest if not started yet.
        atexit_hook: Attempt graceful stop during interpreter shutdown.
        min_auto_flush_wait_s / max_auto_flush_wait_s: Envelope for passive flush on stop("auto").
        producer_config: Default LogProducerConfig template (per-table override injects schema).
        aggregator_config: Default LogAggregatorConfig template (per-table override injects schema/table_path).
        shipper_enabled: Enable background day shipping to S3.
        ship_delay_after_rollover_s, verify_grace_s, verify_timeout_s, upload_max_workers: Shipper knobs.
        internal_otel_logs: Emit Depths' own logs via OTel.
        stats: StatsConfig (v0.2.0 generalized stats sidecar).
        realtime_read: RealtimeReadConfig (in-memory tails/SSE).
        add_session_context: Whether to store session identity or not.
        add_user_context: Whether to store user identity context or not.
        addons: Mapping of OTel table name → list of SchemaDelta objects to compose
                onto that table’s EventSchema at startup. Example:
                {
                    "logs": [SchemaDelta(...), ...],
                    "spans": [SchemaDelta(...)]
                }
                The valid OTel table keys are: "spans", "span_events", "span_links",
                "logs", "metrics_points", "metrics_hist".

    Defaults:
        See field defaults below; nested configs default to enabled with sane caps.
    """

    init_early_terminate: bool = False
    auto_start: bool = True
    install_signal_handlers: bool = True
    lazy_start_on_first_log: bool = True
    atexit_hook: bool = True

    min_auto_flush_wait_s: float = 0.1
    max_auto_flush_wait_s: float = 2.0

    producer_config: Optional["LogProducerConfig"] = None
    aggregator_config: Optional["LogAggregatorConfig"] = None

    shipper_enabled: bool = True
    ship_delay_after_rollover_s: float = 5.0
    verify_grace_s: int = 60
    verify_timeout_s: int = 300
    upload_max_workers: int = 8

    internal_otel_logs: bool = False

    stats: Optional[StatsConfig] = None
    realtime_read: Optional["RealtimeReadConfig"] = None

    add_session_context: bool = False
    add_user_context: bool = False

    addons: Dict[str, List[SchemaDelta]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """
        Serialize options to a JSON-safe dict (embedding nested configs).

        Returns:
            A dict suitable for `_save_json`, stable across versions.
        """

        out = {
            "auto_start": self.auto_start,
            "install_signal_handlers": self.install_signal_handlers,
            "lazy_start_on_first_log": self.lazy_start_on_first_log,
            "atexit_hook": self.atexit_hook,
            "min_auto_flush_wait_s": getattr(self, "min_auto_flush_wait_s", 0.1),
            "max_auto_flush_wait_s": getattr(self, "max_auto_flush_wait_s", 2.0),
            "shipper_enabled": self.shipper_enabled,
            "ship_delay_after_rollover_s": getattr(self, "ship_delay_after_rollover_s", 5.0),
            "verify_grace_s": getattr(self, "verify_grace_s", 60),
            "verify_timeout_s": getattr(self, "verify_timeout_s", 300),
            "upload_max_workers": getattr(self, "upload_max_workers", 8),
            "internal_otel_logs": getattr(self, "internal_otel_logs", False),

            "producer_config": (self.producer_config or LogProducerConfig()).to_dict(),
            "aggregator_config": (self.aggregator_config or LogAggregatorConfig()).to_dict(),

            "stats": (self.stats or StatsConfig()).to_dict(),
            "realtime_read": (self.realtime_read or RealtimeReadConfig()).to_dict(),

            "add_session_context": getattr(self, "add_session_context", False),
            "add_user_context": getattr(self, "add_user_context", False),

            "addons": {
                tname: [_schema_delta_to_dict(sd) for sd in (lst or [])]
                for (tname, lst) in (getattr(self, "addons", {}) or {}).items()
            },
        }
        return out

    @classmethod
    def from_dict(cls, d: dict) -> "DepthsLoggerOptions":
        """
        Reconstruct options from a JSON dict.

        Args:
            d: Parsed JSON mapping (may be partial).

        Returns:
            DepthsLoggerOptions with defaults filled for missing keys.
        """

        if d is None:
            return cls()

        dd = dict(d or {})

        pc = dd.get("producer_config")
        ac = dd.get("aggregator_config")
        st = dd.get("stats")
        rc = dd.get("realtime_read")

        if isinstance(pc, dict):
            dd["producer_config"] = LogProducerConfig.from_dict(pc)
        else:
            dd["producer_config"] = None

        if isinstance(ac, dict):
            dd["aggregator_config"] = LogAggregatorConfig.from_dict(ac)
        else:
            dd["aggregator_config"] = None

        if isinstance(st, dict):
            dd["stats"] = StatsConfig.from_dict(st)
        else:
            dd["stats"] = None

        if isinstance(rc, dict):
            dd["realtime_read"] = RealtimeReadConfig.from_dict(rc)
        else:
            dd["realtime_read"] = None

        raw_addons = dd.get("addons")
        if raw_addons is None:
            dd["addons"] = {}
        elif isinstance(raw_addons, dict):
            decoded: Dict[str, List[SchemaDelta]] = {}
            for tname, seq in raw_addons.items():
                if not isinstance(seq, list):
                    continue
                decoded[tname] = [_schema_delta_from_dict(x) for x in seq if isinstance(x, dict)]
            dd["addons"] = decoded
        else:
            dd["addons"] = {}

        base = cls()
        return replace(base, **{k: v for k, v in dd.items() if hasattr(base, k)})

    def save_to_dir(self, configs_dir: Path, filename: str = "options.json") -> None:
        """
        Persist this options object under <configs_dir>/<filename>.

        Args:
            configs_dir: Directory to hold options files.
            filename:    Name of the JSON file (default: options.json).

        Returns:
            None
        """

        configs_dir.mkdir(parents=True, exist_ok=True)
        _save_json(configs_dir / filename, self.to_dict())

    @classmethod
    def load_from_dir(cls, configs_dir: Path, filename: str = "options.json") -> "DepthsLoggerOptions | None":
        """
        Load options from <configs_dir>/<filename> if present.

        Args:
            configs_dir: Directory that contains options.json.
            filename:    Filename to read.

        Returns:
            DepthsLoggerOptions or None if missing.
        """

        p = configs_dir / filename
        if not p.exists():
            return None
        return cls.from_dict(_load_json(p))

@dataclass(frozen=True)
class S3Config:
    """
    Unified S3 configuration for both boto3 and delta-rs.

    Overview (v0.2.0 role):
        Single source of truth for S3 endpoints and credentials. Supplies:
        - boto3 client kwargs (uploads, discovery)
        - delta-rs storage_options (scan/query/rowcounts)
        Also defines the canonical S3 path layout for day roots.

    Fields:
        access_key_id, secret_key, region, url, bucket: Required cloud parameters.
        prefix: Optional key prefix (e.g., "depths-prod").
        session_token: Optional STS token for temporary creds.
    """

    access_key_id: str
    secret_key: str
    region: str
    url: str
    bucket: str
    prefix: str = ""
    session_token: str | None = None

    def to_boto3_kwargs(self) -> Dict[str, object]:
        """
        Convert to boto3.client kwargs.

        Returns:
            Dict consumable by boto3.client("s3", **kwargs).
        """

        kw: Dict[str, object] = {
            "aws_access_key_id": self.access_key_id,
            "aws_secret_access_key": self.secret_key,
        }
        if self.region:
            kw["region_name"] = self.region
        if self.session_token:
            kw["aws_session_token"] = self.session_token
        if self.url:
            kw["endpoint_url"] = self.url
        return kw

    def to_delta_storage_options(self) -> Dict[str, str]:
        """
        Convert to delta-rs storage_options.

        Returns:
            Mapping of AWS_* keys recognized by delta-rs.
        """

        opts: Dict[str, str] = {
            "AWS_ACCESS_KEY_ID": self.access_key_id,
            "AWS_SECRET_ACCESS_KEY": self.secret_key,
        }
        if self.session_token:
            opts["AWS_SESSION_TOKEN"] = self.session_token
        if self.region:
            opts["AWS_REGION"] = self.region
        if self.url:
            opts["AWS_ENDPOINT_URL"] = self.url
            if self.url.startswith("http://"):
                opts["AWS_ALLOW_HTTP"] = "true"
        return opts

    def instance_prefix(self, instance_id: str) -> str:
        """
        Compute POSIX-safe base key for an instance's day partitions.

        Args:
            instance_id: Logical Depths instance id.

        Returns:
            "<prefix>/<instance_id>/days" (without scheme/bucket).
        """

        base = self.prefix.strip("/")
        if base:
            return posixpath.join(base, instance_id, "days")
        return posixpath.join(instance_id, "days")

    def day_uri(self, instance_id: str, day: str) -> str:
        """
        Build a full S3 URI for a given UTC day.

        Args:
            instance_id: Instance id.
            day:         "YYYY-MM-DD".

        Returns:
            s3://<bucket>/<prefix>/<instance_id>/days/<day>
        """

        return f"s3://{self.bucket}/{self.instance_prefix(instance_id)}/{day}"

    @classmethod
    def from_env(cls, env: dict | None = None, *, prefix: str | None = None) -> "S3Config":
        """
        Construct S3Config from environment variables.

        Args:
            env:    Env mapping (defaults to os.environ).
            prefix: Optional uppercase prefix to namespace variables (e.g., "DEPTHS_").

        Reads (first-hit wins):
            AWS_ACCESS_KEY_ID / S3_ACCESS_KEY_ID
            AWS_SECRET_ACCESS_KEY / S3_SECRET_KEY / S3_SECRET_ACCESS_KEY
            AWS_REGION / S3_REGION
            AWS_ENDPOINT_URL / S3_URL
            S3_BUCKET (required)
            S3_PREFIX (optional)
            AWS_SESSION_TOKEN (optional)

        Returns:
            S3Config populated from the environment.
        """

        e = env if env is not None else os.environ
        p = (prefix or "").upper()

        def g(*names: str, default: str = "") -> str:
            for n in names:
                key = (p + n).upper() if p else n.upper()
                if key in e and e[key]:
                    return e[key]
            return default

        return cls(
            access_key_id=g("AWS_ACCESS_KEY_ID", "S3_ACCESS_KEY_ID"),
            secret_key=g("AWS_SECRET_ACCESS_KEY", "S3_SECRET_KEY", "S3_SECRET_ACCESS_KEY"),
            region=g("AWS_REGION", "S3_REGION"),
            url=g("AWS_ENDPOINT_URL", "S3_URL"),
            bucket=g("S3_BUCKET"),
            prefix=g("S3_PREFIX"),
            session_token=g("AWS_SESSION_TOKEN", default="") or None,
        )

@dataclass(frozen=True)
class ShipperOptions:
    """
    Tuning for verification timing and upload concurrency.

    Overview (v0.2.0 role):
        Passed to `ship_day` to tune grace/timeout and worker counts when
        uploading and verifying multi-table day partitions on S3.

    Fields:
        verify_grace_s: Wait before first remote verification attempt.
        verify_timeout_s: Max wall time for verification loop.
        upload_max_workers: Per-day upload concurrency.
        multipart_threshold_bytes: Reserved for future multipart tuning.
    """

    verify_grace_s: int = 60
    verify_timeout_s: int = 300
    upload_max_workers: int = 8
    multipart_threshold_bytes: int = 8 * 1024 * 1024

@dataclass(frozen=True)
class ManifestEntry:
    """
    One file inside a per-day manifest.

    Fields:
        relpath: POSIX path relative to the day's local root.
        kind:    'data' | 'log_checkpoint' | 'log_json' | 'last_checkpoint'
    """

    relpath: str
    kind: str

@dataclass(frozen=True)
class Manifest:
    """
    Whole-day manifest (flat listing) – primarily diagnostic.

    Fields:
        day:        "YYYY-MM-DD".
        local_root: Absolute path to local day root.
        entries:    List of ManifestEntry items.
    """

    day: str
    local_root: str
    entries: List[ManifestEntry]

@dataclass(frozen=True)
class TableManifest:
    """
    Files for a SINGLE Delta table within a day.

    Fields:
        table_relpath: e.g., "otel/spans" relative to the day root.
        data:           Parquet data file relpaths (no _delta_log).
        log_checkpoints:Checkpoint Parquet relpaths under _delta_log.
        log_jsons:      Commit JSON relpaths under _delta_log.
        last_checkpoint:Optional relpath to _last_checkpoint file.
    """

    table_relpath: str
    data: List[str]
    log_checkpoints: List[str]
    log_jsons: List[str]
    last_checkpoint: Optional[str]

@dataclass(frozen=True)
class SealTable:
    """
    Seal statistics for one table.

    Fields:
        table_relpath: Relative path (e.g., "otel/spans").
        rowcount:      Local rowcount after compaction.
        version:       Delta log version after checkpoint (if available).
    """

    table_relpath: str
    rowcount: int
    version: Optional[int]

@dataclass(frozen=True)
class SealResult:
    """
    Aggregated seal statistics for the whole day (multi-table).

    Fields:
        day:            "YYYY-MM-DD".
        local_rowcount: Sum of rowcounts across all tables.
        local_version:  Max version observed (heuristic); may be None.
        tables:         Per-table SealTable details.
    """

    day: str
    local_rowcount: int
    local_version: Optional[int]
    tables: List[SealTable] = field(default_factory=list)

@dataclass(frozen=True)
class UploadReport:
    """
    Summary of an upload thread for a single table.

    Fields:
        uploaded: Count of files successfully uploaded.
        skipped:  Count of skipped files (reserved).
        errors:   Text errors captured during upload.
    """

    uploaded: int
    skipped: int
    errors: List[str]

@dataclass(frozen=True)
class VerifyResult:
    """
    Result of remote verification against S3 for the day.

    Fields:
        ok:             True when remote rowcount matches local rowcount.
        remote_rowcount:Summed rowcount across discovered remote tables.
        remote_version: Reserved for single-table legacy paths; None in v0.2.0.
        retries:        Attempts performed in the verify loop.
        remote_tables:  Optional per-table remote rowcounts for diagnostics.
    """

    ok: bool
    remote_rowcount: int
    remote_version: Optional[int]
    retries: int
    remote_tables: Optional[List[SealTable]] = None

@dataclass(frozen=True)
class LogProducerConfig:
    """
    Validation, normalization, and buffering policy for a LogProducer.

    Overview (v0.2.0 role):
        Governs schema enforcement (required/extra/types), JSON serialization,
        OTel id/service_name normalization, and enqueue behavior. A table-specific
        schema is injected at runtime by DepthsLogger.

    Fields (highlights):
        schema: EventSchema injected per OTel table.
        max_queue_size: Producer buffer capacity.
        drop_policy: "block" | "drop_new" | "drop_old".
        validate_required/types/json_fields/date_coherence: Validation toggles.
        enforce_extra_policy: error|strip|keep (driven by schema.extra_policy).
        serialize_json_fields: To JSON for schema.json_fields.
        normalize_service_name/default_service_name: Ensures partition-safe value.
        normalize_otlp_ids/enforce_otlp_id_lengths: Lower-hex + expected lengths.
        audit_rejects: Ring size for recent rejection reasons (debugging).
    """

    schema: EventSchema = LOG_SCHEMA

    max_queue_size: int = 10_000
    drop_policy: Literal["block", "drop_new", "drop_old"] = "drop_old"

    validate_required: bool = True
    validate_types: bool = True
    validate_json_fields: bool = True
    validate_date_coherence: bool = True
    enforce_extra_policy: bool = True

    serialize_json_fields: bool = True

    normalize_service_name: bool = True
    default_service_name: str = "unknown"
    normalize_otlp_ids: bool = True
    enforce_otlp_id_lengths: bool = True

    audit_rejects: int = 200

    @classmethod
    def from_env(cls, env: dict) -> "LogProducerConfig":
        """
        Build a config from environment variables (placeholder hook).

        Args:
            env: Mapping of env vars.

        Returns:
            LogProducerConfig instance. (v0.2.0 returns defaults.)
        """

        return cls()

    def to_dict(self) -> dict:
        """
        Serialize to a portable dict (schema omitted on purpose).

        Returns:
            Dict without the `schema` field.
        """

        d = asdict(self)
        d.pop("schema", None)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "LogProducerConfig":
        """
        Rehydrate from a dict produced by `to_dict`.

        Args:
            d: Portable dict (without `schema`).

        Returns:
            LogProducerConfig, ready for `.override(schema=...)`.
        """

        dd = dict(d or {})
        dd.pop("schema", None)
        return replace(cls(), **dd)

    def override(self, **kw) -> "LogProducerConfig":
        """
        Return a copy with selected fields replaced.

        Args:
            **kw: Field overrides (e.g., schema=SPAN_SCHEMA).

        Returns:
            New LogProducerConfig.
        """

        return replace(self, **kw)

@dataclass
class ProducerMetrics:
    """
    Minimal counters for ingestion outcomes.

    Fields:
        accepted:               Number of events admitted to the buffer.
        rejected_schema:        Rejects due to required/type/extra policy.
        rejected_payload_json:  Rejects due to JSON serialization/validation.
        rejected_date_mismatch: Rejects due to event_date checks.
        dropped_capacity:       Events dropped due to buffer pressure.
    """

    accepted: int = 0
    rejected_schema: int = 0
    rejected_payload_json: int = 0
    rejected_date_mismatch: int = 0
    dropped_capacity: int = 0

@dataclass(frozen=True)
class LogAggregatorConfig:
    """
    Polling, batching, and Delta write policy for LogAggregator.

    Overview (v0.2.0 role):
        Drives when/what the aggregator drains from a producer and how it
        writes into Delta (init vs flush modes), including partition layout.

    Fields (highlights):
        schema:          EventSchema injected per table.
        max_age_s, near_full_ratio, poll_interval_s, quiet_flush_s: Poll triggers.
        min_batch_rows, max_batch_rows, strict_df: Batch & DataFrame construction.
        table_path:      Local/S3-resolved at runtime per UTC day.
        partition_by:    OTel-native partitions (project_id/service_name/schema_version).
        initialize_table:Create table on start with empty schema-only frame.
        delta_write_mode_init / _flush: Modes for initial create and appends.
        delta_write_options: Passed to polars.write_delta/delta-rs.
        writer_queue_maxsize: Backpressure between poller and writer.
    """

    schema: EventSchema = LOG_SCHEMA

    max_age_s: float = 5.0
    near_full_ratio: float = 0.75
    poll_interval_s: float = 0.05
    quiet_flush_s: float | None = None

    min_batch_rows: int = 1
    max_batch_rows: int | None = 5000
    strict_df: bool = True

    table_path: str = "./depths_logs"

    partition_by: List[str] = field(default_factory=lambda: ["project_id", "service_name", "schema_version"])

    initialize_table: bool = True
    delta_write_mode_init: Literal["ignore", "error", "overwrite", "append"] = "ignore"
    delta_write_mode_flush: Literal["append", "error", "overwrite", "ignore"] = "append"
    delta_write_options: Dict[str, object] = field(default_factory=dict)

    writer_queue_maxsize: int = 8

    @classmethod
    def from_env(cls, env: dict) -> "LogAggregatorConfig":
        """
        Build a config from environment variables (placeholder hook, yet to be implemented).

        Args:
            env: Mapping of env vars.

        Returns:
            LogAggregatorConfig instance. (v0.2.0 returns defaults.)
        """

        return cls()

    def to_dict(self) -> dict:
        """
        Serialize to a portable dict (omit runtime-bound fields).

        Returns:
            Dict without `schema` and `table_path`.
        """

        d = asdict(self)
        d.pop("schema", None)
        d.pop("table_path", None)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "LogAggregatorConfig":
        """
        Rehydrate from a dict produced by `to_dict`.

        Args:
            d: Portable dict (without `schema`/`table_path`).

        Returns:
            LogAggregatorConfig; attach schema/table_path via `.override(...)`.
        """

        dd = dict(d or {})
        dd.pop("schema", None)
        dd.pop("table_path", None)
        return replace(cls(), **dd)

    def override(self, **kw) -> "LogAggregatorConfig":
        """
        Return a copy with selected fields replaced.

        Args:
            **kw: Field overrides (e.g., schema=LOG_SCHEMA, table_path="...").

        Returns:
            New LogAggregatorConfig.
        """

        return replace(self, **kw)

class AggregatorMetrics:
    """
    Runtime counters for the aggregator & writer.

    Overview (v0.2.0 role):
        Exposed via DepthsLogger.metrics() and /healthz for quick observability.

    Fields:
        flushes:               Number of flush cycles scheduled.
        rows_scheduled_total:  Total rows sent to writer queue.
        rows_last_flush:       Rows in the most recent scheduled batch.
        last_flush_ts/mono:    Wall-clock & monotonic timestamps of last schedule.
        skipped_empty:         Count of empty drains.
        rows_persisted_total:  Rows successfully written to Delta.
        last_commit_seconds:   Duration of most recent write.
        delta_init_ok:         Whether initial table create succeeded.
        delta_last_error:      Last error text from Delta write paths.
        writer_queue_size:     Current writer queue depth.
    """

    __slots__ = (
        "flushes", "rows_scheduled_total", "rows_last_flush",
        "last_flush_ts", "last_flush_mono", "skipped_empty",
        "rows_persisted_total", "last_commit_seconds",
        "delta_init_ok", "delta_last_error",
        "writer_queue_size",
    )
    def __init__(self) -> None:
        self.flushes = 0
        self.rows_scheduled_total = 0
        self.rows_last_flush: int = 0
        self.last_flush_ts: Optional[float] = None
        self.last_flush_mono: Optional[float] = None
        self.skipped_empty = 0
        self.rows_persisted_total = 0
        self.last_commit_seconds: Optional[float] = None
        self.delta_init_ok = False
        self.delta_last_error: Optional[str] = None
        self.writer_queue_size = 0

# --------------------------------------------------------------------
# Legacy (v0.1.x) sidecar config retained for now (not referenced in v0.2.0)
# --------------------------------------------------------------------

@dataclass(frozen=True)
class StatsRollupConfig:
    """
    Minute-wise stats rollup settings for StatsRollup (views.py).

    This legacy sidecar is superseded by `Stats` in v0.2.0. Retained here
    only to avoid import churn during the migration of other modules.
    """

    enabled: bool = True
    bucket_seconds: int = 60
    allowed_lateness_s: int = 15
    optimize_frequency: int = 10

    @classmethod
    def from_env(cls, env: dict | None = None) -> "StatsRollupConfig":
        return cls()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "StatsRollupConfig":
        base = cls()
        dd = dict(d or {})
        return replace(base, **{k: v for k, v in dd.items() if hasattr(base, k)})

@dataclass(frozen=True)
class RealtimeReadConfig:
    """
    In-memory realtime read path settings for RealtimeTap (views.py).

    Overview (v0.2.0 role):
        Caps in-memory FIFO deques for traces/logs/metrics, and controls the
        drop policy under pressure.

    Fields:
        enabled: Whether RealtimeTap is active.
        max_traces: Max items to retain in the traces deque.
        max_logs: Max items to retain in the logs deque.
        max_metrics: Max items to retain in the metrics deque.
        drop_policy: Drop strategy when full (v0.1.2 fixed to "drop_old").

    Defaults:
        enabled=True, max_*=2000, drop_policy="drop_old"
    """

    enabled: bool = True
    max_traces: int = 2000
    max_logs: int = 2000
    max_metrics: int = 2000
    drop_policy: Literal["drop_old"] = "drop_old"

    @classmethod
    def from_env(cls, env: dict | None = None) -> "RealtimeReadConfig":
        return cls()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "RealtimeReadConfig":
        base = cls()
        dd = dict(d or {})
        return replace(base, **{k: v for k, v in dd.items() if hasattr(base, k)})
