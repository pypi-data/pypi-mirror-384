"""
======================================================================
(A) FILE PATH & IMPORT PATH
depths/core/shipper.py  →  import path: depths.core.shipper
======================================================================

======================================================================
(B) FILE OVERVIEW (concept & significance in v0.1.2)
Seals, uploads, verifies, and (optionally) cleans a *UTC day* of data.
A day contains the six OTel Delta tables under:
  <instance_root>/staging/days/<YYYY-MM-DD>/otel/<table>/

Pipeline for ship_day(...):
  1) Seal: optimize + checkpoint + vacuum each nested Delta table; compute
     per-table rowcounts/versions and the day’s totals.
  2) Build per-table manifests: strict upload order
        data → _delta_log/*.checkpoint.parquet → _delta_log/*.json → _last_checkpoint
  3) Upload to S3 (per-table threads).
  4) Verify by summing remote rowcounts across all discovered tables on S3.
  5) On match, cleanup the local day directory.

Throughout, append small JSON records to <instance_root>/index/{days.jsonl,day.json}
describing the “sealed”, “uploaded”, “verified”, and “cleaned” phases.
======================================================================

======================================================================
(C) IMPORTS & GLOBALS (what & why)
json, os, posixpath, shutil, time, threading, Path → I/O, key construction,
  cleanup, concurrency.
depths.core.config → typed options and small value-objects for S3 and results.
depths.io.delta → optimize(), count_rows(), delta_version() for sealing + stats.
boto3/BotoConfig (optional) → S3 uploads and list operations.
Globals: none (boto3/BotoConfig may be None when not installed).
======================================================================
"""

from __future__ import annotations

import json, os, posixpath, shutil, time, threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

from depths.core.config import (
    _save_json, _load_json, S3Config, ShipperOptions,
    Manifest, ManifestEntry, SealResult, UploadReport, VerifyResult,
    TableManifest, SealTable,
)
from depths.io.delta import optimize, count_rows, delta_version

try:
    import boto3
    from botocore.config import Config as BotoConfig
except Exception:
    boto3 = None
    BotoConfig = None


def _is_checkpoint_file(p: Path) -> bool:
    """
    Return True if the path looks like a Delta JSON checkpoint parquet.

    Overview (v0.1.2 role):
        Used while building per-table manifests to group checkpoint parquet files
        under _delta_log. This keeps upload ordering correct for Delta readers.

    Args:
        p: Candidate file path under a table's _delta_log directory.

    Returns:
        True if it matches Delta checkpoint parquet naming; False otherwise.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Accepts both canonical "<ver>.checkpoint.parquet" and
    #   "<ver>.<N>.checkpoint.parquet" patterns observed in the wild.

    name = p.name
    return name.endswith(".checkpoint.parquet") or (".checkpoint." in name and name.endswith(".parquet"))

def _discover_delta_tables_local(day_root: Path) -> List[Path]:
    """
    Find all nested Delta table roots under a local day directory.

    Overview (v0.1.2 role):
        Scans <day_root> recursively for directories containing a _delta_log
        subdirectory, returning each table root. Deterministic order.

    Args:
        day_root: Local path to the UTC day root.

    Returns:
        Sorted list of table root Paths (e.g., .../otel/logs, .../otel/spans).
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Uses rglob to handle arbitrarily nested tables.
    # - De-duplicates and sorts paths to keep uploads/verifies stable.

    out: List[Path] = []
    for log_dir in day_root.rglob("_delta_log"):
        if log_dir.is_dir():
            out.append(log_dir.parent)
    
    return sorted(set(out))

