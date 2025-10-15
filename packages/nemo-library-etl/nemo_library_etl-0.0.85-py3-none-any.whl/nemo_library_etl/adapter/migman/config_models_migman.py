from typing import Dict, List, Optional
from pydantic import BaseModel, Field, conint

##############################################################
# Extract
##############################################################


class ExtractInforcomConfig(BaseModel):
    """ODBC-based extraction from INFORCOM (INFOR.* tables)."""

    active: bool = True
    odbc_connstr: str = Field(..., description="ODBC connection string for SQL Server")
    chunk_size: conint(gt=0) = 10_000
    timeout: conint(gt=0) = 300
    table_prefix: str = "INFOR."

    class Config:
        extra = "forbid"  # keep schema tight for the inforcom block


class ExtractConfigMigMan(BaseModel):
    extract_active: bool = True
    load_to_nemo: bool = True
    nemo_project_prefix: str = "migman_extract_"
    inforcom: ExtractInforcomConfig

    class Config:
        extra = "allow"  # allow future adapter-specific keys


##############################################################
# Transform
##############################################################


class TransformJoinsConfig(BaseModel):
    active: bool = True
    file: str


class TransformJoinConfig(BaseModel):
    active: bool = True
    adapter: str
    joins: Dict[str, TransformJoinsConfig] = Field(
        default_factory=dict,
        description="Mapping from adapter name to its join configuration",
    )


class TransformNonEmptyConfig(BaseModel):
    active: bool = True


class TransformDuplicatesConfig(BaseModel):
    active: bool = True
    threshold: conint(ge=0, le=100) = 90  # similarity threshold between 0 and 100
    primary_key: str
    fields: List[str] = Field(
        default_factory=list, description="Fields to consider for duplicate detection"
    )


class TransformDuplicateConfig(BaseModel):
    active: bool = True
    duplicates: Dict[str, TransformDuplicatesConfig] = Field(
        default_factory=dict,
        description="Mapping from object name to its duplicate configuration",
    )


class TransformConfigMigMan(BaseModel):
    transform_active: bool = True
    load_to_nemo: bool = True
    nemo_project_prefix: str = "migman_transform_"
    join: TransformJoinConfig
    nonempty: TransformNonEmptyConfig
    duplicate: TransformDuplicateConfig


##############################################################
# Load
##############################################################


class LoadConfigMigMan(BaseModel):
    load_active: bool = True
    entities: List[str] = Field(
        default_factory=list, description="List of entities to load"
    )


##############################################################
# Full Config
##############################################################


class MigManProjectConfig(BaseModel):
    project_status_file: Optional[str] = None
    projects: List[str] = Field(
        default_factory=list,
        description="List of MigMan projects to process (alternatively, use property 'project_status_file')",
    )


class ConfigMigMan(BaseModel):

    config_version: str = "0.0.1"
    etl_directory: str = "./etl/migman"
    local_database: str = "./etl/migman/migman_etl.duckdb"
    setup: MigManProjectConfig
    extract: ExtractConfigMigMan
    transform: TransformConfigMigMan
    load: LoadConfigMigMan

    class Config:
        extra = "allow"  # allow adapter-specific keys without failing


CONFIG_MODEL = ConfigMigMan
