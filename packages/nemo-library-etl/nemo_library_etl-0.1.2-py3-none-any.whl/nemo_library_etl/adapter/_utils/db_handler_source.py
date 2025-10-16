from enum import Enum
import logging
from typing import Any, Iterable, Optional, Union
from typing import Optional, Iterable, Any

from pydantic import BaseModel
import pyodbc
from nemo_library_etl.adapter._utils.db_handler_local import ETLDuckDBHandler
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library.core import NemoLibrary
import re
import pyodbc
import pandas as pd
from hdbcli import dbapi


class DatabaseHandlerSource:

    def __init__(
        self,
        nl: NemoLibrary,
        cfg: BaseModel,
        logger: Union[logging.Logger, object],
        fh: ETLFileHandler,
    ):
        self.nl = nl
        self.cfg = cfg
        self.logger = logger
        self.fh = fh

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
                {
                    col: DatabaseHandlerSource._decode(r[i])
                    for i, col in enumerate(columns)
                }
            )
        return out

    # ---------- public API ----------

    def connect_odbc(
        self,
        odbc_connstr: str,
        timeout: int | None = 300,
    ) -> pyodbc.Connection:
        self.logger.info("Connecting via ODBC ...")
        conn = pyodbc.connect(odbc_connstr, timeout=timeout if timeout else 0)
        self.logger.info("Connected.")
        return conn

    def connect_hdb(
        self,
        address: str,
        port: int,
        user: str,
        password: str,
        autocommit: bool = True,
    ) -> dbapi.Connection:
        self.logger.info("Connecting to HANA database ...")
        conn = dbapi.connect(
            address=address,
            port=port,
            user=user,
            password=password,
            autocommit=autocommit,
        )
        self.logger.info("Connected.")
        return conn

    def generic_odbc_extract(
        self,
        conn: pyodbc.Connection | dbapi.Connection,
        query: str,
        step: str | Enum,
        entity: str | None,
        filename: str | None = None,
        chunksize: Optional[int] = None,
        gzip_enabled: bool = False,
    ) -> None:
        log = self.logger
        log.info("Starting extraction (ODBC, JSON only) ...")

        cur: pyodbc.Cursor | dbapi.Cursor = conn.cursor()

        if chunksize:
            cur.arraysize = chunksize  # hint for fetchmany

        log.info("Executing query ...")
        log.info(f"Query: {query}")
        cur.execute(query)

        # Column names
        columns = [desc[0] for desc in cur.description]

        if chunksize:
            log.info(f"Streaming rows with chunksize={chunksize} ...")
            total = 0
            with self.fh.streamJSONL(
                step=step,
                entity=entity,
                filename=filename,
                gzip_enabled=gzip_enabled,
            ) as writer:
                while True:
                    rows = cur.fetchmany(chunksize)
                    if not rows:
                        break
                    recs = self._rows_to_dicts(columns, rows)
                    writer.write_many(recs)
                    total += len(recs)
            log.info(f"Completed (streamed JSON array). Rows: {total:,}")
        else:
            # No streaming: fetch all (only for small/medium result sets)
            rows = cur.fetchall()
            recs = self._rows_to_dicts(columns, rows)
            self.fh.writeJSONL(
                step=step,
                data=recs,
                entity=entity,
                filename=filename,
                gzip_enabled=gzip_enabled,
            )
            log.info(f"Completed (non-streamed JSON). Rows: {len(recs):,}")
