"""
MigMan ETL Adapter Main Entry Point.

This module serves as the main entry point for the MigMan ETL adapter, which handles
the extraction, transformation, and loading of data from MigMan systems into Nemo.
"""
from nemo_library_etl.adapter._utils.argparse import parse_startup_args
from nemo_library_etl.adapter.migman.flow import migman_flow

def main() -> None:
    """
    Main function to execute the MigMan ETL flow.

    This function initiates the complete MigMan ETL process by calling the MigMan_flow
    function, which orchestrates the extract, transform, and load operations.
    """
    args = parse_startup_args()
    migman_flow(args)


if __name__ == "__main__":
    main()
