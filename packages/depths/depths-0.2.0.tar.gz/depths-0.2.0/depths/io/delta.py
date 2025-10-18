"""
======================================================================
(A) FILE PATH & IMPORT PATH
depths/io/delta.py  →  import path: depths.io.delta
======================================================================

======================================================================
(B) FILE OVERVIEW (concept & significance in v0.1.2)
Thin, pragmatic helpers around delta-rs + Polars for Delta Lake I/O.
Responsibilities:
  • Safe CREATE for empty and non-empty DataFrames (schema-only create when empty)
  • INSERT/UPSERT/DELETE via Polars' delta-merge API where available
  • READ via pl.scan_delta with robust PyArrow fallback
  • Basic table maintenance: COMPACT + CHECKPOINT + VACUUM + metadata cleanup
  • Fast rowcounts and current table version discovery

These are used by:
  - depths.core.aggregator (initial create, flush appends)
  - depths.core.shipper   (seal: compact→checkpoint→vacuum; rowcount checks)
  - depths.core.logger    (ad hoc reads for local/remote verification)

Design goals: keep behavior predictable across local FS and S3, be resilient
to environment quirks (Arrow/FFI), and provide minimal retries where I/O can
be transient.
======================================================================

======================================================================
(C) IMPORTS & GLOBALS (what & why)
polars as pl              → DataFrame/LazyFrame I/O to Delta
deltalake.DeltaTable      → management ops (optimize, vacuum, checkpoint)
deltalake.exceptions      → precise error raising on read/create failures
time                      → tiny linear backoff between retries
typing                    → clear signatures for storage options & filters

Globals:
  NUM_RETRIES = 3          → default retry budget for I/O operations
  NO_HISTORY               → Delta configuration to shorten log/file retention
                             on write paths (keeps test/dev footprints small)
  RUST_LOG="error"         → suppress noisy delta-rs logs by default
======================================================================
"""

import os
os.environ["RUST_LOG"] = "error"

import polars as pl
from deltalake import DeltaTable
from deltalake.exceptions import DeltaError, TableNotFoundError
import time
from typing import Optional, List, Dict, Any, Tuple

NUM_RETRIES = 3
NO_HISTORY = {
    "delta.logRetentionDuration": "interval 0 days",
    "delta.deletedFileRetentionDuration": "interval 0 days",
}

def _sanitize_lists_for_delta(df: pl.DataFrame) -> pl.DataFrame:
    """
    Normalize list-typed columns so empty lists become NULLs.

    Overview (v0.1.2 role):
        Avoids Arrow/FFI alignment panics observed when writing DataFrames
        that contain [] in List columns. Preserves dtype and leaves non-empty
        lists untouched.

    Args:
        df: Input Polars DataFrame.

    Returns:
        A DataFrame where cells equal to [] in List columns are replaced with
        nulls of the same list dtype.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Only transforms cells with length==0; does not coerce scalar types.
    # - Keep this small and pure; writing functions call it just-in-time.

    list_cols = [name for name, dt in zip(df.columns, df.dtypes) if isinstance(dt, pl.List)]
    if not list_cols:
        return df
    exprs = []
    for name, dt in zip(df.columns, df.dtypes):
        if isinstance(dt, pl.List):
            exprs.append(
                pl.when(pl.col(name).list.lengths() == 0)
                  .then(pl.lit(None).cast(dt))
                  .otherwise(pl.col(name))
                  .alias(name)
            )
        else:
            exprs.append(pl.col(name))
    return df.select(exprs)

def create_delta(
    table_path: str,
    data: pl.DataFrame,
    mode: str = "ignore",
    num_retries: int = NUM_RETRIES,
    storage_options: Optional[Dict[str, str]] = None,
    partition_by: Optional[List[str]] = None,
    partition_filters: Optional[List[Tuple[str, str, Any]]] = None,  # unused on create
    delta_write_options: Optional[Dict[str, Any]] = None,
):
    """
    Create a Delta table at `table_path`.

    Overview (v0.1.2 role):
        Used by Aggregator on first touch of a table (or day partition). If the
        provided frame is empty, this writes a *schema-only* Delta table (via
        DeltaTable.create with a PyArrow schema derived from Polars). If the
        frame is non-empty, it writes through Polars, after sanitizing list
        columns.

    Args:
        table_path: Local path or S3 URI to the table root.
        data: Polars DataFrame to use for schema (and initial rows if non-empty).
        mode: Delta write/create mode ('error' | 'append' | 'overwrite' | 'ignore').
        num_retries: Retry attempts on transient errors.
        storage_options: delta-rs storage options (S3 creds, endpoints, etc.).
        partition_by: Optional partition columns to register on create.
        partition_filters: Unused during create; kept for symmetry.
        delta_write_options: Extra write options passed to Polars/delta-rs.

    Returns:
        None (raises on final failure).
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - For empty frames we call DeltaTable.create(...) to ensure a valid
    #   _delta_log entry exists without invoking data writes.
    # - We merge NO_HISTORY into write configuration to keep logs/files short-
    #   lived since tables are day-spanned by design.
    # - Linear backoff: (attempt+1)*0.1s.

    write_opts = dict(delta_write_options or {})
    if partition_by:
        write_opts["partition_by"] = partition_by
    if partition_filters:
        write_opts["partition_filters"] = partition_filters
    cfg: Dict[str, str] = {**NO_HISTORY, **write_opts.get("configuration", {})}
    write_opts["configuration"] = cfg

    for attempt in range(num_retries):
        try:
            if data.height == 0:
                import pyarrow as pa
                pa_schema: pa.Schema = data.to_arrow().schema

                DeltaTable.create(
                    table_uri=table_path,
                    schema=pa_schema,
                    mode=mode,  
                    partition_by=partition_by,
                    configuration=cfg,
                    storage_options=storage_options,
                )
                return

            safe_df = _sanitize_lists_for_delta(data)
            safe_df.write_delta(
                table_path,
                mode=mode,
                storage_options=storage_options,
                delta_write_options=write_opts,
            )
            return

        except Exception as e:
            if attempt == num_retries - 1:
                raise e
            time.sleep((attempt + 1) * 0.1)

