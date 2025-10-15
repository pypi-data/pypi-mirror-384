# All comments and code identifiers in English (as per your preference)
import os
import re
import tempfile
import duckdb
from duckdb import DuckDBPyConnection
from pathlib import Path
from typing import Optional, Iterable, Any, Tuple, Union
import logging

from nemo_library import NemoLibrary
from enum import Enum


from nemo_library_etl.adapter._utils.config import ConfigBase
from nemo_library_etl.adapter._utils.dbandfileutils import (
    _output_path,
)
import sqlglot


def _safe_table_name(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        s = "table"
    if s[0].isdigit():
        s = "_" + s
    return s


def _quote_ident(name: str) -> str:
    """Safely quote a SQL identifier for DuckDB (double-quote escaping)."""
    return '"' + name.replace('"', '""') + '"'


class ETLDuckDBHandler:
    """
    DuckDB helper for ingesting ETL JSONL/JSONL.GZ outputs efficiently.
    """

    def __init__(
        self,
        nl: NemoLibrary,
        cfg: ConfigBase,
        logger: Union[logging.Logger, object],
        database: Optional[str | Path] = None,
        read_only: bool = False,
        threads: Optional[int] = None,
        memory_limit: Optional[str] = None,
    ):
        """
        Args:
            database: DuckDB file path. If None, use in-memory (':memory:').
            read_only: Open the DuckDB database in read-only mode.
            threads: Optional PRAGMA threads=N.
            memory_limit: Optional PRAGMA memory_limit='XGB' (e.g., '4GB').
        """
        self.nl = nl
        self.cfg = cfg
        self.logger = logger
        db = ":memory:" if database is None else str(database)
        if db != ":memory:":
            db = Path(db)
            db.parent.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Opening DuckDB database at: {db} (read_only={read_only})")
        self.con: DuckDBPyConnection = duckdb.connect(database=db, read_only=read_only)
        # Optional performance pragmas
        if not threads:
            threads = os.cpu_count()
        if threads:
            self.con.execute(f"PRAGMA threads={int(threads)};")
        if memory_limit:
            self.con.execute(f"PRAGMA memory_limit='{memory_limit}';")

    def close(self) -> None:
        try:
            self.con.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    # --------------------------- path resolution ---------------------------

    def _resolve_jsonl_path(
        self,
        step: str | Enum,
        entity: str | Enum | None,
        filename: str | None,
        substep: Optional[str | Enum],
    ) -> Optional[Path]:
        """
        Resolve the output file path for the given ETL object.
        Tries <stem>.jsonl then <stem>.jsonl.gz and returns the first that exists.
        """
        base = _output_path(self.cfg.etl_directory, step, substep, entity, filename, "")
        candidates = [base.with_suffix(".jsonl"), base.with_suffix(".jsonl.gz")]
        for c in candidates:
            if c.exists():
                return c
        return None

    # --------------------------- public API --------------------------------

    def export_table(
        self,
        table_name: str,
        fh,  # ETLFileHandler instance
        step: str | Enum,
        entity: str | Enum | None,
        filename: str | None = None,
        substep: Optional[str | Enum] = None,
        gzip_enabled: bool = False,
        order_by: Optional[str] = None,
        chunk_rows: int = 50_000,
        newline: str = "\n",
    ) -> Tuple[Path, int]:
        """
        Export a DuckDB table to JSONL (optionally .gz) using ETLFileHandler in streaming mode.

        Args:
            table_name: Source DuckDB table to export.
            fh: ETLFileHandler instance to manage JSONL streaming and path resolution.
            adapter, step, entity, filename, substep: Passed through to ETLFileHandler to build the output path.
            gzip_enabled: If True, write .jsonl.gz, otherwise .jsonl.
            order_by: Optional ORDER BY clause (e.g. "id" or "id, created_at DESC") for deterministic output.
            chunk_rows: Number of rows to fetch per batch from DuckDB.
            newline: Newline separator (defaults to '\n').

        Returns:
            (output_path, total_rows)
        """
        if not self.table_exists(
            _safe_table_name(table_name)
        ) and not self.table_exists(table_name):
            raise ValueError(f'DuckDB table does not exist: "{table_name}"')

        # Build SELECT
        ident = (
            table_name
            if self.table_exists(table_name)
            else _safe_table_name(table_name)
        )
        sql = f"SELECT * FROM {_quote_ident(ident)}"
        if order_by:
            sql += f" ORDER BY {order_by}"

        # Prepare execution and column mapping
        res = self.con.execute(sql)
        # DuckDB exposes column names via description
        if not hasattr(res, "description") or res.description is None:
            # Force a zero-row fetch to populate description if needed
            res = self.con.execute(sql + " LIMIT 0")
        res = self.con.execute(sql)
        col_names = [
            d[0] for d in res.description
        ]  # tuples like (name, type_code, ...)

        total = 0
        # Stream writer from your ETLFileHandler determines the final path and handles gzip
        with fh.streamJSONL(
            step=step,
            entity=entity,
            filename=filename,
            gzip_enabled=gzip_enabled,
            substep=substep,
            newline=newline,
        ) as writer:
            # Fetch and write in chunks
            while True:
                rows = res.fetchmany(chunk_rows)
                if not rows:
                    break
                for row in rows:
                    # Map row tuple -> dict with column names
                    rec = {col_names[i]: row[i] for i in range(len(col_names))}
                    writer.write_one(rec, chunk_size=chunk_rows)
                    total += 1
            out_path = writer.path

        self.logger.info(
            f'Exported table "{table_name}" to JSONL at {out_path} with {total:,} records.'
        )

        # If you want the exact total without recounting during the loop (for speed),
        # you can compute it via DuckDB afterwards:
        try:
            total = int(
                self.con.execute(
                    f"SELECT COUNT(*) FROM {_quote_ident(ident)};"
                ).fetchone()[0]
            )
        except Exception:
            # Fallback: total remains as counted (0 if loop avoided counting)
            pass

        return out_path, total

    # --------------------------- helpers -----------------------------------

    def table_exists(self, name: str) -> bool:
        q = self.con.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?;",
            [name],
        ).fetchone()[0]
        return q > 0

    def count_rows(self, name: str) -> int:
        return int(self.con.execute(f'SELECT COUNT(*) FROM "{name}";').fetchone()[0])

    # Optional convenience wrappers
    def query(self, sql: str, params: Optional[Iterable[Any]] = None):
        return self.con.execute(sql, params or [])

    def latest_table_name(self, steps: type[Enum], entity: str) -> str | None:
        for step in reversed(list(steps)):
            table_name = f"{step.value}_{entity}"
            if self.table_exists(table_name):
                return table_name
        return None

    def upload_table_to_nemo(self, table_name: str, project_name: str) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / f"{table_name}.csv"
            self.con.execute(
                f"""
                COPY "{table_name}" TO '{csv_path.as_posix()}'
                (HEADER, DELIMITER ';', QUOTE '"', ESCAPE '"');
            """
            )
            self.logger.info(
                f"Uploading table {table_name} to Nemo project {project_name} from {csv_path}"
            )
            self.nl.ReUploadFile(
                projectname=project_name,
                filename=csv_path,
                update_project_settings=False,
            )

    def extract_tables(self, sql: str) -> list[str]:
        """Extract unique table names from SQL using sqlglot."""
        parsed = sqlglot.parse_one(sql)
        tables = {table.name for table in parsed.find_all(sqlglot.expressions.Table)}
        return sorted(tables)
