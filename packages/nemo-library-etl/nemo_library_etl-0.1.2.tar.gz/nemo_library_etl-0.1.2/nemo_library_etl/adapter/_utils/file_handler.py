# nemo_library/adapter/_utils/file_handler.py
from datetime import date, datetime
from enum import Enum
import json
import logging
import gzip
from pathlib import Path
from contextlib import contextmanager
from typing import Iterable, Optional, Any, Iterator, Union

from pydantic import BaseModel

from nemo_library_etl.adapter._utils.dbandfileutils import (
    _as_str,
    _init_logger,
    _is_gz,
    _output_path,
    _slugify_filename,
)

try:
    from prefect import get_run_logger  # type: ignore

    _PREFECT_AVAILABLE = True
except Exception:
    _PREFECT_AVAILABLE = False

from nemo_library import NemoLibrary


class ETLFileHandler:
    """
    JSONL-focused ETL file operations:
    - Write all records as JSON Lines (one JSON object per line)
    - Streaming write (append line by line efficiently)
    - Auto-detect gzip (.jsonl.gz) on read & write

    Backwards compatibility:
    - readJSON(), writeJSON(), streamJSONList() are thin wrappers
      around their JSONL equivalents and will log a deprecation warning.
    """

    def __init__(
        self,
        nl: NemoLibrary,
        cfg: BaseModel,
        logger: Union[logging.Logger, object],
    ) -> None:
        self.nl = nl
        self.cfg = cfg
        self.logger = logger
        super().__init__()

    # ---------- (de)serialization helpers ----------

    def _json_default(self, o):
        """Default JSON serializer for datetimes, enums, and objects with to_dict()."""
        if hasattr(o, "to_dict") and callable(o.to_dict):
            return o.to_dict()
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, Enum):
            return o.value
        return str(o)

    # ---------- utility methods ----------

    def _open_text_auto(self, path: Path, mode: str):
        """
        Open text file; auto-detect gzip by file extension. Mode is 'r' or 'w' or 'a'.
        Always uses UTF-8 text encoding.
        """
        assert mode in ("r", "w", "a")
        if _is_gz(path):
            return gzip.open(path, mode + "t", encoding="utf-8")
        else:
            return open(path, mode, encoding="utf-8")

    # =====================================================================
    #                             JSONL METHODS
    # =====================================================================

    def readJSONL(
        self,
        step: str | Enum,
        entity: str | None | Enum,
        filename: str | None = None,
        label: str | None = None,
        ignore_nonexistent: bool = False,
        substep: Optional[str | Enum] = None,
    ) -> list[dict]:
        """
        Read a JSONL file (one JSON object per line) from the ETL output location.
        Tries <stem>.jsonl then <stem>.jsonl.gz; returns a list[dict].
        Empty or non-existent (when ignore_nonexistent=True) => [].
        """
        base_path = _output_path(
            self.cfg.etl_directory, step, substep, entity, filename, ""
        )
        
        candidates = [
            base_path.with_suffix(".jsonl"),
            base_path.with_suffix(".jsonl.gz"),
        ]

        file_path = None
        for cand in candidates:
            if cand.exists():
                file_path = cand
                break

        obj_label = entity or label or "<unknown>"
        if file_path is None:
            if ignore_nonexistent:
                self.logger.warning(
                    f"No JSONL file found for base {base_path}. Returning empty list for entity {obj_label}."
                )
                return []
            raise FileNotFoundError(
                f"No JSONL file found. Tried: {', '.join(str(c) for c in candidates)}"
            )

        records: list[dict] = []
        with self._open_text_auto(file_path, "r") as f:
            for ln, line in enumerate(f, start=1):
                s = line.strip()
                if not s:
                    continue
                try:
                    rec = json.loads(s)
                except Exception as e:
                    raise ValueError(f"Invalid JSONL at {file_path}:{ln}: {e}") from e
                if not isinstance(rec, dict):
                    raise ValueError(
                        f"Expected JSON object per line at {file_path}:{ln}, got {type(rec).__name__}"
                    )
                records.append(rec)

        if not records:
            self.logger.warning(
                f"No records found in file {file_path} for entity {obj_label}."
            )
        return records

    def writeJSONL(
        self,
        step: str | Enum,
        data: dict | Iterable[dict] | Any,
        entity: str | Enum | None,
        filename: str | None = None,
        label: str | None = None,
        gzip_enabled: bool = False,
        substep: Optional[str | Enum] = None,
        newline: str = "\n",
    ) -> Path:
        """
        Write records as JSON Lines (one JSON object per line).
        'data' may be:
        - a dict (single record)
        - an iterable of dicts
        - a container object with attributes like .value / .items / .results / .records / .data
        - a single object convertible via .to_dict() / .model_dump() / __dict__
        """
        from collections.abc import Iterable as _Iterable
        import dataclasses

        suffix = ".jsonl.gz" if gzip_enabled else ".jsonl"
        file_path = _output_path(
            self.cfg.etl_directory, step, substep, entity, filename, suffix
        )

        obj_label = (
            (entity.value if isinstance(entity, Enum) else entity)
            or label
            or "<unknown>"
        )

        def _to_dict(obj: Any) -> dict:
            # 1) explicit converters
            if hasattr(obj, "to_dict") and callable(obj.to_dict):
                return obj.to_dict()
            if hasattr(obj, "model_dump") and callable(obj.model_dump):
                return obj.model_dump()
            # 2) dataclass
            if dataclasses.is_dataclass(obj):
                return dataclasses.asdict(obj)
            # 3) fall back to __dict__ if it looks like a plain object
            if hasattr(obj, "__dict__"):
                return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
            # 4) last resort: let JSON default handle it (stringify enums/datetimes etc.)
            #    but we still want a mapping
            return {"value": obj}

        def _iter_records(d: Any):
            # Single dict → yield once
            if isinstance(d, dict):
                yield d
                return

            # If it's an Iterable of dict-like objects (but not str/bytes)
            if isinstance(d, _Iterable) and not isinstance(d, (str, bytes, bytearray)):
                for item in d:
                    if isinstance(item, dict):
                        yield item
                    else:
                        yield _to_dict(item)
                return

            # Known container attributes with collections inside
            for attr in ("value", "items", "results", "records", "data"):
                if hasattr(d, attr):
                    seq = getattr(d, attr)
                    if isinstance(seq, _Iterable) and not isinstance(
                        seq, (str, bytes, bytearray)
                    ):
                        for item in seq:
                            if isinstance(item, dict):
                                yield item
                            else:
                                yield _to_dict(item)
                        return
                    # If the attribute itself is a single dict/object
                    if isinstance(seq, dict):
                        yield seq
                        return
                    else:
                        yield _to_dict(seq)
                        return

            # Fallback: treat as single object
            yield _to_dict(d)

        count = 0
        with self._open_text_auto(file_path, "w") as f:
            for rec in _iter_records(data):
                if not isinstance(rec, dict):
                    raise TypeError(
                        f"writeJSONL expects dict-like records; got element of type {type(rec).__name__}"
                    )
                line = json.dumps(rec, ensure_ascii=False, default=self._json_default)
                f.write(line)
                f.write(newline)
                count += 1

        if count == 0:
            self.logger.warning(
                f"No data to write for entity {obj_label}. Created empty file at {file_path}."
            )
        else:
            self.logger.info(
                f"{count:,} records written to {file_path} for {obj_label}."
            )
        return file_path

    @contextmanager
    def streamJSONL(
        self,
        step: str | Enum,
        entity: str | Enum | None,
        filename: str | None = None,
        label: str | None = None,
        gzip_enabled: bool = False,
        substep: Optional[str | Enum] = None,
        newline: str = "\n",
    ):
        """
        Context manager to stream JSONL:
        - Each call to write_one(rec) writes one JSON object + newline.
        - write_many(recs) iterates and writes each record.
        - Works with .jsonl or .jsonl.gz based on gzip_enabled.
        """
        suffix = ".jsonl.gz" if gzip_enabled else ".jsonl"
        path = _output_path(
            self.cfg.etl_directory, step, substep, entity, filename, suffix
        )

        f = self._open_text_auto(path, "w")
        obj_label = (
            (entity.value if isinstance(entity, Enum) else entity)
            or label
            or "<unknown>"
        )

        self.logger.info(f"Streaming JSONL to {path} for entity {obj_label}.")

        total = 0

        class _Writer:
            def write_one(self_inner, rec: dict, chunk_size: int = 10000):
                nonlocal total
                nonlocal obj_label
                if not isinstance(rec, dict):
                    raise TypeError(
                        f"streamJSONL.write_one expects dict; got {type(rec).__name__}"
                    )
                line = json.dumps(rec, ensure_ascii=False, default=self._json_default)
                f.write(line)
                f.write(newline)
                total += 1
                if total % chunk_size == 0:
                    self.logger.info(
                        f"{total:,} records written so far for entity {obj_label} to {path}"
                    )

            def write_many(self_inner, recs: Iterable[dict]):
                chunk_size = len(recs) if hasattr(recs, "__len__") else 10000
                for rec in recs:
                    self_inner.write_one(rec, chunk_size=chunk_size)

            @property
            def path(self_inner) -> Path:
                return path

        try:
            yield _Writer()
        finally:
            f.close()
            self.logger.info(
                f"Streaming JSONL written to {path} for entity {obj_label}: "
                f"{total:,} records written."
            )