def read_delta(
    table_path: str,
    storage_options: Optional[Dict[str, str]] = None,
    partitions: Optional[List[Tuple[str, str, Any]]] = None,
    filters: Optional[Any] = None,
    return_lf: Optional[bool] = False,
) -> pl.DataFrame:
    """
    Read a Delta table via Polars; optionally return a LazyFrame.

    Overview (v0.1.2 role):
        Primary read path for Logger/CLI tooling. Uses `pl.scan_delta(...)`
        with optional PyArrow options for partitions/filters. On scan failure,
        falls back to `DeltaTable(...).to_pyarrow_table()` → `pl.from_arrow`.

    Args:
        table_path: Local path or S3 URI to the table root.
        storage_options: delta-rs storage options (S3 creds, endpoints, etc.).
        partitions: Optional partition selectors for the read.
        filters: Optional row filter expression (PyArrow-compatible).
        return_lf: If True, returns a Polars LazyFrame; else collects to DataFrame.

    Returns:
        LazyFrame (when return_lf=True) or a collected DataFrame.

    Raises:
        ValueError: When the table is not found or both paths fail.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Prefer the lazy scan for projection/predicate pushdown.
    # - The fallback path enables reading even if scan_delta lacks parity in
    #   some environments/backends.

    try:
        pyarrow_opts = None
        if partitions or filters:
            pyarrow_opts = {}
            if partitions:
                pyarrow_opts["partitions"] = partitions
            if filters:
                pyarrow_opts["filter"] = filters

        lf = pl.scan_delta(
            table_path,
            storage_options=storage_options,
            pyarrow_options=pyarrow_opts,
        )
        return lf if return_lf else lf.collect()

    except (TableNotFoundError, DeltaError):
        raise ValueError("Table not found")

    except Exception:
        try:
            dt = DeltaTable(table_path, storage_options=storage_options)
            pa_tbl = dt.to_pyarrow_table(partitions=partitions, filters=filters)
            return pl.from_arrow(pa_tbl)
        except Exception:
            raise ValueError("Failed to read table")
        
def insert_delta(
    table_path: str,
    data: pl.DataFrame,
    mode: str = "append",
    num_retries: int = NUM_RETRIES,
    storage_options: Optional[Dict[str, str]] = None,
    partition_by: Optional[List[str]] = None,
    partition_filters: Optional[List[Tuple[str, str, Any]]] = None,
    delta_write_options: Optional[Dict[str, Any]] = None,
):
    """
    Append/insert rows into an existing Delta table.

    Overview (v0.1.2 role):
        Main flush path for Aggregator. Relies on Polars' `write_delta(...)`
        and inherits table partitions from existing metadata unless overrides
        are provided.

    Args:
        table_path: Local path or S3 URI to the table root.
        data: Polars DataFrame of rows to append.
        mode: Delta write mode ('append' typical; others per delta-rs semantics).
        num_retries: Retry attempts on transient errors.
        storage_options: delta-rs storage options (S3 creds, endpoints, etc.).
        partition_by: Optional partition columns (rarely set on insert).
        partition_filters: Optional partition filters to constrain writes.
        delta_write_options: Extra write options passed to Polars/delta-rs.

    Returns:
        None (raises on final failure).
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - No-op if `data` is empty (fast-return); callers should already batch.
    # - Merges NO_HISTORY into write configuration (dev/test footprint).
    # - Linear backoff: (attempt+1)*0.1s.

    if data.height == 0:
        return
    
    write_opts = dict(delta_write_options or {})
    if partition_by:
        write_opts["partition_by"] = partition_by  #
    if partition_filters:
        write_opts["partition_filters"] = partition_filters
    cfg: Dict[str, str] = {**NO_HISTORY, **write_opts.get("configuration", {})}
    write_opts["configuration"] = cfg

    for attempt in range(num_retries):
        try:
            data.write_delta(
                table_path,
                mode=mode,
                storage_options=storage_options,
                delta_write_options=write_opts,
            )
            return
        except Exception as e:
            if attempt == num_retries - 1:
                raise e
            time.sleep((attempt + 1) * 0.1)