def _posix_rel(base: Path, p: Path) -> str:
    """
    Compute POSIX-style relative path from base to p.

    Args:
        base: Base directory.
        p:    Target path beneath base.

    Returns:
        Relative path using '/' separators (suitable for S3 keys).
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Normalizes os.sep differences across platforms.

    return str(p.relative_to(base)).replace(os.sep, "/")

def _table_relpath(day_root: Path, table_root: Path) -> str:
    """
    Return the per-day relative path for a table root (e.g., 'otel/spans').

    Args:
        day_root: Day directory root.
        table_root: Discovered Delta table root under the day.

    Returns:
        POSIX relative path from day_root to table_root.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Lightweight wrapper for clarity when building manifests.

    return _posix_rel(day_root, table_root)


def seal_local_day(local_day_path: str, *, storage_options: Optional[Dict[str, str]] = None) -> SealResult:
    """
    Optimize + checkpoint + vacuum all Delta tables for a given local day,
    in parallel, and compute rowcounts/versions.

    Overview (v0.1.2 role):
        Produces canonical “sealed” statistics before any upload. This ensures
        compact files, a fresh checkpoint, and stable rowcounts for verification.

    Args:
        local_day_path: Absolute path to the UTC day directory on local disk.
        storage_options: Optional delta-rs storage options (usually None for local).

    Returns:
        SealResult containing per-table SealTable entries, the total local rowcount,
        and the max observed Delta version (heuristic).
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - One thread per table to avoid blocking when many tables are present.
    # - optimize(...) runs compact + checkpoint + vacuum; failures produce
    #   zero-row entries but do not abort the whole seal step.
    # - Individual "last_ver" is not meaningful across many-table scenario likes ours; use max version observed

    day_root = Path(local_day_path)
    assert day_root.is_dir(), f"local path not found: {local_day_path}"

    tables = _discover_delta_tables_local(day_root)
    results: List[SealTable] = []
    lock = threading.Lock()

    def _seal_one(troot: Path) -> None:
        try:
            optimize(str(troot), storage_options=storage_options)
            rows = count_rows(str(troot), storage_options=storage_options)
            ver = delta_version(str(troot), storage_options=storage_options)
            rel = _table_relpath(day_root, troot)
            with lock:
                results.append(SealTable(table_relpath=rel, rowcount=rows, version=ver))
        except Exception:
            rel = _table_relpath(day_root, troot)
            with lock:
                results.append(SealTable(table_relpath=rel, rowcount=0, version=None))

    threads = [threading.Thread(target=_seal_one, args=(troot,)) for troot in tables]
    for th in threads: th.start()
    for th in threads: th.join()

    total_rows = sum(t.rowcount for t in results)
    last_ver = max((t.version for t in results if t.version is not None), default=None)
    return SealResult(day=day_root.name, local_rowcount=total_rows, local_version=last_ver, tables=sorted(results, key=lambda s: s.table_relpath))


def build_table_manifests(local_day_path: str) -> List[TableManifest]:
    """
    Construct upload manifests for each Delta table under a local day.

    Overview (v0.1.2 role):
        Groups files by *per-table* upload order required by Delta readers:
          data files → _delta_log checkpoint parquet files → _delta_log commit JSONs → _last_checkpoint

    Args:
        local_day_path: Absolute path to the UTC day directory on local disk.

    Returns:
        List of TableManifest objects, sorted by table path for deterministic uploads.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Data files exclude anything under _delta_log.
    # - _last_checkpoint is optional; include only if present.

    day_root = Path(local_day_path)
    assert day_root.is_dir(), f"local path not found: {local_day_path}"

    manifests: List[TableManifest] = []
    for troot in _discover_delta_tables_local(day_root):
        rel = _table_relpath(day_root, troot)
        data: List[str] = []
        for p in sorted(troot.rglob("*.parquet")):
            if "/_delta_log/" in _posix_rel(troot, p):
                continue
            data.append(_posix_rel(day_root, p))

        log_dir = troot / "_delta_log"
        cpts: List[str] = []
        logs: List[str] = []
        last_cp: Optional[str] = None
        if log_dir.exists() and log_dir.is_dir():
            for p in sorted(log_dir.iterdir()):
                if p.is_file() and _is_checkpoint_file(p):
                    cpts.append(_posix_rel(day_root, p))
            for p in sorted(log_dir.iterdir()):
                if p.is_file() and p.suffix == ".json":
                    logs.append(_posix_rel(day_root, p))
            lc = log_dir / "_last_checkpoint"
            if lc.exists() and lc.is_file():
                last_cp = _posix_rel(day_root, lc)

        manifests.append(TableManifest(
            table_relpath=rel,
            data=data,
            log_checkpoints=cpts,
            log_jsons=logs,
            last_checkpoint=last_cp,
        ))

    return sorted(manifests, key=lambda m: m.table_relpath)


