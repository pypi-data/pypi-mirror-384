import logging
from pathlib import Path

from nemo_library import NemoLibrary

from nemo_library_etl.adapter.repintercompany.flow import repintercompany_flow
from nemo_library_etl.adapter.repintercompany.load import PROJECT_NAME_INTERCOMPANY

ETL_Path = Path(__file__).parent / "etl" / "repintercompany"


def test_reporting_pl() -> None:

    # delete ETL folder if it exists
    if ETL_Path.exists():
        import shutil

        logging.info(f"Removing existing ETL folder: {ETL_Path}")
        shutil.rmtree(ETL_Path)

    try:
        args = {
            "config_ini": "./tests/config.ini",
            "config_json": "./tests/config/repintercompany.json",
        }
        repintercompany_flow(args)
    except Exception as e:
        assert False, f"Reporting Intercompany flow failed with exception: {e}"

    # check if the flow created the expected files
    # we expect 2 folders in etl/repintercompany: extract, transform

    etl_path = Path(__file__).parent / "etl" / "repintercompany"
    assert etl_path.exists(), f"ETL path {etl_path} does not exist"
    extract_path = etl_path / "extract"
    assert extract_path.exists(), f"Extract path {extract_path} does not exist"

    # check whether the project exsists
    nl = NemoLibrary(config_file="./tests/config.ini")
    project_id = nl.getProjectID(PROJECT_NAME_INTERCOMPANY)
    assert (
        project_id is not None
    ), f"Project {PROJECT_NAME_INTERCOMPANY} does not exist in Nemo"

    # get columns of the project
    columns = nl.getColumns(projectname=PROJECT_NAME_INTERCOMPANY)
    column_internal_names = [col.internalName for col in columns]

    # clean up
    # delete ETL folder if it exists
    if ETL_Path.exists():
        import shutil

        logging.info(f"Removing existing ETL folder: {ETL_Path}")
        shutil.rmtree(ETL_Path)