def update_delta(
    table_path: str,
    updates_df: pl.DataFrame,
    id_column: str,
    num_retries: int = NUM_RETRIES,
    storage_options: Optional[Dict[str, str]] = None,
    delta_merge_options: Optional[Dict[str, Any]] = None,
):
    """
    Update rows in-place using a merge-on-id strategy.

    Overview (v0.1.2 role):
        Convenience wrapper over Polars' delta-merge builder. Produces:
          predicate: "source.<id> = target.<id>"
          update set: {col: "source.col" for col in updates_df.columns}
        Then executes `.when_matched_update(...).execute()`.

    Args:
        table_path: Local path or S3 URI to the table root.
        updates_df: Polars DataFrame containing rows to apply as updates.
        id_column: Column name used to match target rows.
        num_retries: Retry attempts on transient errors.
        storage_options: delta-rs storage options (S3 creds, endpoints, etc.).
        delta_merge_options: Extra options for the underlying delta merge.

    Returns:
        None (raises on final failure).

    Raises:
        AssertionError: If `updates_df` is empty.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - We do not drop id_column from update_set; delta semantic resolves this.
    # - Callers should ensure id uniqueness within `updates_df`.
    # - Merge options can override predicate/aliases via `delta_merge_options`.

    assert updates_df.height > 0, "Data to be updated should be non-empty"

    update_set = {col: f"source.{col}" for col in updates_df.columns}
    base_opts = {
        "predicate": f"source.{id_column} = target.{id_column}",
        "source_alias": "source",
        "target_alias": "target",
    }
    if delta_merge_options:
        base_opts.update(delta_merge_options)

    for attempt in range(num_retries):
        try:
            (
                updates_df.write_delta(
                    table_path,
                    mode="merge",
                    delta_merge_options=base_opts,
                    storage_options=storage_options,
                )
                .when_matched_update(updates=update_set)
                .execute()
            )
            break
        except Exception as e:
            if attempt == num_retries - 1:
                raise e
            time.sleep((attempt + 1) * 0.1)

def delete_delta(
    table_path: str,
    ids_to_delete_df: pl.DataFrame,
    id_column: str,
    num_retries: int = NUM_RETRIES,
    storage_options: Optional[Dict[str, str]] = None,
):
    """
    Delete rows by id using a merge-based delete.

    Overview (v0.1.2 role):
        Builds a merge with predicate "source.<id> = target.<id>" and executes
        `.when_matched_delete().execute()` with `ids_to_delete_df` as source.

    Args:
        table_path: Local path or S3 URI to the table root.
        ids_to_delete_df: Single-column DataFrame listing ids to delete.
        id_column: Column name carrying the ids.
        num_retries: Retry attempts on transient errors.
        storage_options: delta-rs storage options (S3 creds, endpoints, etc.).

    Returns:
        None (raises on final failure).

    Raises:
        AssertionError: If `ids_to_delete_df` is empty.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - The source DataFrame must contain `id_column` only; extra columns are ignored.
    # - Consider batching large deletions for better Delta performance.

    assert ids_to_delete_df.height > 0, (
        "DataFrame with IDs to delete should be non-empty"
    )

    predicate = f"source.{id_column} = target.{id_column}"
    for attempt in range(num_retries):
        try:
            (
                ids_to_delete_df.write_delta(
                    table_path,
                    mode="merge",
                    delta_merge_options={
                        "predicate": predicate,
                        "source_alias": "source",
                        "target_alias": "target",
                    },
                    storage_options=storage_options,
                )
                .when_matched_delete()
                .execute()
            )
            break
        except Exception as e:
            if attempt == num_retries - 1:
                raise e
            time.sleep((attempt + 1) * 0.1)

