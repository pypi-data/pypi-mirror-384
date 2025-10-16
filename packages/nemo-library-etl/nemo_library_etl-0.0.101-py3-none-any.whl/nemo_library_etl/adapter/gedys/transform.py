"""
Gedys ETL Transform Module.

This module handles the transformation phase of the Gedys ETL pipeline.
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
    GedysTransform: Main class handling Gedys data transformation.
"""

import logging
from typing import Union
from nemo_library_etl.adapter._utils.recursive_json_flattener import RecursiveJsonFlattener
from nemo_library_etl.adapter._utils.sentiment_analyzer import SentimentAnalyzer
from nemo_library_etl.adapter.gedys.config_models import PipelineGedys
from nemo_library_etl.adapter._utils.enums import ETLAdapter, ETLStep
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library import NemoLibrary

from nemo_library_etl.adapter.gedys.enums import GedysTransformStep


class GedysTransform:
    """
    Handles transformation of extracted Gedys data.
    
    This class manages the transformation phase of the Gedys ETL pipeline,
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
        cfg (PipelineGedys): Pipeline configuration with transformation settings.
    """
    
    def __init__(
        self, 
        nl: NemoLibrary, 
        cfg: PipelineGedys, 
        logger: Union[logging.Logger, object], 
        fh: ETLFileHandler,
    ) -> None:
        """
        Initialize the Gedys Transform instance.

        Sets up the transformer with the necessary library instances, configuration,
        and logging capabilities for the transformation process.

        Args:
            nl (NemoLibrary): Core Nemo library instance for system integration.
            cfg (PipelineGedys): Pipeline configuration object containing
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
        Execute the main transformation process for Gedys data.
        
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
            the specific Gedys system requirements and business rules.
        """
        self.logger.info("Transforming all Gedys objects")

        if self.cfg.transform.sentiment_analysis:
            self._sentiment_analysis()
        if self.cfg.transform.flatten:
            self._flatten()
        if self.cfg.transform.join:
            self._join()

    def _sentiment_analysis(self) -> None:
        self.logger.info("Performing sentiment analysis for Gedys objects")

        sentiment_analyzer = SentimentAnalyzer()

        for table, model in self.cfg.extract.tables.items():
            if model.active is False:
                self.logger.info(f"Skipping inactive table: {table}")
                continue

            data = self.fh.readJSONL(
                step=ETLStep.EXTRACT,
                entity=table,
                ignore_nonexistent=True,  # Ignore if file does not exist
            )
            if not data:
                self.logger.warning(
                    f"No data found for entity {table}. Skipping sentiment analysis."
                )
                continue

            if model.sentiment_analysis_fields:
                self.logger.info(f"Performing sentiment analysis for entity {table}")
                data = sentiment_analyzer.analyze_sentiment(
                    data=data,
                    sentiment_analysis_fields=model.sentiment_analysis_fields,
                )

            self.fh.writeJSONL(
                step=ETLStep.TRANSFORM,
                substep=GedysTransformStep.SENTIMENT,
                data=data,
                entity=table,
            )

    def _flatten(self) -> None:
        self.logger.info("Flattening Gedys objects")

        flattener = RecursiveJsonFlattener()

        for table, model in self.cfg.extract.tables.items():
            if model.active is False:
                self.logger.info(f"Skipping inactive table: {table}")
                continue

            data = self.fh.readJSONL(
                step=ETLStep.TRANSFORM,
                substep=GedysTransformStep.SENTIMENT,
                entity=table,
                ignore_nonexistent=True,  # Ignore if file does not exist
            )
            if not data:
                self.logger.warning(
                    f"No data found for entity {table}. Skipping flattener"
                )
                continue

            self.logger.info(f"Flattening data for entity {table}")
            flattened_data = flattener.flatten(data)

            self.fh.writeJSONL(
                step=ETLStep.TRANSFORM,
                substep=GedysTransformStep.FLATTEN,
                data=flattened_data,
                entity=table,
            )

    def _join(self) -> None:
        self.logger.info("Joining Gedys objects")

        flattener = RecursiveJsonFlattener()

        # Load base data from GEDYS
        companies = self.fh.readJSONL(
            step=ETLStep.TRANSFORM,
            substep=GedysTransformStep.FLATTEN,
            entity="Company",
        )
        if not companies:
            raise ValueError("No company data found for joining with opportunities.")

        contacts = self.fh.readJSONL(
            step=ETLStep.TRANSFORM,
            substep=GedysTransformStep.FLATTEN,
            entity="Contact",
        )
        if not contacts:
            raise ValueError("No contact data found for joining with opportunities.")

        opportunities = self.fh.readJSONL(
            step=ETLStep.TRANSFORM,
            substep=GedysTransformStep.FLATTEN,
            entity="Opportunity",
        )

        # data model
        # Comp -> Contact -> Opportunity
        # or Comp -> Opportunity

        # start with joining contacts to companies
        for company in companies:
            company["contact_join"] = [
                contact
                for contact in contacts
                if contact.get("RelatedMainParents.Oid", "") == company["Oid"]
                or contact.get("RelatedParents.Oid", "") == company["Oid"]
            ]

        # flatten this structure
        companies_with_contacts = flattener.flatten(companies)

        # now join opportunities with this flattened structure
        for company in companies_with_contacts:
            company["opportunity_join"] = [
                opportunity
                for opportunity in opportunities
                if opportunity.get("RelatedMainParents.Oid", "") == company["Oid"]
                or opportunity.get("RelatedParents.Oid", "") == company["Oid"]
                or opportunity.get("RelatedMainParents.Oid", "")
                == company.get("contact_join.Oid", "---")  # --- to ensure no match
                or opportunity.get("RelatedParents.Oid", "")
                == company.get("contact_join.Oid", "---")
            ]

        # finally flatten the whole structure again
        companies_with_contacts_and_opportunities = flattener.flatten(
            companies_with_contacts
        )

        # save the transformed data finally
        self.fh.writeJSONL(
            step=ETLStep.TRANSFORM,
            substep=GedysTransformStep.JOIN,
            data=companies_with_contacts_and_opportunities,
            entity="Company Joined",
        )
                
        