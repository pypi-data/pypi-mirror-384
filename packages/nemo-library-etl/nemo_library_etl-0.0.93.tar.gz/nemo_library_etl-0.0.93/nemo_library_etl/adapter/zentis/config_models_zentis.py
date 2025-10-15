from pydantic import BaseModel, Field


class ZentisFileConfig(BaseModel):
    extract_active: bool = True
    file_path: str
    separator: str = ","  # default separator for CSV files
    decimal: str = "."  # default decimal point for CSV files
    encoding: str = "utf-8"  # default encoding
    datatypes: dict[str, str] = Field(default_factory=dict)  # field name to data type mapping


class ExtractConfigZentis(BaseModel):
    extract_active: bool = True
    files: dict[str, ZentisFileConfig]


class TransformConfigZentis(BaseModel):
    transform_active: bool = True


class LoadConfigZentis(BaseModel):
    load_active: bool = True


class ConfigZentis(BaseModel):

    config_version: str = "0.0.1"
    etl_directory: str = "./etl/"
    extract: ExtractConfigZentis 
    transform: TransformConfigZentis 
    load: LoadConfigZentis 

    class Config:
        extra = "allow"  # allow adapter-specific keys without failing


CONFIG_MODEL = ConfigZentis