def optimize(
    table_path: str,
    num_retries: int = NUM_RETRIES,
    dry_run: bool = False,
    retention_hours: int = 24,
    partition_filters: Optional[List[Tuple[str, str, Any]]] = None,
    storage_options: Optional[Dict[str, str]] = None,
):
    """
    Compact small files, checkpoint, and vacuum a Delta table.

    Overview (v0.1.2 role):
        Used by Shipper during the “seal” phase to produce compact files and
        a fresh checkpoint (faster remote reads), then VACUUMs unreachable
        files and performs metadata cleanup.

    Args:
        table_path: Local path or S3 URI to the table root.
        num_retries: Retry attempts on transient errors.
        dry_run: If True, VACUUM only reports deletable files (no deletions).
        retention_hours: VACUUM retention horizon (enforce_retention_duration=False).
        partition_filters: Optional compact only selected partitions.
        storage_options: delta-rs storage options (S3 creds, endpoints, etc.).

    Returns:
        None (raises on final failure).
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Implements: dt.optimize.compact(...), dt.create_checkpoint(), dt.vacuum(...),
    #   dt.cleanup_metadata().
    # - We deliberately pass enforce_retention_duration=False for dev/test; adjust
    #   for production governance as needed.

    for attempt in range(num_retries):
        try:
            dt = DeltaTable(table_path, storage_options=storage_options)

            dt.optimize.compact(partition_filters=partition_filters)
            dt.create_checkpoint()
            dt.vacuum(
                retention_hours=retention_hours,
                dry_run=dry_run,
                enforce_retention_duration=False,
            )
            dt.cleanup_metadata()
            
            break
        except Exception as e:
            if attempt == num_retries - 1:
                raise e
            time.sleep((attempt + 1) * 0.1)

def count_rows(table_path: str, storage_options: Optional[Dict[str, str]] = None) -> int:
    """
    Return the number of rows in a Delta table.

    Overview (v0.1.2 role):
        Primary rowcount primitive used by Shipper verification and quick
        diagnostics. Prefers a fast lazy scan; falls back to DeltaTable→PyArrow.

    Args:
        table_path: Local path or S3 URI to the table root.
        storage_options: delta-rs storage options (S3 creds, endpoints, etc.).

    Returns:
        Integer rowcount (raises on unrecoverable errors).
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - `pl.scan_delta(...).select(pl.len()).collect().item()` is typically fastest.
    # - Fallback keeps things working when scan/engine lacks feature parity.

    try:
        lf = pl.scan_delta(table_path, storage_options=storage_options)
        return lf.select(pl.len()).collect().item()
    except Exception:
        try:
            dt = DeltaTable(table_path, storage_options=storage_options)
            pa_tbl = dt.to_pyarrow_table()
            return pa_tbl.num_rows
        except Exception as e:
            raise e

def delta_version(table_path: str, storage_options: Optional[Dict[str, str]] = None) -> Optional[int]:
    """
    Return the current Delta log version for a table, if available.

    Overview (v0.1.2 role):
        Lightweight introspection used by seal/reporting paths to record the
        latest observed version alongside rowcount.

    Args:
        table_path: Local path or S3 URI to the table root.
        storage_options: delta-rs storage options (S3 creds, endpoints, etc.).

    Returns:
        Integer version if queryable; otherwise None.
    """
    # --- DEVELOPER NOTES -------------------------------------------------
    # - Some delta-rs versions expose .version as a property vs method; handle both.
    # - Absorb exceptions and return None for resilience in mixed environments.
    try:
        dt = DeltaTable(table_path, storage_options=storage_options)
        try:
            return int(dt.version())
        except TypeError:
            v = getattr(dt, "version", None)
            return int(v) if v is not None else None
    except Exception:
        return None