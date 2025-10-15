import logging
from pathlib import Path

from nemo_library import NemoLibrary

from nemo_library_etl.adapter.reppl.flow import reppl_flow
from nemo_library_etl.adapter.reppl.load import PROJECT_NAME_PLFROMCONTROLLING

ETL_Path = Path(__file__).parent / "etl" / "reppl"


def test_reporting_pl() -> None:

    # delete ETL folder if it exists
    if ETL_Path.exists():
        import shutil

        logging.info(f"Removing existing ETL folder: {ETL_Path}")
        shutil.rmtree(ETL_Path)

    try:
        args = {
            "config_ini": "./tests/config.ini",
            "config_json": "./tests/config/reppl.json",
        }
        reppl_flow(args)
    except Exception as e:
        assert False, f"Reporting P&L flow failed with exception: {e}"

    # check if the flow created the expected files
    # we expect 2 folders in etl/reppl: extract, transform

    etl_path = Path(__file__).parent / "etl" / "reppl"
    assert etl_path.exists(), f"ETL path {etl_path} does not exist"
    extract_path = etl_path / "extract"
    transform_path = etl_path / "transform"
    assert extract_path.exists(), f"Extract path {extract_path} does not exist"
    assert transform_path.exists(), f"Transform path {transform_path} does not exist"

    # check whether the project exsists
    nl = NemoLibrary(config_file="./tests/config.ini")
    project_id = nl.getProjectID(PROJECT_NAME_PLFROMCONTROLLING)
    assert (
        project_id is not None
    ), f"Project {PROJECT_NAME_PLFROMCONTROLLING} does not exist in Nemo"

    # get columns of the project
    columns = nl.getColumns(projectname=PROJECT_NAME_PLFROMCONTROLLING)
    column_internal_names = [col.internalName for col in columns]

    # assert there are columns starting with
    # "budget_ytd_"
    # "budget_"
    # "ist_ytd_"
    # "ist_"

    assert any(
        col.startswith("budget_ytd_") for col in column_internal_names
    ), "No columns starting with 'budget_ytd_'"
    assert any(
        col.startswith("budget_") for col in column_internal_names
    ), "No columns starting with 'budget_'"
    assert any(
        col.startswith("ist_ytd_") for col in column_internal_names
    ), "No columns starting with 'ist_ytd_'"
    assert any(
        col.startswith("ist_") for col in column_internal_names
    ), "No columns starting with 'ist_'"

    # clean up
    # delete ETL folder if it exists
    if ETL_Path.exists():
        import shutil

        logging.info(f"Removing existing ETL folder: {ETL_Path}")
        shutil.rmtree(ETL_Path)
