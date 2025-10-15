from enum import Enum
import logging
from typing import Any, Iterable, Optional, Union
from typing import Optional, Iterable, Any

from pydantic import BaseModel
import pyodbc
from nemo_library_etl.adapter._utils.db_handler import ETLDuckDBHandler
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library.core import NemoLibrary
import re
import pyodbc
import pandas as pd


class GenericODBCExtract:

    def __init__(
        self,
        nl: NemoLibrary,
        cfg: BaseModel,
        logger: Union[logging.Logger, object],
        fh: ETLFileHandler,
        odbc_connstr: str | None,
        timeout: int | None = 300,
    ):
        self.nl = nl
        self.cfg = cfg
        self.logger = logger
        self.fh = fh

        if odbc_connstr is None:
            raise ValueError("ODBC connection string must be provided.")
        self.odbc_connstr = odbc_connstr
        self.timeout = timeout
        super().__init__()

    # ---------- helpers ----------

    @staticmethod
    def _decode(value: Any) -> Any:
        """Convert values to JSON-serializable types; decode bytes if necessary."""
        if isinstance(value, (bytes, bytearray, memoryview)):
            b = bytes(value)
            try:
                return b.decode("utf-8")
            except UnicodeDecodeError:
                return b.decode("cp1252", errors="ignore")
        return value

    @staticmethod
    def _rows_to_dicts(columns: list[str], rows: Iterable[tuple]) -> list[dict]:
        out: list[dict] = []
        for r in rows:
            out.append(
                {col: GenericODBCExtract._decode(r[i]) for i, col in enumerate(columns)}
            )
        return out

    # ---------- public API ----------


    def generic_odbc_extract_table(
        self,
        table: str,
        step: str | Enum,
        local_database,
        source_prefix: str | None = None,
        filename: str | None = None,
        chunksize: int = 10_000,
        gzip_enabled: bool = False,
        dump_to_jsonl: bool = False,
    ) -> None:
        """
        Plain 1:1 table extract via ODBC into DuckDB with source-accurate types.
        - Reads source schema from ODBC metadata for (optional prefix + table).
        - Creates target table in DuckDB explicitly with mapped types (same name as source).
        - Streams rows in chunks, registers them as strings, and CASTs strictly into target types.
        - Aborts on the first type/cast error (no silent data loss).
        """
        import pyodbc
        import pandas as pd

        log = self.logger
        log.info("Starting table extraction (ODBC → DuckDB, typed, strict, 1:1) ...")

        if not table or not table.strip():
            raise ValueError("Parameter 'table' must not be empty.")
        if chunksize is None or int(chunksize) <= 0:
            raise ValueError("Parameter 'chunksize' must be a positive integer.")

        # Build fully-qualified source name if prefix is given
        source_name = f"{source_prefix.rstrip('.')}.{table}" if source_prefix else table

        # DuckDB connection from handler
        ddb = getattr(local_database, "con", None)
        if ddb is None:
            raise RuntimeError("ETLDuckDBHandler.con returned None (no valid DuckDB connection).")

        # DuckDB identifier quoting
        def q(identifier: str) -> str:
            return '"' + str(identifier).replace('"', '""') + '"'

        def quote_source_table(t: str) -> str:
            parts = [p.strip().strip('"') for p in t.split(".")]
            return ".".join([f'"{p}"' for p in parts])

        def _odbc_to_duck_type(col: dict) -> str:
            t = (col["type_name"] or "").upper()
            s = col.get("column_size") or 0
            d = col.get("decimal_digits") or 0
            if t in ("VARCHAR", "NVARCHAR", "CHAR", "NCHAR", "TEXT", "STRING", "LONGVARCHAR", "NTEXT"):
                return "VARCHAR"
            if t in ("TINYINT", "SMALLINT"):
                return "SMALLINT"
            if t in ("INT", "INTEGER"):
                return "INTEGER"
            if t in ("BIGINT", "INT8", "LONG"):
                return "BIGINT"
            if t in ("FLOAT", "REAL"):
                return "REAL"
            if t in ("DOUBLE", "DOUBLE PRECISION"):
                return "DOUBLE"
            if t.startswith("DECIMAL") or t.startswith("NUMERIC"):
                p = min(max(int(s or 18), 1), 38)
                d = min(max(int(d or 0), 0), 18)
                if d > p:
                    d = max(0, p - 1)
                return f"DECIMAL({p},{d})"
            if t in ("DATE",):
                return "DATE"
            if t in ("DATETIME", "DATETIME2", "TIMESTAMP", "SMALLDATETIME"):
                return "TIMESTAMP"
            if t in ("TIME",):
                return "TIME"
            if t in ("BIT", "BOOLEAN"):
                return "BOOLEAN"
            if t in ("BLOB", "VARBINARY", "BINARY", "IMAGE"):
                return "BLOB"
            if t in ("UUID", "UNIQUEIDENTIFIER"):
                return "UUID"
            return "VARCHAR"

        def _get_source_schema(cur: pyodbc.Cursor, tbl: str) -> list[dict]:
            cols = []
            schema_part = None
            base_table = tbl
            if "." in tbl and not tbl.strip().startswith('"'):
                parts = tbl.split(".")
                if len(parts) == 2:
                    schema_part, base_table = parts[0], parts[1]
            it = cur.columns(table=base_table, schema=schema_part) if schema_part else cur.columns(table=tbl)
            for col in it:
                cols.append({
                    "name": col.column_name,
                    "type_name": (col.type_name or "").upper(),
                    "column_size": col.column_size,
                    "decimal_digits": col.decimal_digits,
                    "nullable": bool(col.nullable),
                    "ordinal": getattr(col, "ordinal_position", None),
                })
            if not cols:
                raise RuntimeError(f"No column metadata returned for source table '{tbl}'.")
            cols.sort(key=lambda c: (999999 if c["ordinal"] is None else c["ordinal"]))
            return cols

        conn = None
        cur = None
        jsonl_writer_ctx = None
        writer = None
        total_rows = 0

        try:
            log.info(f"Connecting via ODBC ...")
            conn = pyodbc.connect(self.odbc_connstr, timeout=self.timeout or 0)
            cur = conn.cursor()
            cur.arraysize = chunksize

            # Discover schema from source
            log.info(f"Discovering source schema for table '{source_name}' ...")
            table_schema = _get_source_schema(cur, source_name)
            schema_map = {c["name"]: _odbc_to_duck_type(c) for c in table_schema}
            column_names = [c["name"] for c in table_schema]

            # Create target table in DuckDB (same name as source)
            cols_ddl = ", ".join([f'{q(c["name"])} {schema_map[c["name"]]}' for c in table_schema])
            ddb.execute(f"CREATE OR REPLACE TABLE {q(table)} ({cols_ddl});")
            log.info(f"Target table '{table}' created with {len(column_names)} columns.")

            # Optional JSONL writer
            if dump_to_jsonl:
                jsonl_writer_ctx = self.fh.streamJSONL(step=step, entity=table, filename=filename, gzip_enabled=gzip_enabled)
                writer = jsonl_writer_ctx.__enter__()

            ddb.execute("BEGIN;")

            src_sql = f"SELECT * FROM {quote_source_table(source_name)}"
            log.info(f"Source SELECT: {src_sql}")
            cur.execute(src_sql)

            try:
                ddb.execute("SET pandas_analyze_sample=0;")
                ddb.execute("SET pandas_analyze_rows=10000000;")
            except Exception:
                pass

            while True:
                rows = cur.fetchmany(chunksize)
                if not rows:
                    break
                df = pd.DataFrame.from_records(rows, columns=column_names).astype("string")
                ddb.register("batch_df", df)
                select_cast = ", ".join([f'{q(c)}:: {schema_map[c]}' for c in column_names])
                ddb.execute(f"INSERT INTO {q(table)} SELECT {select_cast} FROM batch_df;")
                ddb.unregister("batch_df")
                if dump_to_jsonl:
                    writer.write_many(self._rows_to_dicts(column_names, rows))
                total_rows += len(df)

            if jsonl_writer_ctx:
                jsonl_writer_ctx.__exit__(None, None, None)

            ddb.execute("COMMIT;")
            log.info(f"Completed ODBC → DuckDB load. Table: {table}, Rows: {total_rows:,} (strict typed)")

        except Exception as e:
            try:
                ddb.execute("ROLLBACK;")
            except Exception:
                pass
            log.error(f"Error during ODBC→DuckDB load for table '{table}': {e}")
            raise
        finally:
            try:
                ddb.unregister("batch_df")
            except Exception:
                pass
            if cur:
                try: cur.close()
                except Exception: pass
            if conn:
                try: conn.close()
                except Exception: pass
            if jsonl_writer_ctx:
                try: jsonl_writer_ctx.__exit__(None, None, None)
                except Exception: pass
            log.info("ODBC connection closed.")