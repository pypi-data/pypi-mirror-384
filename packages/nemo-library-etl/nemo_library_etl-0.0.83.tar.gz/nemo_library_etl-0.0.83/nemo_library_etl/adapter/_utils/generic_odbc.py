from enum import Enum
import logging
from typing import Any, Iterable, Optional, Union
from typing import Optional, Iterable, Any

from pydantic import BaseModel
import pyodbc
from nemo_library_etl.adapter._utils.db_handler import ETLDuckDBHandler
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library.core import NemoLibrary


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

    def generic_odbc_extract(
        self,
        query: str,
        step: str | Enum,
        entity: str,
        local_database: ETLDuckDBHandler,
        filename: str | None = None,
        chunksize: Optional[int] = 10_000,  # Default chunk size
        gzip_enabled: bool = False,
        dump_to_jsonl: bool = False,
    ) -> None:
        """
        Extract via ODBC in chunks and load into DuckDB.
        Table name equals 'entity'. All columns are stored as VARCHAR to avoid
        schema drift across chunks (e.g., numeric-looking IDs turning into hex strings later).
        """
        import pyodbc
        import pandas as pd

        log = self.logger
        log.info("Starting extraction (ODBC → DuckDB, chunked mode, VARCHAR) ...")

        if not entity:
            raise ValueError("Parameter 'entity' must not be None or empty.")
        if chunksize is None:
            raise ValueError("Parameter 'chunksize' must not be None. Use a positive integer.")

        # DuckDB connection from handler
        ddb = getattr(local_database, "con", None)
        if ddb is None:
            raise RuntimeError("ETLDuckDBHandler.con returned None (no valid DuckDB connection).")

        # Helper: quote identifiers for DuckDB
        def q(identifier: str) -> str:
            # Double-quote and escape inner quotes
            return '"' + str(identifier).replace('"', '""') + '"'

        conn = None
        cur = None
        created_table = False
        total_rows = 0

        try:
            log.info("Connecting via ODBC ...")
            conn = pyodbc.connect(self.odbc_connstr, timeout=self.timeout if self.timeout else 0)
            cur = conn.cursor()
            cur.arraysize = chunksize

            log.info(f"Executing query for entity '{entity}' ...")
            log.info(f"Query: {query}")
            cur.execute(query)

            columns = [desc[0] for desc in cur.description]

            # Optional JSONL writer
            jsonl_writer_ctx = (
                self.fh.streamJSONL(step=step, entity=entity, filename=filename, gzip_enabled=gzip_enabled)
                if dump_to_jsonl
                else None
            )
            if jsonl_writer_ctx:
                writer = jsonl_writer_ctx.__enter__()

            ddb.execute("BEGIN;")
            log.info(f"Streaming rows with chunksize={chunksize} ...")

            while True:
                rows = cur.fetchmany(chunksize)
                if not rows:
                    break

                # Build DataFrame for this chunk (we don't rely on its dtypes)
                df = pd.DataFrame.from_records(rows, columns=columns)

                # Register the chunk as a DuckDB view
                ddb.register("batch_df", df)

                # Build a SELECT list casting ALL columns to VARCHAR to avoid type conflicts
                select_varchar = ", ".join([f"CAST({q(c)} AS VARCHAR) AS {q(c)}" for c in columns])

                if not created_table:
                    # Create table with all VARCHAR columns, then insert the first chunk
                    ddb.execute(f"CREATE OR REPLACE TABLE {q(entity)} AS SELECT {select_varchar} FROM batch_df;")
                    created_table = True
                else:
                    # Append subsequent chunks (again forced to VARCHAR)
                    ddb.execute(f"INSERT INTO {q(entity)} SELECT {select_varchar} FROM batch_df;")

                ddb.unregister("batch_df")

                if dump_to_jsonl:
                    recs = self._rows_to_dicts(columns, rows)
                    writer.write_many(recs)

                total_rows += len(df)

            if jsonl_writer_ctx:
                jsonl_writer_ctx.__exit__(None, None, None)

            ddb.execute("COMMIT;")
            log.info(f"Completed ODBC → DuckDB load. Table: {entity}, Rows: {total_rows:,} (all VARCHAR)")

        except Exception as e:
            try:
                ddb.execute("ROLLBACK;")
            except Exception:
                pass
            log.error(f"Error during ODBC→DuckDB load for entity '{entity}': {e}")
            raise
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
            log.info("ODBC connection closed.")