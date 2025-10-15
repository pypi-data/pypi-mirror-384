"""
RepPrices ETL Transform Module.

This module handles the transformation phase of the RepPrices ETL pipeline.
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
    RepPricesTransform: Main class handling RepPrices data transformation.
"""

import logging
from typing import Union
from nemo_library_etl.adapter.repprices.config_models_repprices import ConfigRepPrices
from nemo_library_etl.adapter._utils.enums import ETLAdapter, ETLStep
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library import NemoLibrary
import pandas as pd

PRICE_LIST_MAX_USER = 2001

class RepPricesTransform:
    """
    Handles transformation of extracted RepPrices data.
    
    This class manages the transformation phase of the RepPrices ETL pipeline,
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
        cfg (PipelineRepPrices): Pipeline configuration with transformation settings.
    """
    
    def __init__(
        self, 
        nl: NemoLibrary, 
        cfg: ConfigRepPrices, 
        logger: Union[logging.Logger, object], 
        fh: ETLFileHandler,
    ) -> None:
        """
        Initialize the RepPrices Transform instance.

        Sets up the transformer with the necessary library instances, configuration,
        and logging capabilities for the transformation process.

        Args:
            nl (NemoLibrary): Core Nemo library instance for system integration.
            cfg (PipelineRepPrices): Pipeline configuration object containing
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
        Execute the main transformation process for RepPrices data.
        
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
            the specific RepPrices system requirements and business rules.
        """
        self.logger.info("Transforming all RepPrices objects")

        # transform objects
                
        # load extracted data
        data = self.fh.readJSONL(
            step=ETLStep.EXTRACT,
            entity="pricelist")
        
        df = pd.DataFrame(data)
        
        # Adding a column for 0 users at the beginning of the DataFrame with all prices set to 0
        df.insert(2, "≤ 0", [0] * len(df))

        # Extracting tiers from the column headers and removing '≤'
        tiers = [int(col.split(" ")[-1]) for col in df.columns[2:] if "≤" in col]

        # Extracting the additional price step from the header of the last column
        # Assuming the header format is like '+ 32 User'
        additional_user_price_step_header = df.columns[-1]
        additional_user_price_step = int(additional_user_price_step_header.split(" ")[1])

        # Initialize a dictionary to store the prices for each product
        product_prices = {
            product: [] for product in df.iloc[:, 0]
        }  # Using product names from the first column

        # Price calculation
        for user in range(PRICE_LIST_MAX_USER):
            for i, product in enumerate(df.iloc[:, 0]):
                if user <= max(tiers):
                    # Finds the nearest lower and higher tier values
                    lower_bound = max([s for s in tiers if s <= user], default=0)
                    upper_bound = min([s for s in tiers if s >= user], default=max(tiers))

                    # Finds the corresponding indices
                    lower_index = tiers.index(lower_bound)
                    upper_index = tiers.index(upper_bound)

                    # Linear interpolation
                    if lower_bound != upper_bound:
                        unit_price = (
                            df.iloc[i, upper_index + 2] - df.iloc[i, lower_index + 2]
                        ) / (upper_bound - lower_bound)
                        price = df.iloc[i, lower_index + 2] + unit_price * (
                            user - lower_bound
                        )
                    else:
                        price = df.iloc[i, lower_index + 2]
                else:
                    # Calculating price for users > max(tiers)
                    additional_users = user - max(tiers)
                    additional_steps = additional_users // additional_user_price_step
                    price = df.iloc[i, -2] + additional_steps * df.iloc[i, -1]

                product_prices[product].append(price)

        # Creating a new DataFrame from the result dictionary
        result_df = pd.DataFrame(product_prices)

        # Setting the user count as the index
        result_df.index = range(PRICE_LIST_MAX_USER)

        # Adding a column for the user count
        result_df["user"] = result_df.index        
        
        # convert DataFrame back to list of dicts for JSON serialization
        data_dict = result_df.to_dict(orient="records")
        self.fh.writeJSONL(
            step=ETLStep.TRANSFORM,
            data=data_dict,
            entity="pricelist",
        )
        self.logger.info("Transformation complete, data ready for loading")                