from pydantic import BaseModel, Field


class ExtractConfigRepPL(BaseModel):
    extract_active: bool = True

class TransformConfigRepPL(BaseModel):
    transform_active: bool = True

class LoadConfigRepPL(BaseModel):
    load_active: bool = True
    
class ConfigRepPL(BaseModel):

    config_version: str = "0.0.1"
    etl_directory: str = "./etl/reppl"
    extract: ExtractConfigRepPL = Field(default_factory=ExtractConfigRepPL)
    transform: TransformConfigRepPL = Field(default_factory=TransformConfigRepPL)
    load: LoadConfigRepPL = Field(default_factory=LoadConfigRepPL)

    class Config:
        extra = "allow"  # allow adapter-specific keys without failing

CONFIG_MODEL = ConfigRepPL