def _mk_s3_client(s3: S3Config):
    """
    Create a boto3 S3 client from S3Config (with resilient retry policy).

    Args:
        s3: S3 configuration (endpoint/region/creds).

    Returns:
        boto3 S3 client.

    Raises:
        RuntimeError: If boto3 is not installed/available.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Attaches botocore Config(retries=standard, max_attempts=8) when available.
    # - Supports custom endpoints (MinIO/DO Spaces) via S3Config.to_boto3_kwargs().

    if boto3 is None:
        raise RuntimeError("boto3 not installed; cannot ship to S3")
    kwargs = s3.to_boto3_kwargs()
    if BotoConfig:
        kwargs["config"] = BotoConfig(retries={"max_attempts": 8, "mode": "standard"})
    return boto3.client("s3", **kwargs)

def _s3_key_for_entry(instance_prefix: str, day: str, relpath: str) -> str:
    """
    Build the S3 object key for a file under a day.

    Args:
        instance_prefix: Prefix from S3Config.instance_prefix(instance_id).
        day:             UTC day ('YYYY-MM-DD').
        relpath:         POSIX relative path (from day root) for the file.

    Returns:
        POSIX S3 key "<instance_prefix>/<day>/<relpath>".
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Ensures backslashes are normalized (Windows paths).

    return posixpath.join(instance_prefix, day, relpath.replace("\\", "/"))


def _upload_one_table(
    table: TableManifest, *, day: str, local_day_root: Path, bucket: str, instance_prefix: str, s3_client
) -> UploadReport:
    """
    Upload one table’s files to S3 in the strict Delta-safe order.

    Overview (v0.1.2 role):
        Executed in parallel across tables. Each table uploads:
          1) data files
          2) checkpoint parquet files
          3) commit JSON files
          4) _last_checkpoint (if any)

    Args:
        table:           Manifest for a single table.
        day:             UTC day ('YYYY-MM-DD').
        local_day_root:  Local day root directory.
        bucket:          Destination S3 bucket name.
        instance_prefix: S3 key prefix for the instance’s /days subtree.
        s3_client:       boto3 S3 client.

    Returns:
        UploadReport with counts and per-file error strings (if any).
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - A single failed put is recorded in errors but does not short-circuit
    #   the table; ship_day() aggregates errors and decides overall outcome.
    # - Order per table: data -> checkpoints -> commit jsons -> _last_checkpoint
    
    uploaded = 0
    skipped = 0
    errors: List[str] = []

    def _put(rel: str) -> None:
        nonlocal uploaded, skipped
        local_file = local_day_root / rel
        key = _s3_key_for_entry(instance_prefix, day, rel)
        try:
            s3_client.upload_file(str(local_file), bucket, key)
            uploaded += 1
        except Exception as e:
            errors.append(f"{table.table_relpath}:{rel}: {e!r}")

    
    for rel in table.data: _put(rel)
    for rel in table.log_checkpoints: _put(rel)
    for rel in table.log_jsons: _put(rel)
    if table.last_checkpoint: _put(table.last_checkpoint)

    return UploadReport(uploaded=uploaded, skipped=skipped, errors=errors)


def _list_s3_keys(s3_client, bucket: str, prefix: str) -> List[str]:
    """
    List all S3 object keys under a prefix (automatic pagination).

    Args:
        s3_client: boto3 S3 client.
        bucket:    Bucket name.
        prefix:    Key prefix to list.

    Returns:
        Flat list of keys under the prefix.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Uses ListObjectsV2 with NextContinuationToken loop.

    out: List[str] = []
    token = None
    while True:
        kw = dict(Bucket=bucket, Prefix=prefix)
        if token: kw["ContinuationToken"] = token
        resp = s3_client.list_objects_v2(**kw)
        for it in resp.get("Contents", []):
            out.append(it["Key"])
        token = resp.get("NextContinuationToken")
        if not token: break
    return out

