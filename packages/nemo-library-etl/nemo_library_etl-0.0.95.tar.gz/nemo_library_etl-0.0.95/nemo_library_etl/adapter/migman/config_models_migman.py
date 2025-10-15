# All code comments in English as requested
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, conint

##############################################################
# Shared strict base: forbid unknown fields everywhere
##############################################################

class StrictBaseModel(BaseModel):
    # Forbid extra keys globally for all derived models.
    model_config = ConfigDict(
        extra="forbid",              # disallow unknown/extra fields
        str_strip_whitespace=True,   # (optional) trim strings
        populate_by_name=True        # allow population by field name/alias
    )


##############################################################
# Extract
##############################################################

class ExtractInforcomConfig(StrictBaseModel):
    """ODBC-based extraction from INFORCOM (INFOR.* tables)."""

    active: bool = True
    odbc_connstr: str = Field(..., description="ODBC connection string for SQL Server")
    chunk_size: conint(gt=0) = 10_000
    timeout: conint(gt=0) = 300
    table_prefix: str = "INFOR."
    table_selector: Literal["all", "join_parser"] = "all"
    tables: List[str]


class ExtractConfigMigMan(StrictBaseModel):
    extract_active: bool = True
    load_to_nemo: bool = True
    delete_temp_files: bool = True
    nemo_project_prefix: str = "migman_extract_"
    inforcom: ExtractInforcomConfig


##############################################################
# Transform
##############################################################

class TransformJoinsConfig(StrictBaseModel):
    active: bool = True
    file: str


class TransformJoinConfig(StrictBaseModel):
    active: bool = True
    adapter: str
    joins: Dict[str, TransformJoinsConfig] = Field(
        default_factory=dict,
        description="Mapping from adapter name to its join configuration",
    )


class TransformNonEmptyConfig(StrictBaseModel):
    active: bool = True


class TransformDuplicatesConfig(StrictBaseModel):
    active: bool = True
    threshold: conint(ge=0, le=100) = 90  # similarity threshold between 0 and 100
    primary_key: str
    fields: List[str] = Field(
        default_factory=list, description="Fields to consider for duplicate detection"
    )


class TransformDuplicateConfig(StrictBaseModel):
    active: bool = True
    duplicates: Dict[str, TransformDuplicatesConfig] = Field(
        default_factory=dict,
        description="Mapping from object name to its duplicate configuration",
    )


class TransformConfigMigMan(StrictBaseModel):
    transform_active: bool = True
    load_to_nemo: bool = True
    delete_temp_files: bool = True
    nemo_project_prefix: str = "migman_transform_"
    join: TransformJoinConfig
    nonempty: TransformNonEmptyConfig
    duplicate: TransformDuplicateConfig


##############################################################
# Load
##############################################################

class LoadConfigMigMan(StrictBaseModel):
    load_active: bool = True
    entities: List[str] = Field(
        default_factory=list, description="List of entities to load"
    )


##############################################################
# Full Config
##############################################################

class MigManProjectConfig(StrictBaseModel):
    project_status_file: Optional[str] = None
    projects: List[str] = Field(
        default_factory=list,
        description="List of MigMan projects to process (alternatively, use property 'project_status_file')",
    )


class ConfigMigMan(StrictBaseModel):
    config_version: str = "0.0.1"
    etl_directory: str = "./etl/migman"
    local_database: str = "./etl/migman/migman_etl.duckdb"
    setup: MigManProjectConfig
    extract: ExtractConfigMigMan
    transform: TransformConfigMigMan
    load: LoadConfigMigMan


CONFIG_MODEL = ConfigMigMan