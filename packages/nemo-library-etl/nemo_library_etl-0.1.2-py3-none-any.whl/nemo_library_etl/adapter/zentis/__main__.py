"""
Zentis ETL Adapter Main Entry Point.

This module serves as the main entry point for the Zentis ETL adapter, which handles
the extraction, transformation, and loading of data from Zentis systems into Nemo.
"""
from nemo_library_etl.adapter._utils.argparse import parse_startup_args
from nemo_library_etl.adapter.zentis.flow import zentis_flow

def main() -> None:
    """
    Main function to execute the Zentis ETL flow.

    This function initiates the complete Zentis ETL process by calling the Zentis_flow
    function, which orchestrates the extract, transform, and load operations.
    """
    args = parse_startup_args()
    zentis_flow(args)


if __name__ == "__main__":
    main()
