"""
RepIntercompany ETL Adapter Main Entry Point.

This module serves as the main entry point for the RepIntercompany ETL adapter, which handles
the extraction, transformation, and loading of data from RepIntercompany systems into Nemo.
"""
from nemo_library_etl.adapter._utils.argparse import parse_startup_args
from nemo_library_etl.adapter.repintercompany.flow import repintercompany_flow

def main() -> None:
    """
    Main function to execute the RepIntercompany ETL flow.

    This function initiates the complete RepIntercompany ETL process by calling the RepIntercompany_flow
    function, which orchestrates the extract, transform, and load operations.
    """
    args = parse_startup_args()
    repintercompany_flow(args)


if __name__ == "__main__":
    main()
