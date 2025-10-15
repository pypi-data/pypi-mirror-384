def parse_startup_args() -> dict[str, str]:
    """Parse command line arguments for the ETL process.

    Returns:
        dict[str, str]: Parsed command line arguments.
    """
    import argparse

    parser = argparse.ArgumentParser(description="ETL Process Arguments")

    parser.add_argument(
        "--config_ini",
        type=str,
        required=False,
        default="./config.ini",
        help="Path to the configuration file.",
    )

    parser.add_argument(
        "--config_json",
        type=str,
        required=False,
        default=None,
        help="Path to the JSON configuration file.",
    )

    parser.add_argument(
        "--environment",
        type=str,
        required=False,
        default=None,
        help="Environment setting for the ETL process.",
    )

    parser.add_argument(
        "--tenant",
        type=str,
        required=False,
        default=None,
        help="Tenant identifier for the ETL process.",
    )

    parser.add_argument(
        "--userid",
        type=str,
        required=False,
        default=None,
        help="User ID for authentication.",
    )

    parser.add_argument(
        "--password",
        type=str,
        required=False,
        default=None,
        help="Password for authentication.",
    )
    args = parser.parse_args()
    return vars(args)
