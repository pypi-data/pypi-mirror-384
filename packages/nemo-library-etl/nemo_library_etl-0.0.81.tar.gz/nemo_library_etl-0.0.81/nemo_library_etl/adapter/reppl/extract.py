"""
RepPL ETL Extract Module.

This module handles the extraction phase of the RepPL ETL pipeline.
It provides functionality to extract data from RepPL systems and 
prepare it for the transformation phase.

The extraction process:
1. Connects to the RepPL system using configured credentials
2. Iterates through configured tables and extracts data
3. Handles inactive tables by skipping them
4. Uses ETLFileHandler for data persistence
5. Provides comprehensive logging throughout the process

Classes:
    RepPLExtract: Main class handling RepPL data extraction.
"""

import logging
from pathlib import Path
from typing import Union
from nemo_library_etl.adapter._utils.cloud_dirs import find_onedrive_dir
from nemo_library_etl.adapter.reppl.config_models_reppl import ConfigRepPL
from nemo_library_etl.adapter._utils.enums import ETLAdapter, ETLStep
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library import NemoLibrary
import pandas as pd


class RepPLExtract:
    """
    Handles extraction of data from RepPL system.
    
    This class manages the extraction phase of the RepPL ETL pipeline,
    providing methods to connect to RepPL systems, retrieve data,
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
        cfg (PipelineRepPL): Pipeline configuration with extraction settings.
    """
    
    def __init__(
        self, 
        nl: NemoLibrary, 
        cfg: ConfigRepPL, 
        logger: Union[logging.Logger, object], 
        fh: ETLFileHandler,
    ) -> None:
        """
        Initialize the RepPL Extract instance.
        
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
        Execute the main extraction process for RepPL data.
        
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
            the specific RepPL system requirements.
        """
        self.logger.info("Extracting all RepPL objects")

        onedrive_dir = find_onedrive_dir()
        if not onedrive_dir:
            raise FileNotFoundError("Could not locate OneDrive directory.")

        root = (
            Path(onedrive_dir)
            / "Reporting"
            / "IFRS Reporting von Controlling"
        )

        if not root.exists():
            raise FileNotFoundError(f"root folder not found at {root}")

        # check for files with pattern "NEMO BWA" in file name
        files = [f for f in root.rglob("*NEMO BWA*.xlsx") if f.is_file()]

        # find the latest file in this list now
        if files:
            latest_file = max(files, key=lambda f: f.stat().st_mtime)
        else:
            raise FileNotFoundError(f"No files found in {root} matching pattern 'NEMO BWA'")

        self.logger.info(f"File used for import (with latest file date): {latest_file}")
        sheet_name = "BWA_BUD_Group"
        df = pd.read_excel(latest_file, sheet_name, skiprows=16)
        
        # set headers for data frame
        new_headers = [f"{str(df.iloc[0, i])} {str(col)[:7]}" for i, col in enumerate(df.columns)]
        new_headers[0] = "description"
        
        df.columns = new_headers
        df = df[2:].reset_index(drop=True)        
        
        # convert to dict
        data_dict = df.to_dict(orient="records")
        
        # dump to file
        self.fh.writeJSONL(
            step=ETLStep.EXTRACT,
            data=data_dict,
            entity="pl",
        )
        