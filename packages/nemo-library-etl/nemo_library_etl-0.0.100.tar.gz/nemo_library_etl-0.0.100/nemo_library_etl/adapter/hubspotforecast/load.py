"""
HubSpotForecast ETL Load Module.

This module handles the loading phase of the HubSpotForecast ETL pipeline.
It takes the transformed data and loads it into the target system, typically the
Nemo database or data warehouse.

The loading process typically includes:
1. Data validation before insertion
2. Connection management to target systems
3. Batch processing for efficient data loading
4. Error handling and rollback capabilities
5. Data integrity checks post-loading
6. Performance optimization for large datasets
7. Comprehensive logging throughout the process

Classes:
    HubSpotForecastLoad: Main class handling HubSpotForecast data loading.
"""

from datetime import datetime
import locale
import logging
from pathlib import Path
from typing import Union
import openpyxl
from nemo_library_etl.adapter._utils.cloud_dirs import find_onedrive_dir
from nemo_library_etl.adapter.hubspotforecast.config_models_hubspotforecast import ConfigHubSpotForecast
from nemo_library_etl.adapter._utils.enums import ETLAdapter, ETLStep
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library import NemoLibrary

from nemo_library_etl.adapter.hubspotforecast.enums import HubSpotTransformStep

DEAL_STAGE_SPSTATUS_MAPPING = {
    # "Unqualified lead": "D",
    "Qualified lead": "C",
    "Presentation": "C",
    "Test phase": "C",
    "Negotiation": "B",
    "Commit": "A",
    "closed and won": "K",
    # "closed and lost": "X",
}
DEAL_STAGE_STATUS_MAPPING = {
    # "Unqualified lead": "pipeline",
    "Qualified lead": "upside",
    "Presentation": "upside",
    "Test phase": "upside",
    "Negotiation": "probable",
    "Commit": "commit",
    "closed and won": "won",
    # "closed and lost": "lost",
}
DEAL_STAGE_CASE_MAPPING = {
    # "Unqualified lead": "",
    "Qualified lead": "b",
    "Presentation": "b",
    "Test phase": "b",
    "Negotiation": "n",
    "Commit": "w",
    "closed and won": "",
    # "closed and lost": "",
}


