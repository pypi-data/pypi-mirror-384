import logging
from pathlib import Path

from nemo_library import NemoLibrary

from nemo_library_etl.adapter.repprices.flow import repprices_flow
from nemo_library_etl.adapter.repprices.load import PROJECT_NAME_LIST_PRICES

ETL_Path = Path(__file__).parent / "etl" / "repprices"


def test_reporting_pricing() -> None:

    # delete ETL folder if it exists
    if ETL_Path.exists():
        import shutil

        logging.info(f"Removing existing ETL folder: {ETL_Path}")
        shutil.rmtree(ETL_Path)

    try:
        args = {
            "config_ini": "./tests/config.ini",
            "config_json": "./tests/config/repprices.json",
        }
        repprices_flow(args)
    except Exception as e:
        assert False, f"Reporting Pricing flow failed with exception: {e}"

    # check if the flow created the expected files
    # we expect 2 folders in etl/repprices: extract, transform

    etl_path = Path(__file__).parent / "etl" / "repprices"
    assert etl_path.exists(), f"ETL path {etl_path} does not exist"
    extract_path = etl_path / "extract"
    transform_path = etl_path / "transform"
    assert extract_path.exists(), f"Extract path {extract_path} does not exist"
    assert transform_path.exists(), f"Transform path {transform_path} does not exist"

    # check whether the project exsists
    nl = NemoLibrary(config_file="./tests/config.ini")
    project_id = nl.getProjectID(PROJECT_NAME_LIST_PRICES)
    assert (
        project_id is not None
    ), f"Project {PROJECT_NAME_LIST_PRICES} does not exist in Nemo"

    # get columns of the project
    columns = nl.getColumns(projectname=PROJECT_NAME_LIST_PRICES)
    column_internal_names = [col.internalName for col in columns]

    # check special columns
    for col in ["x_user", "nem_nemo_adv", "nem_nemo_ess"]:
        assert (
            col in column_internal_names
        ), f"Column '{col}' does not exist in project {PROJECT_NAME_LIST_PRICES}"

    # clean up
    # delete ETL folder if it exists
    if ETL_Path.exists():
        import shutil

        logging.info(f"Removing existing ETL folder: {ETL_Path}")
        shutil.rmtree(ETL_Path)
