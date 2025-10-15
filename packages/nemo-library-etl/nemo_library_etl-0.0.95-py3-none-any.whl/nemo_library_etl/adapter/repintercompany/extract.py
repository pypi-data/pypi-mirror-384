"""
RepIntercompany ETL Extract Module.

This module handles the extraction phase of the RepIntercompany ETL pipeline.
It provides functionality to extract data from RepIntercompany systems and 
prepare it for the transformation phase.

The extraction process:
1. Connects to the RepIntercompany system using configured credentials
2. Iterates through configured tables and extracts data
3. Handles inactive tables by skipping them
4. Uses ETLFileHandler for data persistence
5. Provides comprehensive logging throughout the process

Classes:
    RepIntercompanyExtract: Main class handling RepIntercompany data extraction.
"""

import csv
from datetime import datetime
import logging
import os
from pathlib import Path
from typing import Union
from nemo_library_etl.adapter._utils.cloud_dirs import find_onedrive_dir
from nemo_library_etl.adapter.repintercompany.config_models_repintercompany import ConfigRepIntercompany
from nemo_library_etl.adapter._utils.enums import ETLAdapter, ETLStep
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library import NemoLibrary
import pandas as pd 

def german_to_float(german_num_str):
    """
    Converts a German-formatted number string to a float.

    German numbers use periods as thousand separators and commas as decimal separators.
    This function removes the periods and replaces the comma with a period to enable
    correct conversion to a float.

    Args:
        german_num_str (str): The German number in string format, e.g., '1.234,56'.

    Returns:
        float: The number converted to a float. Returns 0 if conversion fails.
    """
    try:
        return float(german_num_str.replace(".", "").replace(",", "."))
    except:
        return 0
    
