from typing import List, Optional
from pydantic import BaseModel, Field


class ExtractConfigHubSpotForecast(BaseModel):
    extract_active: bool = True
    deal_pipelines: Optional[List[str]] = Field(
        default_factory=lambda: ["*"],
        description="List of deal pipelines to include. Use ['*'] to include all.",
    )

class TransformConfigHubSpotForecast(BaseModel):
    transform_active: bool = True

class LoadConfigHubSpotForecast(BaseModel):
    load_active: bool = True
    forecast_call_xlsx_file: str = "FCCall.xlsx"
    
class ConfigHubSpotForecast(BaseModel):

    config_version: str = "0.0.1"
    etl_directory: str = "./etl/hubspotforecast"
    extract: ExtractConfigHubSpotForecast = Field(default_factory=ExtractConfigHubSpotForecast)
    transform: TransformConfigHubSpotForecast = Field(default_factory=TransformConfigHubSpotForecast)
    load: LoadConfigHubSpotForecast = Field(default_factory=LoadConfigHubSpotForecast)

    class Config:
        extra = "allow"  # allow adapter-specific keys without failing

CONFIG_MODEL = ConfigHubSpotForecast