"""
HubSpotForecast ETL Extract Module.

This module handles the extraction phase of the HubSpotForecast ETL pipeline.
It provides functionality to extract data from HubSpotForecast systems and 
prepare it for the transformation phase.

The extraction process:
1. Connects to the HubSpotForecast system using configured credentials
2. Iterates through configured tables and extracts data
3. Handles inactive tables by skipping them
4. Uses ETLFileHandler for data persistence
5. Provides comprehensive logging throughout the process

Classes:
    HubSpotForecastExtract: Main class handling HubSpotForecast data extraction.
"""

from datetime import datetime
import logging
from typing import Union
from nemo_library_etl.adapter.hubspotforecast.config_models_hubspotforecast import ConfigHubSpotForecast
from nemo_library_etl.adapter._utils.enums import ETLAdapter, ETLStep
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library import NemoLibrary
from nemo_library_etl.adapter.hubspotforecast.symbols import (
    DEAL_PROPERTIES,
    DEAL_PROPERTIES_WITH_HISTORY,
)
from hubspot import HubSpot
from hubspot.crm.associations.models.batch_input_public_object_id import (
    BatchInputPublicObjectId,
)
from hubspot.crm.objects import BatchReadInputSimplePublicObjectId, SimplePublicObjectId

from nemo_library_etl.adapter.hubspotforecast.enums import HubSpotExtractStep