def _discover_delta_tables_s3(s3: S3Config, s3_client, instance_id: str, day: str) -> List[str]:
    """
    Discover Delta table *root URIs* on S3 under a given day prefix.

    Overview (v0.1.2 role):
        Identifies table roots by detecting either:
          • presence of '_delta_log/_last_checkpoint', or
          • any '_delta_log/*.json' commit files.
        Returns URIs like 's3://bucket/.../days/<day>/otel/<table>'.

    Args:
        s3:          S3 configuration.
        s3_client:   boto3 client.
        instance_id: Instance id (to construct the base day prefix).
        day:         UTC day ('YYYY-MM-DD').

    Returns:
        Sorted list of unique S3 URIs to table roots.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Supports both: (a) instance_id combined with s3.prefix, and
    #   (b) pre-expanded '.../days' in s3.prefix with empty instance_id.

    base = s3.instance_prefix(instance_id) if instance_id else s3.prefix.strip("/")
    day_prefix = posixpath.join(base, day).rstrip("/") + "/"
    client = s3_client
    keys = _list_s3_keys(client, s3.bucket, day_prefix)
    roots: Set[str] = set()
    for k in keys:
        if k.endswith("/_delta_log/_last_checkpoint") or ("/_delta_log/" in k and k.endswith(".json")):
            root = "s3://" + s3.bucket + "/" + k.split("/_delta_log/")[0]
            roots.add(root)
    return sorted(roots)

def _relpath_from_s3_root_uri(day: str, table_root_uri: str) -> str:
    """
    Convert a table root S3 URI into a day-relative path (e.g., 'otel/spans').

    Args:
        day:            UTC day ('YYYY-MM-DD').
        table_root_uri: 's3://<bucket>/<...>/days/<day>/<rel>'.

    Returns:
        '<rel>' portion relative to '/days/<day>/'.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Falls back to the last one or two segments if '/days/<day>/' is missing.

    assert table_root_uri.startswith("s3://")
    _, _, rest = table_root_uri.partition("s3://")
    _, _, path = rest.partition("/") 
    marker = f"/days/{day}/"
    idx = path.find(marker)
    if idx == -1:
        parts = path.strip("/").split("/")
        return "/".join(parts[-2:]) if len(parts) >= 2 else parts[-1]
    return path[idx + len(marker):]


