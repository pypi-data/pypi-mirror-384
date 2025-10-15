"""
Gedys ETL Adapter Main Entry Point.

This module serves as the main entry point for the Gedys ETL adapter, which handles
the extraction, transformation, and loading of data from Gedys systems into Nemo.
"""
from nemo_library_etl.adapter._utils.argparse import parse_startup_args
from nemo_library_etl.adapter.gedys.flow import gedys_flow

def main() -> None:
    """
    Main function to execute the Gedys ETL flow.

    This function initiates the complete Gedys ETL process by calling the Gedys_flow
    function, which orchestrates the extract, transform, and load operations.
    """
    args = parse_startup_args()
    gedys_flow(args)


if __name__ == "__main__":
    main()
