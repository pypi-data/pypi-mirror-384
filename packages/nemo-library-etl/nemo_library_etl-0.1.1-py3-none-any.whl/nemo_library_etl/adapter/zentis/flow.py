"""
Zentis ETL Flow Module.

This module defines the Prefect workflow for the Zentis ETL process. It orchestrates
the extraction, transformation, and loading of data from Zentis systems into Nemo
using Prefect tasks and flows for robust pipeline execution.

The flow consists of three main phases:
1. Extract: Retrieve data from Zentis system
2. Transform: Process and clean the extracted data
3. Load: Insert the transformed data into Nemo

Each phase can be individually enabled/disabled through configuration settings.
"""

import logging
from pathlib import Path
from typing import Union, cast
from nemo_library import NemoLibrary
from prefect import flow, task, get_run_logger
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library_etl.adapter.zentis.config_models_zentis import ConfigZentis
from nemo_library_etl.adapter._utils.config import load_config
from nemo_library_etl.adapter.zentis.extract import ZentisExtract
from nemo_library_etl.adapter.zentis.transform import ZentisTransform
from nemo_library_etl.adapter.zentis.load import ZentisLoad


@flow(name="Zentis ETL Flow", log_prints=True)
def zentis_flow(args) -> None:
    """
    Main Prefect flow for the Zentis ETL pipeline.

    This flow orchestrates the complete ETL process for Zentis data, including:
    - Loading pipeline configuration from JSON files
    - Conditionally executing extract, transform, and load phases based on configuration
    - Comprehensive logging and error handling throughout the process
    - Integration with Prefect for workflow orchestration, monitoring, and retry logic

    The flow follows a sequential execution pattern where each phase (extract, transform, load)
    is executed as a separate Prefect task. Each phase can be individually enabled or disabled
    through the pipeline configuration settings.

    Pipeline Configuration:
        The flow loads its configuration using the load_pipeline_config utility, which reads
        settings from JSON configuration files. The configuration includes:
        - Extract settings: table specifications and activation flags
        - Transform settings: business rules and data processing parameters
        - Load settings: target system configuration and batch parameters
        - Global settings: phase activation flags (extract_active, transform_active, load_active)

    Error Handling:
        Any exceptions raised during the ETL process will be logged and propagated by Prefect,
        enabling built-in retry mechanisms and failure notifications.

    Returns:
        None

    Raises:
        Exception: Any exception raised during the ETL process will be logged
                  and propagated by Prefect for proper error handling and monitoring.
    """
    logger = get_run_logger()
    logger.info("Starting Zentis ETL Flow")

    # load config
    nl = NemoLibrary(
        config_file=(args["config_ini"] if "config_ini" in args else None),
        environment=(args["environment"] if "environment" in args else None),
        tenant=(args["tenant"] if "tenant" in args else None),
        userid=(args["userid"] if "userid" in args else None),
        password=(args["password"] if "password" in args else None),
    )
    cfg: ConfigZentis = cast(
        ConfigZentis,
        load_config(
            adapter="Zentis",
            config_json_path=(
                Path(args["config_json"])
                if "config_json" in args and args["config_json"]
                else None
            ),
        ),
    )
    fh: ETLFileHandler = ETLFileHandler(nl=nl, cfg=cfg, logger=logger)

    # run steps
    if cfg.extract.extract_active:
        logger.info("Extracting objects from Zentis")
        extract(nl=nl, cfg=cfg, logger=logger, fh=fh)

    if cfg.transform.transform_active:
        logger.info("Transforming Zentis objects")
        transform(nl=nl, cfg=cfg, logger=logger, fh=fh)

    if cfg.load.load_active:
        logger.info("Loading Zentis objects")
        load(nl=nl, cfg=cfg, logger=logger, fh=fh)

    logger.info("Zentis ETL Flow finished")


@task(name="Extract All Objects from Zentis")
def extract(
    nl: NemoLibrary,
    cfg: ConfigZentis,
    logger: Union[logging.Logger, object],
    fh: ETLFileHandler,
) -> None:
    """
    Prefect task to extract data from Zentis system.

    This task handles the extraction phase of the ETL pipeline, retrieving
    data from the Zentis system based on the configuration settings.
    It manages table-specific extraction settings and respects activation flags.

    Args:
        cfg (PipelineZentis): Pipeline configuration containing extraction settings,
                                                      including table configurations and activation flags.
        logger (Union[logging.Logger, object]): Logger instance for recording execution details.
                                               Can be a standard Python logger or Prefect logger.

    Returns:
        None

    Note:
        The actual extraction logic is delegated to the ZentisExtract class.
    """
    logger.info("Extracting all Zentis objects")
    extractor = ZentisExtract(nl=nl, cfg=cfg, logger=logger, fh=fh)
    extractor.extract()


@task(name="Transform Objects")
def transform(
    nl: NemoLibrary,
    cfg: ConfigZentis,
    logger: Union[logging.Logger, object],
    fh: ETLFileHandler,
) -> None:
    """
    Prefect task to transform extracted Zentis data.

    This task handles the transformation phase of the ETL pipeline, processing
    and cleaning the extracted data to prepare it for loading into Nemo.
    It applies business rules, data validation, and formatting operations.

    Args:
        cfg (PipelineZentis): Pipeline configuration containing transformation settings,
                                                      including business rules and data processing parameters.
        logger (Union[logging.Logger, object]): Logger instance for recording execution details.
                                               Can be a standard Python logger or Prefect logger.

    Returns:
        None

    Note:
        The actual transformation logic is delegated to the ZentisTransform class.
    """
    logger.info("Transforming Zentis objects")
    transformer = ZentisTransform(nl=nl, cfg=cfg, logger=logger, fh=fh)
    transformer.transform()


@task(name="Load Objects")
def load(
    nl: NemoLibrary,
    cfg: ConfigZentis,
    logger: Union[logging.Logger, object],
    fh: ETLFileHandler,
) -> None:
    """
    Prefect task to load transformed data into target system.

    This task handles the loading phase of the ETL pipeline, inserting
    the transformed data into the target system with proper error handling
    and performance optimization.

    Args:
        cfg (PipelineZentis): Pipeline configuration containing load settings,
                                                      including target system configuration and batch parameters.
        logger (Union[logging.Logger, object]): Logger instance for recording execution details.
                                               Can be a standard Python logger or Prefect logger.

    Returns:
        None

    Note:
        The actual loading logic is delegated to the ZentisLoad class.
    """
    logger.info("Loading Zentis objects into target system")
    loader = ZentisLoad(nl=nl, cfg=cfg, logger=logger, fh=fh)
    loader.load()
