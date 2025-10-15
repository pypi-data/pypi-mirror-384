from enum import Enum
import logging
from pathlib import Path
from typing import Any, Optional
from nemo_library.utils.config import Config

try:
    from prefect import get_run_logger  # type: ignore

    _PREFECT_AVAILABLE = True
except Exception:
    _PREFECT_AVAILABLE = False


def _slugify_filename(name: str | Enum) -> str:
    """Make a safe lowercase file stem from a human name."""
    import re

    if isinstance(name, Enum):
        name = name.value
    s = str(name)
    s = s.strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_") or "table"


def _as_str(x: Any) -> str:
    """Return enum.value for Enums else str(x)."""
    return x.value if isinstance(x, Enum) else str(x)


def _is_gz(path: Path) -> bool:
    return str(path).lower().endswith(".gz")


def _output_path(
    etl_directory: str | Path,
    step: str | Enum,
    substep: str | Enum | None,
    entity: Optional[str | Enum],
    filename: Optional[str],
    suffix: str,
) -> Path:
    """
    Build the path in the ETL directory structure and ensure parent exists.
    adapter: e.g. 'gedys' or ETLAdapter.GEDYS
    step: e.g. 'extract' or ETLStep.EXTRACT
    entity: table name (human string), used to derive file stem unless 'filename' is given
    """
    if not etl_directory:
        raise RuntimeError("ETL directory is not configured (cfg.get_etl_directory())")
    step_s = _as_str(step)
    substep_s = _as_str(substep) if substep else None
    # prefer explicit filename; else derive from entity; else 'result'
    if filename:
        stem = _slugify_filename(filename)
    elif entity:
        stem = _slugify_filename(entity)
    else:
        stem = "result"
    # build directory path stepwise
    base = Path(etl_directory) / step_s
    if substep_s:
        base = base / substep_s

    p = base / f"{stem}{suffix}"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

# ---------- logger ----------

def _init_logger() -> logging.Logger:
    if _PREFECT_AVAILABLE:
        try:
            plogger = get_run_logger()
            plogger.info("Using Prefect run logger.")
            return plogger  # type: ignore[return-value]
        except Exception:
            pass

    logger_name = "nemo.etl"
    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    logger.info(
        "Using standard Python logger (no active Prefect context detected)."
    )
    return logger

