from pydantic import BaseModel, Field


class ExtractConfigRepPrices(BaseModel):
    extract_active: bool = True

class TransformConfigRepPrices(BaseModel):
    transform_active: bool = True

class LoadConfigRepPrices(BaseModel):
    load_active: bool = True
    
class ConfigRepPrices(BaseModel):

    config_version: str = "0.0.1"
    etl_directory: str = "./etl/repprices"
    extract: ExtractConfigRepPrices = Field(default_factory=ExtractConfigRepPrices)
    transform: TransformConfigRepPrices = Field(default_factory=TransformConfigRepPrices)
    load: LoadConfigRepPrices = Field(default_factory=LoadConfigRepPrices)

    class Config:
        extra = "allow"  # allow adapter-specific keys without failing

CONFIG_MODEL = ConfigRepPrices