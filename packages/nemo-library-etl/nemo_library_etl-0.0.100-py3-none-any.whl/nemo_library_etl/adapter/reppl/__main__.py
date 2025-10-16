"""
RepPL ETL Adapter Main Entry Point.

This module serves as the main entry point for the RepPL ETL adapter, which handles
the extraction, transformation, and loading of data from RepPL systems into Nemo.
"""
from nemo_library_etl.adapter._utils.argparse import parse_startup_args
from nemo_library_etl.adapter.reppl.flow import reppl_flow

def main() -> None:
    """
    Main function to execute the RepPL ETL flow.

    This function initiates the complete RepPL ETL process by calling the RepPL_flow
    function, which orchestrates the extract, transform, and load operations.
    """
    args = parse_startup_args()
    reppl_flow(args)


if __name__ == "__main__":
    main()
