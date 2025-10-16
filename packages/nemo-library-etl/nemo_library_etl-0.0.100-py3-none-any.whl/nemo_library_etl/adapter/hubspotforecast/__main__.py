"""
HubSpotForecast ETL Adapter Main Entry Point.

This module serves as the main entry point for the HubSpotForecast ETL adapter, which handles
the extraction, transformation, and loading of data from HubSpotForecast systems into Nemo.
"""
from nemo_library_etl.adapter._utils.argparse import parse_startup_args
from nemo_library_etl.adapter.hubspotforecast.flow import hubspotforecast_flow

def main() -> None:
    """
    Main function to execute the HubSpotForecast ETL flow.

    This function initiates the complete HubSpotForecast ETL process by calling the HubSpotForecast_flow
    function, which orchestrates the extract, transform, and load operations.
    """
    args = parse_startup_args()
    hubspotforecast_flow(args)


if __name__ == "__main__":
    main()
