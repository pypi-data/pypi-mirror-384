"""
Zentis ETL Extract Module.

This module handles the extraction phase of the Zentis ETL pipeline.
It provides functionality to extract data from Zentis systems and
prepare it for the transformation phase.

The extraction process:
1. Connects to the Zentis system using configured credentials
2. Iterates through configured tables and extracts data
3. Handles inactive tables by skipping them
4. Uses ETLFileHandler for data persistence
5. Provides comprehensive logging throughout the process

Classes:
    ZentisExtract: Main class handling Zentis data extraction.
"""

import logging
from pathlib import Path
from typing import Union
from nemo_library_etl.adapter.zentis.config_models_zentis import ConfigZentis
from nemo_library_etl.adapter._utils.enums import ETLAdapter, ETLStep
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library import NemoLibrary
import pandas as pd


class ZentisExtract:
    """
    Handles extraction of data from Zentis system.

    This class manages the extraction phase of the Zentis ETL pipeline,
    providing methods to connect to Zentis systems, retrieve data,
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
        cfg (PipelineZentis): Pipeline configuration with extraction settings.
    """

    def __init__(
        self,
        nl: NemoLibrary,
        cfg: ConfigZentis,
        logger: Union[logging.Logger, object],
        fh: ETLFileHandler,
    ) -> None:
        """
        Initialize the Zentis Extract instance.

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
        Execute the main extraction process for Zentis data.

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
            the specific Zentis system requirements.
        """
        self.logger.info("Extracting all Zentis objects")

        # extract objects
        for entity, file_cfg in self.cfg.extract.files.items():
            if not file_cfg.extract_active:
                self.logger.info(
                    f"Skipping extraction of file {file_cfg.file_path} as it is marked inactive"
                )
                continue

            file_path = Path(file_cfg.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File {file_cfg.file_path} does not exist.")

            self.logger.info(f"Extracting file {file_cfg.file_path}")

            match file_path.suffix:

                case ".csv":
                    dtype_mapping = {
                        field_name: data_type for field_name, data_type in file_cfg.datatypes.items()
                    }
                    logging.info(f"Using dtype mapping: {dtype_mapping}")
                    df = pd.read_csv(
                        file_path,
                        sep=file_cfg.separator,
                        decimal=file_cfg.decimal,
                        encoding=file_cfg.encoding,
                        dtype=dtype_mapping,
                    )
                case ".xlsx":
                    df = pd.read_excel(
                        file_cfg.file_path,
                        engine="openpyxl",
                    )
                case _:
                    raise ValueError(f"Unsupported file format: {file_path.suffix}")

            self.fh.writeJSONL(
                step=ETLStep.EXTRACT, data=df.to_dict(orient="records"), entity=entity
            )
            self.logger.info(
                f"Completed extraction for file {file_cfg.file_path} with {len(df):,} records"
            )
