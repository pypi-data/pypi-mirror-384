"""
RepPrices ETL Extract Module.

This module handles the extraction phase of the RepPrices ETL pipeline.
It provides functionality to extract data from RepPrices systems and 
prepare it for the transformation phase.

The extraction process:
1. Connects to the RepPrices system using configured credentials
2. Iterates through configured tables and extracts data
3. Handles inactive tables by skipping them
4. Uses ETLFileHandler for data persistence
5. Provides comprehensive logging throughout the process

Classes:
    RepPricesExtract: Main class handling RepPrices data extraction.
"""

import logging
from pathlib import Path
from typing import Union
from nemo_library_etl.adapter._utils.cloud_dirs import find_onedrive_dir
from nemo_library_etl.adapter.repprices.config_models_repprices import ConfigRepPrices
from nemo_library_etl.adapter._utils.enums import ETLAdapter, ETLStep
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library import NemoLibrary
import pandas as pd


class RepPricesExtract:
    """
    Handles extraction of data from RepPrices system.
    
    This class manages the extraction phase of the RepPrices ETL pipeline,
    providing methods to connect to RepPrices systems, retrieve data,
    and prepare it for subsequent transformation and loading phases.
    
    The extractor:
    - Uses NemoLibrary for core functionality and configuration
    - Integrates with Prefect logging for pipeline visibility
    - Processes tables based on configuration settings
    - Handles both active and inactive table configurations
    - Leverages ETLFileHandler for data persistence
    
    Attributes:
        nl (NemoLibrary): Core Nemo library instance for system integration.
        config: Configuration object from the Nemo library.
        logger: Prefect logger for pipeline execution tracking.
        cfg (PipelineRepPrices): Pipeline configuration with extraction settings.
    """
    
    def __init__(
        self, 
        nl: NemoLibrary, 
        cfg: ConfigRepPrices, 
        logger: Union[logging.Logger, object], 
        fh: ETLFileHandler,
    ) -> None:
        """
        Initialize the RepPrices Extract instance.
        
        Sets up the extractor with the necessary library instances, configuration,
        and logging capabilities for the extraction process.
        
        Args:
            nl (NemoLibrary): Core Nemo library instance for system integration.
            cfg (PipelineZentis): Pipeline configuration object containing
                                                          extraction settings and rules.
            logger (Union[logging.Logger, object]): Logger instance for recording execution details.
                                                   Can be a standard Python logger or Prefect logger.
        """
        self.nl = nl
        self.cfg = cfg
        self.logger = logger
        self.fh = fh

        super().__init__()            
    
    def extract(self) -> None:
        """
        Execute the main extraction process for RepPrices data.
        
        This method orchestrates the complete extraction process by:
        1. Logging the start of extraction
        2. Iterating through configured tables
        3. Skipping inactive tables
        4. Processing active tables and extracting their data
        5. Using ETLFileHandler for data persistence
        
        The method respects table activation settings and provides detailed
        logging for monitoring and debugging purposes.
        
        Note:
            The actual data extraction logic needs to be implemented based on
            the specific RepPrices system requirements.
        """
        self.logger.info("Extracting all RepPrices objects")

        onedrive_dir = find_onedrive_dir()
        if not onedrive_dir:
            raise FileNotFoundError("Could not locate OneDrive directory.")

        pricing_file = (
            Path(onedrive_dir)
            / "Product Management"
            / "03 Go-To-Market"
            / "Pricing"
            / "internal"
            / "Price List.xlsx"
        )

        if not pricing_file.exists():
            raise FileNotFoundError(f"Pricing file not found at {pricing_file}")

        self.logger.info(f"Using pricing file at {pricing_file}")
        cols_to_use = [0, 7] + list(
            range(13, 38)
        )  # A (Product), H (Part id), N - AL (users)
        df = pd.read_excel(
            pricing_file, sheet_name="NEMO", skiprows=3, nrows=14, usecols=cols_to_use
        )
        df = df.drop(df.index[0])
        df = df.reset_index(drop=True)

        # extract product module codes
        df.iloc[:, 0] = df.iloc[:, 0].str.split().str[0]

        # convert to dict
        data_dict = df.to_dict(orient="records")

        # dump to file
        self.fh.writeJSONL(
            step=ETLStep.EXTRACT,
            data=data_dict,
            entity="pricelist",
        )
