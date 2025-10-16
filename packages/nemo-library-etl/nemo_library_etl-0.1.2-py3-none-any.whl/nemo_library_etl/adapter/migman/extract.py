"""
MigMan ETL Extract Module.

This module handles the extraction phase of the MigMan ETL pipeline.
It provides functionality to extract data from MigMan systems and
prepare it for the transformation phase.

The extraction process:
1. Connects to the MigMan system using configured credentials
2. Iterates through configured tables and extracts data
3. Handles inactive tables by skipping them
4. Uses ETLFileHandler for data persistence
5. Provides comprehensive logging throughout the process

Classes:
    MigManExtract: Main class handling MigMan data extraction.
"""

from importlib import resources
import logging
from pathlib import Path
import tempfile
from typing import Union
from nemo_library_etl.adapter._utils.db_handler_local import ETLDuckDBHandler
from nemo_library_etl.adapter._utils.db_handler_source import DatabaseHandlerSource
from nemo_library_etl.adapter.migman.config_models_migman import ConfigMigMan
from nemo_library_etl.adapter._utils.enums import ETLAdapter, ETLStep
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library import NemoLibrary

from nemo_library_etl.adapter.migman.migmanutils import MigManUtils
from hdbcli import dbapi


class MigManExtract:
    """
    Handles extraction of data from MigMan system.

    This class manages the extraction phase of the MigMan ETL pipeline,
    providing methods to connect to MigMan systems, retrieve data,
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
        cfg (PipelineMigMan): Pipeline configuration with extraction settings.
    """

    def __init__(
        self,
        nl: NemoLibrary,
        cfg: ConfigMigMan,
        logger: Union[logging.Logger, object],
        fh: ETLFileHandler,
        local_database: ETLDuckDBHandler,
    ) -> None:
        """
        Initialize the MigMan Extract instance.

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
        self.local_database = local_database

        super().__init__()

    def extract(self) -> None:
        """
        Execute the main extraction process for MigMan data.

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
            the specific MigMan system requirements.
        """
        self.logger.info("Extracting all MigMan objects")

        # extract objects
        dbsrc = DatabaseHandlerSource(
            nl=self.nl,
            cfg=self.cfg,
            logger=self.logger,
            fh=self.fh,
        )

        for adapter in [ETLAdapter.INFORCOM, ETLAdapter.SAPECC]:
            if getattr(self.cfg.extract, f"{adapter.value}").active:
                try:
                    self.logger.info(f"Starting extraction for {adapter} ...")

                    # identify tables to extract
                    tables_to_extract, fields_to_extract = self.get_tables_and_fields(
                        adapter.value
                    )

                    self.logger.info(
                        f"Tables to extract for {adapter}: {tables_to_extract}"
                    )
                    self.logger.info(
                        f"Fields to extract for {adapter}: {fields_to_extract}"
                    )

                    # connect source database
                    match adapter:
                        case ETLAdapter.INFORCOM:
                            conn = dbsrc.connect_odbc(
                                odbc_connstr=self.cfg.extract.inforcom.odbc_connstr,
                                timeout=self.cfg.extract.inforcom.timeout,
                            )
                        case ETLAdapter.SAPECC:
                            conn = dbsrc.connect_hdb(
                                address=self.cfg.extract.sapecc.address,
                                port=self.cfg.extract.sapecc.port,
                                user=self.cfg.extract.sapecc.user,
                                password=self.cfg.extract.sapecc.password,
                                autocommit=self.cfg.extract.sapecc.autocommit,
                            )
                        case _:
                            raise ValueError(f"Unknown adapter: {adapter}")

                    if not conn:
                        raise ConnectionError(f"Failed to connect to {adapter} database")

                    # extract tables
                    for table_name in tables_to_extract:
                        self.logger.info(
                            f"Extracting table {table_name} from {adapter} ..."
                        )
                        query = f"SELECT {', '.join(fields_to_extract.get(table_name, []))} FROM {self.cfg.extract.inforcom.table_prefix}{table_name}"
                        self.logger.info(f"Using query: {query}")
                        dbsrc.generic_odbc_extract(
                            conn=conn,
                            query=query,
                            entity=table_name,
                            step=ETLStep.EXTRACT,
                            chunksize=self.cfg.extract.inforcom.chunk_size,
                        )

                        self.local_database.ingest_jsonl(
                            step=ETLStep.EXTRACT,
                            entity=table_name,
                            ignore_nonexistent=True,
                            create_mode="replace",  # or "append"
                            table_name=table_name,  # keep your original table name
                            add_metadata=True,  # adds _source_path & _ingested_at
                        )

                        if self.cfg.extract.load_to_nemo:
                            self.local_database.upload_table_to_nemo(
                                table_name=table_name,
                                project_name=f"{self.cfg.extract.nemo_project_prefix}{table_name}",
                                delete_temp_files=self.cfg.extract.delete_temp_files,
                            )
                            
                    conn.close()
                    self.logger.info(f"Completed extraction for {adapter}.")
                except Exception as e:
                    self.logger.error(f"Error during extraction for {adapter}: {e}")
                    raise
                finally:
                    try:
                        if conn:
                            conn.cursor().close()
                            conn.close()
                    except Exception as close_err:
                        self.logger.warning(
                            f"Failed to close connection for {adapter}: {close_err}"
                        )
            else:
                self.logger.info(f"Skipping extraction for {adapter} (inactive) ...")
                continue

    def get_tables_and_fields(self, adapter) -> tuple[list[str], dict[str, list[str]]]:

        tables_to_extract = []
        fields_to_extract = {}
        if getattr(self.cfg.extract, f"{adapter}").table_selector == "all":
            tables_to_extract = getattr(self.cfg.extract, f"{adapter}").tables
            fields_to_extract = {table: ["*"] for table in tables_to_extract}
        elif getattr(self.cfg.extract, f"{adapter}").table_selector == "join_parser":
            for project in MigManUtils.get_migman_projects(self.cfg):

                join_cfg = self.cfg.transform.join.joins.get(project)
                if not join_cfg:
                    raise ValueError(
                        f"No join configuration found for project: {project}"
                    )

                indiv_file = Path(f"./config/{adapter}/joins/") / join_cfg.file
                if indiv_file.exists():
                    with indiv_file.open("r", encoding="utf-8") as f:
                        query = f.read()
                else:
                    file = (
                        resources.files("nemo_library_etl")
                        / "adapter"
                        / "migman"
                        / "config"
                        / "joins"
                        / f"{adapter}"
                        / join_cfg.file
                    )

                    with resources.as_file(file) as sql_file:
                        query = sql_file.read_text(encoding="utf-8")

                if not query:
                    raise ValueError(f"Join SQL file is empty: {join_cfg.file}")

                tables_to_extract.extend(self.local_database.extract_tables(sql=query))
                fields_in_query = self.local_database.extract_fields_by_base_table(
                    sql=query
                )
                for table, fields in fields_in_query.items():
                    fields_to_extract.setdefault(table, []).extend(fields)

        tables_to_extract = list(set(tables_to_extract))  # deduplicate
        return tables_to_extract, fields_to_extract
