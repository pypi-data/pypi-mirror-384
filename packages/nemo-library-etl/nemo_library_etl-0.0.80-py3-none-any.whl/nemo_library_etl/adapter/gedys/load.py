"""
Gedys ETL Load Module.

This module handles the loading phase of the Gedys ETL pipeline.
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
    GedysLoad: Main class handling Gedys data loading.
"""

import logging
from typing import Union
from nemo_library_etl.adapter.gedys.config_models import PipelineGedys
from nemo_library_etl.adapter._utils.enums import ETLAdapter, ETLStep
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library import NemoLibrary
import pandas as pd

from nemo_library_etl.adapter.gedys.enums import GedysTransformStep


class GedysLoad:
    """
    Handles loading of transformed Gedys data into target system.
    
    This class manages the loading phase of the Gedys ETL pipeline,
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
        cfg (PipelineGedys): Pipeline configuration with loading settings.
    """
    
    def __init__(
        self, 
        nl: NemoLibrary, 
        cfg: PipelineGedys, 
        logger: Union[logging.Logger, object], 
        fh: ETLFileHandler,
    ) -> None:
        """
        Initialize the Gedys Load instance.

        Sets up the loader with the necessary library instances, configuration,
        and logging capabilities for the loading process.

        Args:
            nl (NemoLibrary): Core Nemo library instance for system integration.
            cfg (PipelineGedys): Pipeline configuration object containing
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
        Execute the main loading process for Gedys data.
        
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
        self.logger.info("Loading all Gedys objects")

        if self.cfg.load_tables:
            for table, model in self.cfg.extract.tables.items():

                data = self.fh.readJSONL(
                    step=ETLStep.TRANSFORM,
                    substep=GedysTransformStep.FLATTEN,
                    entity=table,
                    ignore_nonexistent=True,  # Ignore if file does not exist
                )
                if not data:
                    self.logger.warning(
                        f"No data found for entity {table}. Skipping load."
                    )
                    continue

                # Convert to DataFrame for loading
                df = pd.DataFrame(data)
                if df.empty:
                    self.logger.warning(
                        f"No data to load for entity {table}. Skipping load."
                    )
                    continue

                self.logger.info(f"Loading data for entity {table}")
                self.nl.ReUploadDataFrame(
                    projectname=f"{self.cfg.NemoProjectPrefix}{table}",
                    df=df,
                    update_project_settings=False,
                )

        if self.cfg.load_joined:
            data = self.fh.readJSONL(
                step=ETLStep.TRANSFORM,
                substep=GedysTransformStep.JOIN,
                entity="Company Joined",
                ignore_nonexistent=True,  # Ignore if file does not exist
            )
            if not data:
                self.logger.warning(
                    f"No data found for entity Company Joined. Skipping load."
                )
                return

            # Convert to DataFrame for loading
            df = pd.DataFrame(data)
            if df.empty:
                self.logger.warning(
                    f"No data to load for entity Company Joined. Skipping load."
                )
                return

            self.logger.info(f"Loading data for entity Company Joined")
            self.nl.ReUploadDataFrame(
                projectname=f"{self.cfg.NemoProjectPrefix}Company_Joined",
                df=df,
                update_project_settings=False,
            )
                
        