class HubSpotForecastLoad:
    """
    Handles loading of transformed HubSpotForecast data into target system.
    
    This class manages the loading phase of the HubSpotForecast ETL pipeline,
    providing methods to insert transformed data into the target system with
    proper error handling, validation, and performance optimization.
    
    The loader:
    - Uses NemoLibrary for core functionality and configuration
    - Integrates with Prefect logging for pipeline visibility
    - Manages database connections and transactions
    - Provides batch processing capabilities
    - Handles data validation before insertion
    - Ensures data integrity and consistency
    - Optimizes performance for large datasets
    
    Attributes:
        nl (NemoLibrary): Core Nemo library instance for system integration.
        config: Configuration object from the Nemo library.
        logger: Prefect logger for pipeline execution tracking.
        cfg (PipelineHubSpotForecast): Pipeline configuration with loading settings.
    """
    
    def __init__(
        self, 
        nl: NemoLibrary, 
        cfg: ConfigHubSpotForecast, 
        logger: Union[logging.Logger, object], 
        fh: ETLFileHandler,
    ) -> None:
        """
        Initialize the HubSpotForecast Load instance.

        Sets up the loader with the necessary library instances, configuration,
        and logging capabilities for the loading process.

        Args:
            nl (NemoLibrary): Core Nemo library instance for system integration.
            cfg (PipelineHubSpotForecast): Pipeline configuration object containing
                                                          loading settings and rules.
            logger (Union[logging.Logger, object]): Logger instance for recording execution details.
                                                   Can be a standard Python logger or Prefect logger.
        """
        self.nl = nl
        self.cfg = cfg
        self.logger = logger
        self.fh = fh

        super().__init__()           

    def load(self) -> None:
        """
        Execute the main loading process for HubSpotForecast data.
        
        This method orchestrates the complete loading process by:
        1. Connecting to the target system (database, data warehouse, etc.)
        2. Loading transformed data from the previous ETL phase
        3. Validating data before insertion
        4. Performing batch inserts for optimal performance
        5. Handling errors and implementing rollback mechanisms
        6. Verifying data integrity post-insertion
        7. Updating metadata and audit tables
        8. Cleaning up temporary resources
        
        The method provides detailed logging for monitoring and debugging purposes
        and ensures transaction safety through proper error handling.
        
        Note:
            The actual loading logic needs to be implemented based on
            the target system requirements and data models.
        """
        self.logger.info("Loading all HubSpotForecast objects")

        # load objects

        header = self.fh.readJSONL(
            step=ETLStep.TRANSFORM,
            substep=HubSpotTransformStep.FORECAST,
            entity=HubSpotTransformStep.DEALS_FORECAST_HEADER,
        )

        deals = self.fh.readJSONL(
            step=ETLStep.TRANSFORM,
            substep=HubSpotTransformStep.FORECAST,
            entity=HubSpotTransformStep.DEALS_FORECAST_DEALS,
        )

        # Load the Excel workbook containing the forecast data
        xlsx_file = Path(
            self.cfg.load.forecast_call_xlsx_file.replace(
                "<onedrivedir>", find_onedrive_dir()
            )
        )
        if not xlsx_file.exists():
            raise FileNotFoundError(f"Forecast Excel file not found: {xlsx_file}")

        workbook = openpyxl.load_workbook(xlsx_file)

        # Open the specific worksheet in the workbook
        worksheet = workbook["Access-Datenbasis"]
        worksheet.delete_rows(2, worksheet.max_row)

        # set local for german export
        locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

        # write header
        for deal in header:
            if not deal.get("dealstage").startswith("closed"):
                amount_json = float(deal.get("amount", 0) or 0)
                amount_de = locale.format_string("%.2f", amount_json, grouping=True)
                row = [
                    "hIT",
                    "21",
                    "",
                    "Verbal FC",
                    "Verbal FC",
                    deal.get("dealname").replace("(FORECAST) ", ""),
                    "",
                    deal.get("closedate"),
                    deal.get("closedate"),
                    "",
                    "",
                    amount_de,
                    "A",
                    "commit",
                    "n",
                    "",
                    "",
                    (
                        "Licence"
                        if deal.get("revenue_stream") == "SW"
                        else (
                            "Subscription"
                            if deal.get("revenue_stream") == "SaaS"
                            else "undefined !!!"
                        )
                    ),
                    (
                        "Kauf"
                        if deal.get("revenue_stream") == "SW"
                        else (
                            "SaaS / Cloud"
                            if deal.get("revenue_stream") == "SaaS"
                            else "undefined !!!"
                        )
                    ),
                    "hIT",
                    "EUR",
                    None,
                ]
                worksheet.append(row)

        # add the deals

        forecast_deals = [
            deal
            for deal in deals
            if deal.get("revenue_stream") in ["SW", "SaaS"]
            and deal.get("verkauf_uber") in ["hIT"]
        ]

        for deal in forecast_deals:

            closedate = deal.get("closedate")
            if isinstance(closedate, datetime):
                closedate = closedate.date()  # keep only date part

            amount_json = float(deal.get("amount", 0) or 0)
            amount_de = locale.format_string("%.2f", amount_json, grouping=True)

            row = [
                "hIT",
                "21",
                "",
                deal.get("id"),
                (
                    deal.get("company_name")
                    if deal.get("company_name")
                    else deal.get("dealname")
                ),
                deal.get(
                    "dealname",
                ),
                deal.get("hubspot_owner_id"),
                closedate,
                closedate,
                "",
                "",
                amount_de,
                DEAL_STAGE_SPSTATUS_MAPPING.get(
                    deal.get("dealstage"), f"UNDEFINED '{deal.get('dealstage')}'"
                ),
                DEAL_STAGE_STATUS_MAPPING.get(
                    deal.get("dealstage"), f"UNDEFINED '{deal.get('dealstage')}'"
                ),
                DEAL_STAGE_CASE_MAPPING.get(
                    deal.get("dealstage"), f"UNDEFINED '{deal.get('dealstage')}'"
                ),
                "",
                "x" if amount_json > 20000 else "",
                (
                    "Licence"
                    if deal.get("revenue_stream") == "SW"
                    else (
                        "Subscription"
                        if deal.get("revenue_stream") == "SaaS"
                        else "undefined !!!"
                    )
                ),
                (
                    "Kauf"
                    if deal.get("revenue_stream") == "SW"
                    else (
                        "SaaS / Cloud"
                        if deal.get("revenue_stream") == "SaaS"
                        else "undefined !!!"
                    )
                ),
                "hIT",
                "EUR",
                None,
            ]
            worksheet.append(row)

        # Save the workbook with the updated data
        workbook.save(xlsx_file)
