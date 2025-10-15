"""
RepPL ETL Transform Module.

This module handles the transformation phase of the RepPL ETL pipeline.
It processes the extracted data, applies business rules, data cleaning, and formatting
to prepare the data for loading into the target system.

The transformation process typically includes:
1. Data validation and quality checks
2. Data type conversions and formatting
3. Business rule application
4. Data enrichment and calculated fields
5. Data structure normalization
6. Comprehensive logging throughout the process

Classes:
    RepPLTransform: Main class handling RepPL data transformation.
"""

import logging
from typing import Union
from nemo_library_etl.adapter.reppl.config_models_reppl import ConfigRepPL
from nemo_library_etl.adapter._utils.enums import ETLAdapter, ETLStep
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library import NemoLibrary
import pandas as pd


class RepPLTransform:
    """
    Handles transformation of extracted RepPL data.
    
    This class manages the transformation phase of the RepPL ETL pipeline,
    providing methods to process, clean, and format the extracted data for loading
    into the target system.
    
    The transformer:
    - Uses NemoLibrary for core functionality and configuration
    - Integrates with Prefect logging for pipeline visibility
    - Applies business rules and data validation
    - Handles data type conversions and formatting
    - Provides data enrichment and calculated fields
    - Ensures data quality and consistency
    
    Attributes:
        nl (NemoLibrary): Core Nemo library instance for system integration.
        config: Configuration object from the Nemo library.
        logger: Prefect logger for pipeline execution tracking.
        cfg (PipelineRepPL): Pipeline configuration with transformation settings.
    """
    
    def __init__(
        self, 
        nl: NemoLibrary, 
        cfg: ConfigRepPL, 
        logger: Union[logging.Logger, object], 
        fh: ETLFileHandler,
    ) -> None:
        """
        Initialize the RepPL Transform instance.

        Sets up the transformer with the necessary library instances, configuration,
        and logging capabilities for the transformation process.

        Args:
            nl (NemoLibrary): Core Nemo library instance for system integration.
            cfg (PipelineRepPL): Pipeline configuration object containing
                                                          transformation settings and rules.
            logger (Union[logging.Logger, object]): Logger instance for recording execution details.
                                                   Can be a standard Python logger or Prefect logger.
        """
        self.nl = nl
        self.cfg = cfg
        self.logger = logger
        self.fh = fh

        super().__init__()           

    def transform(self) -> None:
        """
        Execute the main transformation process for RepPL data.
        
        This method orchestrates the complete transformation process by:
        1. Loading extracted data from the previous ETL phase
        2. Applying data validation and quality checks
        3. Performing data type conversions and formatting
        4. Applying business rules and logic
        5. Creating calculated fields and data enrichment
        6. Ensuring data consistency and integrity
        7. Preparing data for the loading phase
        
        The method provides detailed logging for monitoring and debugging purposes
        and handles errors gracefully to ensure pipeline stability.
        
        Note:
            The actual transformation logic needs to be implemented based on
            the specific RepPL system requirements and business rules.
        """
        self.logger.info("Transforming all RepPL objects")

        # load extracted data
        data = self.fh.readJSONL(step=ETLStep.EXTRACT, entity="pl")

        df = pd.DataFrame(data)

        # drop empty columns
        df = df.dropna(subset=["description"]).reset_index(drop=True)

        # transpose data frame
        df_transposed = df.set_index("description").T.reset_index()
        df_transposed.columns = ["bp"] + df_transposed.columns[1:].tolist()

        # convert DataFrame back to list of dicts for JSON serialization
        data_dict = df.to_dict(orient="records")
        self.fh.writeJSONL(
            step=ETLStep.TRANSFORM,
            data=data_dict,
            entity="pl",
        )
        self.logger.info("Transformation complete, data ready for loading")
