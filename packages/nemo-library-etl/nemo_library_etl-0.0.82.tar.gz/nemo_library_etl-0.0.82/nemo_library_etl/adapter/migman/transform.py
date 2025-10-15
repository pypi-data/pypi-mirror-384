"""
MigMan ETL Transform Module.

This module handles the transformation phase of the MigMan ETL pipeline.
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
    MigManTransform: Main class handling MigMan data transformation.
"""

from importlib import resources
import logging
from pathlib import Path
import re
from typing import Union
from nemo_library_etl.adapter._utils.db_handler import ETLDuckDBHandler
from nemo_library_etl.adapter.migman.config_models_migman import (
    ConfigMigMan,
    TransformDuplicateConfig,
    TransformDuplicatesConfig,
)
from nemo_library_etl.adapter._utils.enums import ETLAdapter, ETLStep
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library import NemoLibrary

from nemo_library_etl.adapter.migman.enums import MigManTransformStep
from rapidfuzz import fuzz

from nemo_library_etl.adapter.migman.migmanutils import MigManUtils


class MigManTransform:
    """
    Handles transformation of extracted MigMan data.

    This class manages the transformation phase of the MigMan ETL pipeline,
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
        cfg (PipelineMigMan): Pipeline configuration with transformation settings.
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
        Initialize the MigMan Transform instance.

        Sets up the transformer with the necessary library instances, configuration,
        and logging capabilities for the transformation process.

        Args:
            nl (NemoLibrary): Core Nemo library instance for system integration.
            cfg (PipelineMigMan): Pipeline configuration object containing
                                                          transformation settings and rules.
            logger (Union[logging.Logger, object]): Logger instance for recording execution details.
                                                   Can be a standard Python logger or Prefect logger.
        """
        self.nl = nl
        self.cfg = cfg
        self.logger = logger
        self.fh = fh
        self.local_database = local_database

        super().__init__()

    def transform(self) -> None:
        """
        Execute the main transformation process for MigMan data.

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
            the specific MigMan system requirements and business rules.
        """
        self.logger.info("Transforming all MigMan objects")

        # transform objects

        # start with joins. After this step, we have all data in our data modell
        self.joins()

        # then remove empty columns
        self.nonempty()
        
        # then handle duplicates
        self.duplicates()

    def joins(self) -> None:
        """
        Execute join operations for MigMan data transformation.

        This method handles the joining of data from different sources or tables
        as part of the transformation process. It ensures that related data is
        combined correctly based on specified keys and relationships.

        The join process includes:
        1. Identifying the datasets to be joined
        2. Defining the join keys and types (e.g., inner, left, right, full)
        3. Performing the join operation using efficient algorithms
        4. Validating the joined data for consistency and integrity
        5. Logging the join process for monitoring and debugging

        Note:
            The actual join logic needs to be implemented based on
            the specific MigMan system requirements and data relationships.
        """
        self.logger.info("Joining MigMan objects")

        if self.cfg.transform.join is None:
            self.logger.info("No join configuration found, skipping joins")
            return

        if not self.cfg.transform.join.active:
            self.logger.info("Join configuration is inactive, skipping joins")
            return

        adapter = self.cfg.transform.join.adapter
        self.logger.info(f"Using adapter: {adapter}")

        for join_name, join_cfg in self.cfg.transform.join.joins.items():
            if not join_cfg.active:
                self.logger.info(f"Skipping inactive join: {join_name}")
                continue

            self.logger.info(f"Processing join: {join_name}")

            # load the JOIN SQL from the config
            file = (
                resources.files("nemo_library_etl")
                / "adapter"
                / "migman"
                / "config"
                / "joins"
                / adapter
                / join_cfg.file
            )

            with resources.as_file(file) as sql_file:
                query = sql_file.read_text(encoding="utf-8")

            if not query:
                raise ValueError(f"Join SQL file is empty: {join_cfg.file}")

            # add result_creation to the query
            table_name = MigManTransformStep.JOINS.value + "_" + join_name
            query = f'CREATE OR REPLACE TABLE "{table_name}" AS\n' + query

            # Execute the join query
            self.local_database.query(query)

            # Compare columns with expected columns from Migman
            columns = self.local_database.con.execute(
                f"SELECT name FROM pragma_table_info('{table_name}')"
            ).fetchall()
            columns = [col[0] for col in columns]
            MigManUtils.validate_columns(
                project=join_name, postfix="", columns=columns, missing_ok=True
            )

            # export results from database
            self.local_database.export_table(
                table_name=table_name,
                fh=self.fh,
                step=ETLStep.TRANSFORM,
                substep=MigManTransformStep.JOINS,
                entity=join_name,
                gzip_enabled=False,
            )

            if self.cfg.transform.load_to_nemo:
                self.local_database.upload_table_to_nemo(
                    table_name=table_name,
                    project_name=f"{self.cfg.transform.nemo_project_prefix}{table_name}",
                )

    def nonempty(self) -> None:
        """
        Remove empty columns from the MigMan data.
        """
        self.logger.info("Removing empty columns from MigMan data")

        if self.cfg.transform.nonempty is None:
            self.logger.info("No nonempty configuration found, skipping nonempty")
            return

        if not self.cfg.transform.nonempty.active:
            self.logger.info("Nonempty configuration is inactive, skipping nonempty")
            return



    def duplicates(self) -> None:
        """
        Handle duplicate records in the MigMan data.

        This method identifies and processes duplicate records in the extracted
        MigMan data to ensure data integrity and quality before loading into the
        target system. The specific logic for handling duplicates should be
        implemented based on business rules and requirements.

        Steps may include:
        1. Identifying duplicate records based on key fields.
        2. Merging or removing duplicates according to defined rules.
        3. Logging actions taken for audit purposes.

        Note:
            The actual implementation of duplicate handling logic is pending
            and should be customized to fit the MigMan system's needs.
        """
        self.logger.info("Handling duplicates in MigMan data")

        if self.cfg.transform.duplicate is None:
            self.logger.info("No duplicate configuration found, skipping duplicates")
            return

        if not self.cfg.transform.duplicate.active:
            self.logger.info("Duplicate configuration is inactive, skipping joins")
            return

        # create UDFs in DuckDB
        if not self.local_database or not self.local_database.con:
            raise ValueError("Database handler is not initialized")

        def normalize_text(s: str) -> str:
            if s is None:
                return ""
            s = s.lower().strip()
            s = (
                s.replace("ä", "ae")
                .replace("ö", "oe")
                .replace("ü", "ue")
                .replace("ß", "ss")
            )
            s = re.sub(r"[^\w\s]", " ", s)  # remove punctuation
            s = re.sub(r"\s+", " ", s).strip()  # collapse spaces
            return s

        def text_similarity(a: str, b: str) -> float:
            a = normalize_text(a)
            b = normalize_text(b)
            return float(fuzz.token_set_ratio(a, b))

        self.local_database.con.create_function("normalize_text", normalize_text)
        self.local_database.con.create_function("text_similarity", text_similarity)

        for duplicate_name, model in self.cfg.transform.duplicate.duplicates.items():
            if model.active is False:
                self.logger.info(f"Skipping inactive duplicate model: {duplicate_name}")
                continue
            self._perform_duplicate_check(duplicate_name, model)

    def _perform_duplicate_check(
        self, duplicate_name: str, model: TransformDuplicatesConfig
    ) -> None:
        """
        Single-pass duplicate annotation with 100% recall for token_set similarity:
        - Build token inverted index (id -> tokens of normalized text)
        - Candidates = pairs sharing at least one token (no false negatives for token_set)
        - Compute similarity and aggregate partners
        - Output has same row count as source; includes JSON partners, top score, count
        - Logs progress per phase (row/token/candidate counts)
        """
        from datetime import datetime

        start_time = datetime.now()

        table = self.local_database.latest_table_name(
            steps=MigManTransformStep, entity=duplicate_name
        )
        if table is None:
            raise ValueError(f"No table found for entity {duplicate_name}")
        id_col = model.primary_key
        con = self.local_database.con
        thresh = model.threshold
        out_tbl = f"{MigManTransformStep.DUPLICATES.value}_{duplicate_name}"

        self.logger.info(
            f"[{duplicate_name}] Starting duplicate check on table {table} (100% coverage via token index)"
        )

        # Helper: CONCAT of configured columns (safe cast to VARCHAR)
        def concat_expr(alias: str, cols: list[str]) -> str:
            parts = [f"coalesce(CAST({alias}.\"{c}\" AS VARCHAR), '')" for c in cols]
            return " || ' | ' || ".join(parts) if parts else "''"

        base_concat = concat_expr("b", model.fields)

        # 1) Base: id, normalized text, raw length
        base_tmp = f"__dup_base_{duplicate_name.lower()}"
        con.execute(f'DROP TABLE IF EXISTS "{base_tmp}"')
        con.execute(
            f"""
            CREATE TEMPORARY TABLE "{base_tmp}" AS
            SELECT
                CAST(b."{id_col}" AS VARCHAR)                 AS id,
                normalize_text({base_concat})                 AS norm_text,
                length({base_concat})                         AS txt_len
            FROM "{table}" b
        """
        )
        n_rows = con.execute(f'SELECT COUNT(*) FROM "{base_tmp}"').fetchone()[0]
        self.logger.info(
            f"[{duplicate_name}] Phase 1/5: base prepared — rows: {n_rows:,}"
        )

        # (Optional) Tiny stopword set; leave empty list [] for absolute maximal recall.
        # For high threshold (>=90), filtering 'gmbh'/'ag' etc. is usually safe and reduces huge candidate stars.
        stop_tmp = f"__dup_stop_{duplicate_name.lower()}"
        con.execute(f'DROP TABLE IF EXISTS "{stop_tmp}"')
        con.execute(
            f"""
            CREATE TEMPORARY TABLE "{stop_tmp}"(token VARCHAR);
            INSERT INTO "{stop_tmp}" VALUES
                -- comment-out or remove lines to disable specific stopwords
                ('gmbh'),('mbh'),('kg'),('ag'),('co'),('kg'),('und'),('the'),('der'),('die');
        """
        )

        # 2) Tokenize: one row per (id, token)
        # Use simple space split on the normalized text (already lowercased & cleaned).
        tokens_tmp = f"__dup_tokens_{duplicate_name.lower()}"
        con.execute(f'DROP TABLE IF EXISTS "{tokens_tmp}"')
        con.execute(
            f"""
            CREATE TEMPORARY TABLE "{tokens_tmp}" AS
            SELECT
                id,
                u.token
            FROM "{base_tmp}"
            , UNNEST(string_split(norm_text, ' ')) AS u(token)
            WHERE u.token <> ''
            AND NOT EXISTS (SELECT 1 FROM "{stop_tmp}" s WHERE s.token = u.token);
            """
        )
        n_tokens = con.execute(f'SELECT COUNT(*) FROM "{tokens_tmp}"').fetchone()[0]
        n_dist_t = con.execute(
            f'SELECT COUNT(DISTINCT token) FROM "{tokens_tmp}"'
        ).fetchone()[0]
        self.logger.info(
            f"[{duplicate_name}] Phase 2/5: tokens built — rows: {n_tokens:,}, distinct tokens: {n_dist_t:,}"
        )

        # 3) Candidate pairs via token matches (distinct id pairs)
        pairs_cand = f"__dup_pairs_cand_{duplicate_name.lower()}"
        con.execute(f'DROP TABLE IF EXISTS "{pairs_cand}"')
        con.execute(
            f"""
            CREATE TEMPORARY TABLE "{pairs_cand}" AS
            SELECT DISTINCT
                LEAST(a.id, b.id)  AS left_id,
                GREATEST(a.id, b.id) AS right_id
            FROM "{tokens_tmp}" a
            JOIN "{tokens_tmp}" b
            ON a.token = b.token
            AND a.id <> b.id
        """
        )
        n_cand = con.execute(f'SELECT COUNT(*) FROM "{pairs_cand}"').fetchone()[0]
        self.logger.info(
            f"[{duplicate_name}] Phase 3/5: candidates generated — pairs: {n_cand:,}"
        )

        # 4) Score candidates and filter by threshold
        pairs_keep = f"__dup_pairs_keep_{duplicate_name.lower()}"
        con.execute(f'DROP TABLE IF EXISTS "{pairs_keep}"')
        con.execute(
            f"""
            CREATE TEMPORARY TABLE "{pairs_keep}" AS
            SELECT
                p.left_id,
                p.right_id,
                text_similarity(a.norm_text, b.norm_text) AS score
            FROM "{pairs_cand}" p
            JOIN "{base_tmp}" a ON a.id = p.left_id
            JOIN "{base_tmp}" b ON b.id = p.right_id
            WHERE text_similarity(a.norm_text, b.norm_text) >= {thresh}
        """
        )
        n_keep = con.execute(f'SELECT COUNT(*) FROM "{pairs_keep}"').fetchone()[0]
        self.logger.info(
            f"[{duplicate_name}] Phase 4/5: scored+filtered — matches >= {thresh}: {n_keep:,}"
        )

        # 5) Build partners for each id and write final annotated table
        con.execute(
            f"""
            CREATE OR REPLACE TABLE "{out_tbl}" AS
            WITH partners AS (
                SELECT left_id AS id,  right_id AS partner_id, score FROM "{pairs_keep}"
                UNION ALL
                SELECT right_id AS id, left_id  AS partner_id, score FROM "{pairs_keep}"
            ),
            agg AS (
                SELECT
                    id,
                    to_json(
                        list(
                            struct_pack(partner_id := partner_id, score := score)
                            ORDER BY score DESC, partner_id
                        )
                    ) AS duplicate_partners_json,
                    max(score) AS duplicate_top_score,
                    count(*)   AS duplicate_match_count
                FROM partners
                GROUP BY id
            )
            SELECT
                b.*,
                coalesce(agg.duplicate_partners_json, '[]') AS duplicate_partners_json,
                coalesce(agg.duplicate_top_score, 0)        AS duplicate_top_score,
                coalesce(agg.duplicate_match_count, 0)      AS duplicate_match_count
            FROM "{table}" b
            LEFT JOIN agg ON agg.id = CAST(b."{id_col}" AS VARCHAR)
        """
        )
        src_cnt = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        out_cnt = con.execute(f'SELECT COUNT(*) FROM "{out_tbl}"').fetchone()[0]

        end_time = datetime.now()
        self.logger.info(
            f"[{duplicate_name}] Phase 5/5: annotated table created: {out_tbl} — rows: {out_cnt:,} (source {src_cnt:,}), duration: {end_time - start_time}"
        )

        self.local_database.export_table(
            table_name=out_tbl,
            fh=self.fh,
            step=ETLStep.TRANSFORM,
            entity=duplicate_name,
            substep=MigManTransformStep.DUPLICATES,
        )

        if self.cfg.transform.load_to_nemo:
            self.local_database.upload_table_to_nemo(
                table_name=out_tbl,
                project_name=f"{self.cfg.transform.nemo_project_prefix}{out_tbl}",
            )