def compute_rowcount_local(local_day_path: str, *, storage_options: Optional[Dict[str, str]] = None) -> int:
    """
    Sum rowcounts across all Delta tables under a local day directory.

    Args:
        local_day_path: Absolute path to the UTC day directory.
        storage_options: Optional delta-rs storage options.

    Returns:
        Integer total of local rowcounts across discovered tables.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Uses count_rows(...) from depths.io.delta for each table root.

    day_root = Path(local_day_path)
    total = 0
    for t in _discover_delta_tables_local(day_root):
        total += count_rows(str(t), storage_options=storage_options)
    return total


def verify_remote(
    s3: S3Config,
    instance_id: str,
    day: str,
    expected_rows: int,
    *,
    grace_s: int = 60,
    timeout_s: int = 300,
    storage_options: Optional[Dict[str, str]] = None,
) -> VerifyResult:
    """
    Verify that the remote S3 copy matches the local sealed rowcount.

    Overview (v0.1.2 role):
        After uploads, repeatedly discover all table roots under the day prefix
        and sum their rowcounts using delta-rs until either:
          • total == expected_rows (success), or
          • timeout is reached (failure).

    Args:
        s3:            S3 configuration (used for both discovery and rowcount reads).
        instance_id:   Instance id (forms the '/days/<day>/' prefix).
        day:           UTC day ('YYYY-MM-DD').
        expected_rows: Rowcount produced by seal_local_day(...).
        grace_s:       Initial sleep before first verify attempt (allow S3 list consistency).
        timeout_s:     Maximum wall-clock seconds to keep retrying.
        storage_options: Optional delta-rs storage options.

    Returns:
        VerifyResult with ok flag, remote rowcount, retries count, and optional
        per-table remote rowcounts for diagnostics.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Backoff: min(2 + retries*0.5, 10.0) between attempts.
    # - We treat exceptions during list/read as transient and keep retrying until timeout.

    client = _mk_s3_client(s3)

    if grace_s > 0:
        time.sleep(grace_s)

    start = time.time()
    retries = 0
    while True:
        try:
            roots = _discover_delta_tables_s3(s3, client, instance_id, day)
            total = 0
            per_table: List[SealTable] = []
            for r in roots:
                rc = count_rows(r, storage_options=storage_options)
                total += rc
                rel = _relpath_from_s3_root_uri(day, r)
                per_table.append(SealTable(table_relpath=rel, rowcount=rc, version=None))
            if total == expected_rows:
                return VerifyResult(ok=True, remote_rowcount=total, remote_version=None, retries=retries, remote_tables=sorted(per_table, key=lambda s: s.table_relpath))
        except Exception:
            pass
        retries += 1
        if time.time() - start > timeout_s:
            return VerifyResult(ok=False, remote_rowcount=-1, remote_version=None, retries=retries, remote_tables=None)
        time.sleep(min(2 + retries * 0.5, 10.0))


def append_index_record(instance_root: str, record: Dict) -> None:
    """
    Append a small JSON record for the day’s shipping phase into index files.

    Overview (v0.1.2 role):
        Writes a JSONL line to <instance_root>/index/days.jsonl and maintains
        a JSON snapshot at <instance_root>/index/day.json for quick inspection.

    Args:
        instance_root: Base directory for the Depths instance.
        record:        JSON-serializable mapping to append.

    Returns:
        None
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Keeps JSON stable by routing through _save_json for the snapshot.
    # - Swallows decode errors for an existing snapshot and recreates it.

    index_dir = Path(instance_root) / "index"
    jsonl = index_dir / "days.jsonl"
    snap = index_dir / "day.json"
    index_dir.mkdir(parents=True, exist_ok=True)
    with open(jsonl, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")
    try:
        import json as _json
        arr = _json.loads(snap.read_text())
    except Exception:
        arr = []
    arr.append(record)
    _save_json(snap, arr)


def cleanup_local_day(local_day_path: str) -> None:
    """
    Delete a local day directory tree (best-effort).

    Args:
        local_day_path: Absolute path to the local day directory.

    Returns:
        None
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Used after successful verify to reclaim disk space.
    # - Missing path is a no-op.

    p = Path(local_day_path)
    if p.exists() and p.is_dir():
        shutil.rmtree(p)


