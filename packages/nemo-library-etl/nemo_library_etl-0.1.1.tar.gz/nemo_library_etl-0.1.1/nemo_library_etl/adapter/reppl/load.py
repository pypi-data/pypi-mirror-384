"""
RepPL ETL Load Module.

This module handles the loading phase of the RepPL ETL pipeline.
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
    RepPLLoad: Main class handling RepPL data loading.
"""

import logging
from typing import Union
from nemo_library_etl.adapter.reppl.config_models_reppl import ConfigRepPL
from nemo_library_etl.adapter._utils.enums import ETLAdapter, ETLStep
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library import NemoLibrary
import pandas as pd


PROJECT_NAME_PLFROMCONTROLLING = "PL from Controlling"


class RepPLLoad:
    """
    Handles loading of transformed RepPL data into target system.
    
    This class manages the loading phase of the RepPL ETL pipeline,
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
        cfg (PipelineRepPL): Pipeline configuration with loading settings.
    """
    
    def __init__(
        self, 
        nl: NemoLibrary, 
        cfg: ConfigRepPL, 
        logger: Union[logging.Logger, object], 
        fh: ETLFileHandler,
    ) -> None:
        """
        Initialize the RepPL Load instance.

        Sets up the loader with the necessary library instances, configuration,
        and logging capabilities for the loading process.

        Args:
            nl (NemoLibrary): Core Nemo library instance for system integration.
            cfg (PipelineRepPL): Pipeline configuration object containing
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
        Execute the main loading process for RepPL data.
        
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
        self.logger.info("Loading all RepPL objects")

        # load transformed data
        data = self.fh.readJSONL(step=ETLStep.TRANSFORM, entity="pl")

        df = pd.DataFrame(data)
        self.nl.ReUploadDataFrame(
            df=df,
            projectname=PROJECT_NAME_PLFROMCONTROLLING,
            update_project_settings=False,
        )