class HubSpotForecastExtract:
    """
    Handles extraction of data from HubSpotForecast system.
    
    This class manages the extraction phase of the HubSpotForecast ETL pipeline,
    providing methods to connect to HubSpotForecast systems, retrieve data,
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
        cfg (PipelineHubSpotForecast): Pipeline configuration with extraction settings.
    """
    
    def __init__(
        self, 
        nl: NemoLibrary, 
        cfg: ConfigHubSpotForecast, 
        logger: Union[logging.Logger, object], 
        fh: ETLFileHandler,
    ) -> None:
        """
        Initialize the HubSpotForecast Extract instance.
        
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
        self.hs = self._getHubSpotAPIToken()

        super().__init__()            
    
    def extract(self) -> None:
        """
        Execute the main extraction process for HubSpotForecast data.
        
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
            the specific HubSpotForecast system requirements.
        """
        self.logger.info("Extracting all HubSpotForecast objects")

        # extract objects
        self.extract_pipelines()
        self.extract_deals()
        self.extract_deal_owners()
        self.extract_deal_companies()
        self.extract_companies()
        self.extract_users()

    def _getHubSpotAPIToken(self) -> HubSpot:
        """
        Initializes and returns a HubSpot API client using the API token from the provided configuration.

        Args:
            config (ConfigHandler): An instance of ConfigHandler that contains configuration details,
                                    including the HubSpot API token.

        Returns:
            HubSpot: An instance of the HubSpot API client initialized with the API token.
        """
        hubspotAPIToken = self.nl.config.get_hubspot_api_token()
        if not hubspotAPIToken:
            raise ValueError("HubSpot API token is missing in the configuration.")
        hs = HubSpot(access_token=hubspotAPIToken)
        return hs

    def extract_pipelines(self) -> None:
        pipelines = self.hs.crm.pipelines.pipelines_api.get_all(object_type="deals")

        # dump the data to a file
        self.fh.writeJSONL(
            step=ETLStep.EXTRACT,
            data=pipelines,
            entity=HubSpotExtractStep.PIPELINES,
        )

    def extract_deals(self) -> None:
        """
        Extract data from HubSpot API and save to files.
        """

        # load all deals

        pipelines = self.fh.readJSONL(
            step=ETLStep.EXTRACT,
            entity=HubSpotExtractStep.PIPELINES,
        )
        if not pipelines:
            raise ValueError("No pipelines data found to transform")
        pipeline_map = {p["label"].lower(): p["id"] for p in pipelines}

        filter_deal_pipelines = (
            self.cfg.extract.deal_pipelines
            if self.cfg.extract.deal_pipelines != ["*"]
            else list(pipeline_map.keys())
        )
        if not filter_deal_pipelines:
            raise ValueError("No pipelines configured to extract deals from")

        self.logger.info(f"Filtering deals by pipelines: {filter_deal_pipelines}")

        # Hubspot returns a proprietary date format. We normalize this into iso
        def normalize_dates(obj: dict) -> dict:
            cd = obj.get("closedate")
            if isinstance(cd, str) and cd.endswith("Z"):
                try:
                    dt = datetime.fromisoformat(cd[:-1] + "+00:00")
                    for field in ["createdate", "closedate", "hs_lastmodifieddate"]:
                        if field in obj:
                            obj[field] = dt.date().isoformat()  # "2024-03-08"
                except ValueError:
                    pass  # falls Format mal anders aussieht
            return obj

        with self.fh.streamJSONL(
            step=ETLStep.EXTRACT,
            entity=HubSpotExtractStep.DEALS,
        ) as writer:
            for pipeline_label in filter_deal_pipelines:
                pipeline_id = pipeline_map.get(pipeline_label.lower())
                if not pipeline_id:
                    raise ValueError(
                        f"Pipeline '{pipeline_label}' not found in pipelines metadata"
                    )

                after = None
                while True:
                    search_request = {
                        "filterGroups": [
                            {
                                "filters": [
                                    {
                                        "propertyName": "pipeline",
                                        "operator": "EQ",
                                        "value": pipeline_id,
                                    }
                                ]
                            }
                        ],
                        "properties": DEAL_PROPERTIES,
                        "limit": 100,
                    }
                    if after:
                        search_request["after"] = after

                    res = self.hs.crm.deals.search_api.do_search(search_request)

                    for deal in res.results:
                        rec = {"id": deal.id, **(deal.properties or {})}
                        writer.write_one(normalize_dates(rec))

                    # pagination handling
                    after = getattr(getattr(res, "paging", None), "next", None)
                    after = getattr(after, "after", None)
                    if not after:
                        break

    def extract_deal_owners(self) -> None:

        # load deal owner
        owners = self.hs.crm.owners.get_all(archived=True)

        # dump the data to a file
        self.fh.writeJSONL(
            step=ETLStep.EXTRACT,
            data=owners,
            entity=HubSpotExtractStep.DEAL_OWNERS,
        )

    def extract_deal_companies(self) -> None:

        # Load extracted deals data
        deals = self.fh.readJSONL(
            step=ETLStep.EXTRACT,
            entity=HubSpotExtractStep.DEALS,
        )

        if not deals:
            raise ValueError("No deals data found to transform")

        # we just need the IDs of the deals
        deal_ids = list(set([deal.get("id") for deal in deals]))
        if not deal_ids:
            raise ValueError("No deal IDs found to extract companies for")

        self.logger.info(
            f"Extracting deal-company associations for {len(deal_ids):,} deals"
        )

        batch_size = 1000  # HubSpot API Limit

        with self.fh.streamJSONL(
            step=ETLStep.EXTRACT,
            entity=HubSpotExtractStep.DEAL_COMPANIES,
        ) as writer:

            for i in range(0, len(deal_ids), batch_size):
                batch_ids = deal_ids[i : i + batch_size]
                batch_input = BatchInputPublicObjectId(inputs=batch_ids)

                associations = self.hs.crm.associations.batch_api.read(
                    from_object_type="deals",
                    to_object_type="company",
                    batch_input_public_object_id=batch_input,
                )

                for result in associations.results:
                    deal_id = result._from.id
                    to_dict = result.to
                    for to in to_dict:
                        rec = {"deal_id": deal_id, "company_id": to.id}
                        writer.write_one(rec)

    def extract_companies(self) -> None:

        # Load extracted deals data
        deal_companies = self.fh.readJSONL(
            step=ETLStep.EXTRACT,
            entity=HubSpotExtractStep.DEAL_COMPANIES,
        )
        if not deal_companies:
            raise ValueError("No deal companies data found to transform")

        company_ids = list(
            set([deal_company.get("company_id") for deal_company in deal_companies])
        )

        self.logger.info(f"Extracting {len(company_ids):,} companies from HubSpot")
        total_companies = len(company_ids)
        # Define the properties you want to fetch (e.g., "industry", "phone", etc.)
        properties_to_fetch = [
            "name",
            "domain",
            "industry",
            "numberofemployees",
            "annualrevenue",
        ]

        batch_size = 100

        with self.fh.streamJSONL(
            step=ETLStep.EXTRACT,
            entity=HubSpotExtractStep.COMPANY_DETAILS,
        ) as writer:

            for i in range(0, total_companies, batch_size):
                batch = company_ids[i : i + batch_size]

                # Using the search API to fetch company details with specific properties
                filter_group = {
                    "filters": [
                        {
                            "propertyName": "hs_object_id",
                            "operator": "IN",
                            "values": batch,
                        }
                    ]
                }
                search_request = {
                    "filterGroups": [filter_group],
                    "properties": properties_to_fetch,
                    "limit": batch_size,
                }

                company_infos = self.hs.crm.companies.search_api.do_search(search_request)

                for company_info in company_infos.results:
                    rec = {
                        "company_id": company_info.id,
                        "company_name": company_info.properties.get("name", ""),
                        "company_domain": company_info.properties.get("domain", ""),
                        "company_industry": company_info.properties.get("industry", ""),
                        "company_numberofemployees": company_info.properties.get(
                            "numberofemployees", ""
                        ),
                        "company_annualrevenue": company_info.properties.get(
                            "annualrevenue", ""
                        ),
                    }
                    writer.write_one(rec)

    def extract_users(self) -> None:
        # load user

        limit = 100
        after = None

        with self.fh.streamJSONL(
            step=ETLStep.EXTRACT,
            entity=HubSpotExtractStep.USERS,
        ) as writer:

            while True:
                page = self.hs.settings.users.users_api.get_page(after=after, limit=limit)

                # page.results is a list of PublicUser
                for user in page.results:
                    writer.write_one(user.to_dict())

                # pagination handling
                after = getattr(getattr(page, "paging", None), "next", None)
                after = getattr(after, "after", None)
                if not after:
                    break

