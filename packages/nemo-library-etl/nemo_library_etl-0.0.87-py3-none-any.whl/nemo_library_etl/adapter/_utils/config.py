# All comments in English as requested

import json
from pathlib import Path
from importlib import resources as importlib_resources
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field, ValidationError


# ======== Minimal generic models (kept small) ========


class ExtractConfig(BaseModel):
    extract_active: bool = True

class TransformConfig(BaseModel):
    transform_active: bool = True
    
class LoadConfig(BaseModel):
    load_active: bool = True
    
class ConfigBase(BaseModel):
    """Generic, permissive pipeline model for extract-only use cases."""

    config_version: str = "0.0.1"
    etl_directory: str = "./etl/"
    extract: ExtractConfig = Field(default_factory=ExtractConfig)
    transform: TransformConfig = Field(default_factory=TransformConfig)
    load: LoadConfig = Field(default_factory=LoadConfig)

    class Config:
        extra = "allow"  # allow adapter-specific keys without failing


# ======== IO helpers ========


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal deep merge: dicts are merged, other values are replaced."""
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _load_json_if_exists(path: Path) -> Dict[str, Any]:
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _load_default_from_package(package_root: str, adapter: str) -> Dict[str, Any]:
    """
    Read adapter default JSON from:
      adapter/<adapter>/config/default_config.json
    inside the given package root.
    """
    resource_rel = f"adapter/{adapter}/config/default_config_{adapter}.json"
    with importlib_resources.as_file(
        importlib_resources.files(package_root).joinpath(resource_rel)
    ) as p:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)


def _load_adapter_CONFIG_MODEL(
    package_root: str, adapter: str
) -> Optional[Type[BaseModel]]:
    """
    If present, loads an adapter-specific pydantic model from:
      <package_root>.adapter.<adapter>.config_models  ->  CONFIG_MODEL
    Returns the type or None if not found.
    """
    module_name = f"{package_root}.adapter.{adapter}.config_models_{adapter}"
    try:
        mod = __import__(module_name, fromlist=["CONFIG_MODEL"])
        model = getattr(mod, "CONFIG_MODEL", None)
        if model and issubclass(model, BaseModel):
            return model
    except Exception:
        # Keep silent: absence of a model should not break loading.
        return None
    return None


# ======== Public API ========


def load_config(
    adapter: str,
) -> BaseModel:
    """
    Load extract configuration with a single override layer and return a BaseModel:
      1) defaults from package: adapter/<adapter>/config/default_config.json
      2) override from project: ./config/<adapter>.json (if present)
    If an adapter-specific CONFIG_MODEL exists, validate & return that.
    Otherwise return the generic PipelineBase.
    """
    adapter = adapter.lower()
    # 1) Read defaults from package
    defaults = _load_default_from_package("nemo_library_etl", adapter)

    # 2) Merge project override
    override_path = Path("./config") / f"{adapter}.json"
    override = _load_json_if_exists(override_path)
    merged = _deep_merge(defaults, override)

    # 3) Try adapter-specific model first
    AdapterModel = _load_adapter_CONFIG_MODEL("nemo_library_etl", adapter)
    if AdapterModel is not None:
        try:
            return AdapterModel.model_validate(merged)
        except ValidationError as e:
            # Make error concise while still actionable
            raise RuntimeError(f"[{adapter}] Invalid adapter configuration: {e}") from e

    # 4) Fallback: validate with the tiny generic model
    try:
        return ConfigBase.model_validate(merged)
    except ValidationError as e:
        raise RuntimeError(f"[{adapter}] Invalid generic configuration: {e}") from e
