"""
HubSpotForecast ETL Transform Module.

This module handles the transformation phase of the HubSpotForecast ETL pipeline.
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
    HubSpotForecastTransform: Main class handling HubSpotForecast data transformation.
"""

import logging
from typing import Union
from nemo_library_etl.adapter.hubspotforecast.config_models_hubspotforecast import ConfigHubSpotForecast
from nemo_library_etl.adapter._utils.enums import ETLAdapter, ETLStep
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library import NemoLibrary

from nemo_library_etl.adapter.hubspotforecast.enums import HubSpotExtractStep, HubSpotTransformStep


class HubSpotForecastTransform:
    """
    Handles transformation of extracted HubSpotForecast data.
    
    This class manages the transformation phase of the HubSpotForecast ETL pipeline,
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
        cfg (PipelineHubSpotForecast): Pipeline configuration with transformation settings.
    """
    
    def __init__(
        self, 
        nl: NemoLibrary, 
        cfg: ConfigHubSpotForecast, 
        logger: Union[logging.Logger, object], 
        fh: ETLFileHandler,
    ) -> None:
        """
        Initialize the HubSpotForecast Transform instance.

        Sets up the transformer with the necessary library instances, configuration,
        and logging capabilities for the transformation process.

        Args:
            nl (NemoLibrary): Core Nemo library instance for system integration.
            cfg (PipelineHubSpotForecast): Pipeline configuration object containing
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
        Execute the main transformation process for HubSpotForecast data.
        
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
            the specific HubSpotForecast system requirements and business rules.
        """
        self.logger.info("Transforming all HubSpotForecast objects")

        # transform objects
        self.transform_deals_plain()
        self.transform_for_forecast()

    def transform_deals_plain(self) -> None:
        """
        Transform deals data for forecast call.
        """
        self.logger.info("Transforming deals data for forecast call")

        # Load extracted deals data
        deals = self.fh.readJSONL(
            step=ETLStep.EXTRACT,
            entity=HubSpotExtractStep.DEALS,
        )

        if not deals:
            raise ValueError("No deals data found to transform")

        # resolve mappings
        deals = self._resolve_mappings(deals)

        # enrich with company associations
        deals = self._add_company_associations(deals)

        # save transformed deals
        self.fh.writeJSONL(
            step=ETLStep.TRANSFORM,
            substep=HubSpotTransformStep.PLAIN_DEALS,
            data=deals,
            entity=HubSpotExtractStep.DEALS,
        )

    def _resolve_mappings(self, deals):
        pipelines = self.fh.readJSONL(
            step=ETLStep.EXTRACT,
            entity=HubSpotExtractStep.PIPELINES,
        )
        if not pipelines:
            raise ValueError("No pipelines data found to transform")

        deal_owners = self.fh.readJSONL(
            step=ETLStep.EXTRACT,
            entity=HubSpotExtractStep.DEAL_OWNERS,
        )
        if not deal_owners:
            raise ValueError("No deal owners data found to transform")

        users = self.fh.readJSONL(
            step=ETLStep.EXTRACT,
            entity=HubSpotExtractStep.USERS,
        )
        if not users:
            raise ValueError("No users data found to transform")

        # Map pipeline_id -> pipeline_label
        pipeline_label_by_id = {}
        # Map (pipeline_id, stage_id) -> stage_label
        stage_label_by_pipeline_and_id = {}
        # Global fallback: stage_id -> stage_label (last one wins if duplicated)
        global_stage_label_by_id = {}
        # deal owner
        owner_label_by_id = {}

        for o in deal_owners:
            o_id = o.get("id")
            o_label = o.get("email")
            if o_id:
                owner_label_by_id[o_id] = o_label

        for u in users:
            u_id = u.get("id")
            u_label = u.get("email")
            if u_id:
                owner_label_by_id[u_id] = u_label

        for p in pipelines:
            p_id = p.get("id")
            p_label = p.get("label")
            if p_id:
                pipeline_label_by_id[p_id] = p_label
            for s in p.get("stages", []):
                s_id = s.get("id")
                s_label = s.get("label")
                if p_id and s_id:
                    stage_label_by_pipeline_and_id[(p_id, s_id)] = s_label
                if s_id:
                    global_stage_label_by_id[s_id] = s_label

        # Track unresolved mappings
        unresolved_stages = set()
        unresolved_pipelines = set()
        unresolved_owners = set()

        # Map deal stage, pipeline, and owner
        for deal in deals:
            stage_key = (deal.get("pipeline"), deal.get("dealstage"))
            if stage_key in stage_label_by_pipeline_and_id:
                deal["dealstage"] = stage_label_by_pipeline_and_id[stage_key]
            else:
                unresolved_stages.add(stage_key)

            pipeline_key = deal.get("pipeline")
            if pipeline_key in pipeline_label_by_id:
                deal["pipeline"] = pipeline_label_by_id[pipeline_key]
            else:
                unresolved_pipelines.add(pipeline_key)

            owner_key = deal.get("hubspot_owner_id")
            if owner_key in owner_label_by_id:
                deal["hubspot_owner_id"] = owner_label_by_id[owner_key]
            else:
                unresolved_owners.add(owner_key)

        # Create a summary dictionary for unresolved mappings
        unresolved_summary = {
            "dealstages": list(unresolved_stages),
            "pipelines": list(unresolved_pipelines),
            "owners": list(unresolved_owners),
        }

        if unresolved_summary:
            self.logger.warning(f"Unresolved mappings found: {unresolved_summary}")

        return deals

    def _add_company_associations(self, deals):
        deal_companies = self.fh.readJSONL(
            step=ETLStep.EXTRACT,
            entity=HubSpotExtractStep.DEAL_COMPANIES,
        )

        if not deal_companies:
            raise ValueError("No deal companies data found to transform")

        company_details = self.fh.readJSONL(
            step=ETLStep.EXTRACT,
            entity=HubSpotExtractStep.COMPANY_DETAILS,
        )
        if not company_details:
            raise ValueError("No company details data found to transform")
        compdetail = {}
        for detail in company_details:
            compdetail[detail.get("company_id")] = detail

        # Map deal_id -> company_ids (still collect all, just in case)
        company_ids_by_deal_id = {}
        for association in deal_companies:
            company_ids_by_deal_id.setdefault(association.get("deal_id"), []).append(
                association.get("company_id")
            )

        # Enrich deals with single company_id property
        for deal in deals:
            company_ids = company_ids_by_deal_id.get(deal.get("id"), [])
            if company_ids:
                deal["company_id"] = company_ids[0]  # take the first one
                detail = compdetail.get(deal["company_id"])
                for key, value in detail.items():
                    deal[key] = value
                if len(company_ids) > 1:
                    self.logger.warning(
                        f"Deal ID {deal.get('id')} is associated with multiple companies: {company_ids}. "
                        f"Using the first one: {deal['company_id']}"
                    )
            else:
                deal["company_id"] = None

        return deals



    def transform_for_forecast(self) -> None:
        # Load transformed deals data
        deals = self.fh.readJSONL(
            step=ETLStep.TRANSFORM,
            substep=HubSpotTransformStep.PLAIN_DEALS,
            entity=HubSpotExtractStep.DEALS,
        )

        # dump the header
        header = [
            deal for deal in deals if deal.get("dealname").startswith("(FORECAST)")
        ]
        self.fh.writeJSONL(
            step=ETLStep.TRANSFORM,
            substep=HubSpotTransformStep.FORECAST,
            entity=HubSpotTransformStep.DEALS_FORECAST_HEADER,
            data=header,
        )

        # dump the deals itself
        forecast_deals = [
            deal
            for deal in deals
            if not deal.get("dealname", "").startswith("(FORECAST)")
            and deal.get("closedate")
            and deal.get("amount")
            and float(deal.get("amount")) > 0
            and not deal.get("dealstage") in ["Unqualified lead", "closed and lost"]
        ]
        self.fh.writeJSONL(
            step=ETLStep.TRANSFORM,
            substep=HubSpotTransformStep.FORECAST,
            entity=HubSpotTransformStep.DEALS_FORECAST_DEALS,
            data=forecast_deals,
        )
                        