def ship_day(
    *, instance_id: str, instance_root: str, day: str, local_day_path: str, s3: S3Config, opts: Optional[ShipperOptions] = None,
) -> Dict:
    """
    End-to-end shipping of a UTC day: seal → upload → verify → cleanup.

    Overview (v0.1.2 role):
        Orchestrates the full multi-table S3 transfer for a completed day.
        Emits phase records to the instance index and returns a compact result.

    Args:
        instance_id:     Logical instance identifier.
        instance_root:   Filesystem root of the instance.
        day:             UTC day ('YYYY-MM-DD') to ship (must NOT be today's day).
        local_day_path:  Absolute local path to the day directory.
        s3:              S3 configuration.
        opts:            ShipperOptions tuning for verify delays and concurrency.

    Returns:
        Dict with:
          - day
          - local_rows, local_version (from sealing)
          - verified (bool), remote_rows, remote_version
          - upload_errors (list)
          - total_s (float) wall-clock seconds

    Raises:
        RuntimeError: If S3 client cannot be constructed (boto3 missing).
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Uploads are parallelized per table (1 thread per table). Within a table,
    #   order is strict: data → checkpoints → JSONs → _last_checkpoint.
    # - Any upload error short-circuits verification/cleanup; details appear in
    #   'upload_errors' and are also recorded in the index “uploaded/verified” phases.
    # - Verification uses the *original* S3Config (not public URIs) to read counts.

    opts = opts or ShipperOptions()
    t0 = time.time()

    seal = seal_local_day(local_day_path)
    append_index_record(instance_root, {
        "instance_id": instance_id, "day": day, "phase": "sealed",
        "local": {
            "rows": seal.local_rowcount, "version": seal.local_version,
            "tables": [{"name": t.table_relpath, "rows": t.rowcount, "ver": t.version} for t in seal.tables],
        },
        "when_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })

    local_root = Path(local_day_path)
    manis = build_table_manifests(local_day_path)
    client = _mk_s3_client(s3)
    s3_instance_prefix = s3.instance_prefix(instance_id)

    upload_reports: List[UploadReport] = []
    errors: List[str] = []
    threads: List[threading.Thread] = []

    def _upload_one(m: TableManifest) -> None:
        rep = _upload_one_table(m, day=day, local_day_root=local_root, bucket=s3.bucket, instance_prefix=s3_instance_prefix, s3_client=client)
        upload_reports.append(rep)
        if rep.errors:
            errors.extend(rep.errors)

    for m in manis:
        th = threading.Thread(target=_upload_one, args=(m,))
        th.start()
        threads.append(th)
    for th in threads: th.join()

    total_uploaded = sum(r.uploaded for r in upload_reports)
    total_skipped = sum(r.skipped for r in upload_reports)

    append_index_record(instance_root, {
        "instance_id": instance_id, "day": day, "phase": "uploaded",
        "upload": {"uploaded": total_uploaded, "skipped": total_skipped, "errors": errors[:3], "tables": [m.table_relpath for m in manis]},
        "when_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })

    if errors:
        append_index_record(instance_root, {
            "instance_id": instance_id, "day": day, "phase": "verified",
            "ok": False, "reason": "upload_errors",
            "remote": {"rows": None, "version": None},
            "when_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        return {
            "day": day,
            "local_rows": seal.local_rowcount, "local_version": seal.local_version,
            "verified": False, "remote_rows": None, "remote_version": None,
            "upload_errors": errors, "total_s": time.time() - t0,
        }

    ver = verify_remote(
        s3, instance_id, day,
        expected_rows=seal.local_rowcount,
        grace_s=opts.verify_grace_s,
        timeout_s=opts.verify_timeout_s,
        storage_options=s3.to_delta_storage_options(),
    )

    append_index_record(instance_root, {
        "instance_id": instance_id, "day": day, "phase": "verified",
        "remote": {
            "rows": ver.remote_rowcount, "version": ver.remote_version,
            "tables": [{"name": t.table_relpath, "rows": t.rowcount} for t in (ver.remote_tables or [])],
        },
        "ok": ver.ok, "retries": ver.retries,
        "when_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })

    if ver.ok and ver.remote_rowcount == seal.local_rowcount:
        cleanup_local_day(local_day_path)
        append_index_record(instance_root, {
            "instance_id": instance_id, "day": day, "phase": "cleaned",
            "when_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })

    return {
        "day": day,
        "local_rows": seal.local_rowcount, "local_version": seal.local_version,
        "verified": ver.ok, "remote_rows": ver.remote_rowcount, "remote_version": ver.remote_version,
        "upload_errors": [], "total_s": time.time() - t0,
    }