class RepIntercompanyExtract:
    """
    Handles extraction of data from RepIntercompany system.
    
    This class manages the extraction phase of the RepIntercompany ETL pipeline,
    providing methods to connect to RepIntercompany systems, retrieve data,
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
        cfg (PipelineRepIntercompany): Pipeline configuration with extraction settings.
    """
    
    def __init__(
        self, 
        nl: NemoLibrary, 
        cfg: ConfigRepIntercompany, 
        logger: Union[logging.Logger, object], 
        fh: ETLFileHandler,
    ) -> None:
        """
        Initialize the RepIntercompany Extract instance.
        
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
        Execute the main extraction process for RepIntercompany data.
        
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
            the specific RepIntercompany system requirements.
        """
        self.logger.info("Extracting all RepIntercompany objects")

        onedrive_dir = find_onedrive_dir()
        if not onedrive_dir:
            raise FileNotFoundError("Could not locate OneDrive directory.")

        root = (
            Path(onedrive_dir)
            / "Reporting"
            / "_input"
            / "pA"
        )

        if not root.exists():
            raise FileNotFoundError(f"root folder not found at {root}")

        # check for files with pattern "NEMO BWA" in file name
        files_csv = [f for f in root.rglob("hIT_IC_*.csv") if f.is_file()]

        # find the latest file in this list now
        if not files_csv:
            raise FileNotFoundError(f"No files found in {root} matching pattern 'hIT_IC_*.csv'")    
        
        self.logger.info(f"Found {len(files_csv)} files matching pattern 'hIT_IC_*.csv' in {root}")     
        

        df = pd.DataFrame()
        endkunde_mapping = {}  # Dictionary to store Seriennummer -> Endkunde mapping
        numfiles = len(files_csv)

        for idx, f in enumerate(files_csv, start=1):

            file_path = Path(root) / f.name

            # Read invoicing date
            with open(file_path, newline="", encoding="ISO8859-1") as csvfile:
                reader = csv.reader(csvfile, delimiter=";")
                for i, row in enumerate(reader):
                    if i == 3:
                        invoice_date_str = row[1]
                        break
            invoice_date = self.intercompany_input_parse_invoice_date(invoice_date_str)

            # Determine positions of the upper and lower headers
            upper_header_position, nrows = self.find_header_positions(file_path)

            self.logger.info(
                f"Invoice date: {invoice_date.strftime('%Y-%m-%d')}, start: {upper_header_position:,}, nrows: {nrows:,} file {f} ({idx}/{numfiles}) "
            )

            # load data
            data = self.read_and_clean_csv_with_types(
                file_path=file_path,
                invoice_date=invoice_date,
                upper_header_position=upper_header_position,
                nrows=nrows,
            )

            # Add invoice date as a new column
            data["Rechnungsdatum"] = invoice_date

            # beginning with 2024-08 the format of the output file has changed
            if invoice_date < datetime(2024, 8, 1):
                if "Kunde" in data.columns:
                    data = data.rename(columns={"Kunde": "Abrechnungskunde"})
            else:
                new_mapping = data.set_index("Seriennummer")["Endkunde"].to_dict()
                endkunde_mapping.update(new_mapping)

            df = pd.concat([df, data])

        # After processing all files, fill 'Endkunde' for older data
        # Fill missing 'Endkunde' for rows where 'Rechnungsdatum' is before 1st August 2024
        mask_old_data = df["Rechnungsdatum"] < datetime(2024, 8, 1)
        df.loc[mask_old_data, "Endkunde"] = df.loc[mask_old_data, "Seriennummer"].map(
            endkunde_mapping
        )

        # Check for completeness of invoice data
        self.check_invoice_completeness(df)

        # Type conversions
        df["Datum Installation"] = pd.to_datetime(
            df["Datum Installation"], format="%d/%m/%y", errors="coerce"
                ).dt.date
        # replace NaT with a default date, e.g., 1900-01-01
        df["Datum Installation"] = df["Datum Installation"].fillna(pd.Timestamp("1900-01-01").date())
        
        df["Rechnungsdatum"] = pd.to_datetime(df["Rechnungsdatum"], errors="coerce").dt.date
        df["Rechnungsdatum"] = df["Rechnungsdatum"].fillna(pd.Timestamp("1900-01-01").date())

        df["Preis alt"] = df["Preis alt"].apply(german_to_float)
        df["Preis neu"] = df["Preis neu"].apply(german_to_float)
        df["Preis"] = df["Preis"].apply(german_to_float)
        df["Preis mit Rabatt"] = df["Preis mit Rabatt"].apply(german_to_float)
        int_cols = ["Mandant", "Endkunde"]
        df[int_cols] = df[int_cols].fillna(0).astype(int)
        
        self.fh.writeJSONL(
            step=ETLStep.EXTRACT,
            data=df.to_dict(orient="records"),
            entity="intercompany",
        )

    def find_header_positions(self,file_path):
        """
        First pass: Read the file to determine the positions of the upper header and where to stop.
        It looks for either a second header or the first empty row.
        """
        # Read the entire file without specifying data types
        data = pd.read_csv(
            file_path, sep=";", encoding="ISO8859-1", skiprows=6, on_bad_lines="skip"
        )

        # The first data line starts after the upper header (which we skip with skiprows)
        upper_header_position = 6

        # Find the first occurrence of "Abrechnungskunde" as a signal for the lower header (if any)
        potential_lower_headers = data[(data == "Typ").any(axis=1)].index

        # If a lower header is found, use its position; otherwise, search for the first empty row
        if len(potential_lower_headers) > 0:
            nrows = potential_lower_headers[0]
        else:
            # Find the first fully empty row (if any) to determine where the data ends
            empty_rows = data[data.isna().all(axis=1)].index
            if len(empty_rows) > 0:
                nrows = empty_rows[0]
            else:
                nrows = len(data)  # No empty row, use the end of the file

        return upper_header_position, nrows


    def read_and_clean_csv_with_types(
        self,
        file_path, invoice_date, upper_header_position, nrows
    ):
        """
        Second pass: Read the file with the correct data types, skiprows, and nrows
        after determining where the relevant data starts and ends.
        """

        # Define the dtype mapping based on the invoice date
        dtype_mapping = {
            "Mandant": str,
            "Betreuer": str,
            "User neu": int,
            "User alt": int,
        }

        # Adjust the dtype mapping based on the date (new format after 1st August 2024)
        if invoice_date < datetime(2024, 8, 1):
            dtype_mapping.update(
                {
                    "Kunde": int,
                }
            )  # Before 1st August 2024: "Kunde"
        else:
            dtype_mapping.update(
                {
                    "Abrechnungskunde": int,
                    "Endkunde": str,
                }
            )  # After 1st August 2024

        # Read the relevant part of the file with the appropriate data types
        data = pd.read_csv(
            file_path,
            sep=";",
            encoding="ISO8859-1",
            skiprows=upper_header_position,  # Skip rows before the actual data
            nrows=nrows,  # Only read up to the lower header
            dtype=dtype_mapping,  # Use the appropriate dtype mapping
        )

        return data


    def intercompany_input_parse_invoice_date(self,date_str):
        """
        Parses the invoice date from a string.

        Args:
            date_str (str): The date string to parse.

        Returns:
            datetime: The parsed date.

        Raises:
            ValueError: If the date format is not recognized.
        """
        formats = ["%d/%m/%y", "%d.%m.%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError("Date format not recognized")


    def check_invoice_completeness(self,df):
        """
        Checks whether there is one invoice for every month between the minimum and maximum invoice dates.

        Args:
            df (pd.DataFrame): The DataFrame containing invoice data with a 'Rechnungsdatum' column.

        Raises:
            ValueError: If there are missing months in the invoice data.
        """
        # Extract the minimum and maximum dates
        min_date = df["Rechnungsdatum"].min()
        max_date = df["Rechnungsdatum"].max()

        # Generate a set of all months between min_date and max_date
        all_months = pd.date_range(start=min_date, end=max_date, freq="MS").to_period("M")

        # Extract the unique months present in the data
        present_months = df["Rechnungsdatum"].dt.to_period("M").unique()

        # Find missing months
        missing_months = set(all_months) - set(present_months)

        if missing_months:
            raise ValueError(f"Missing invoice data for months: {sorted(missing_months)}")

