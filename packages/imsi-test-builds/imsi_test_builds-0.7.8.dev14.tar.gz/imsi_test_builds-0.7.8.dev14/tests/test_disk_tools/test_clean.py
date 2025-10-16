
import pytest
import json
import os
from click.testing import CliRunner
from imsi.tools.disk_tools import disk_tools
from imsi.cli.entry import cli
from pathlib import Path
import subprocess
import shutil
import pickle
from omegaconf import OmegaConf

@pytest.fixture
def runner():
    return CliRunner()


# sets up working directory for tests with data, temp_data, and a minimal setup directory 
def setup_clean_test(fail_type=None):
    cwd = Path.cwd()    

    # create empty data and temp data directories
    data_dir = cwd.joinpath("data")
    data_dir.mkdir()
    temp_dir = cwd.joinpath("temp_data")
    temp_dir.mkdir()
    data_runid = data_dir.joinpath("imsi-test")
    data_runid.mkdir(parents=True)

    temp_runid = temp_dir.joinpath("maestro", "imsi-test")
    if fail_type != "zero":  # Makes it so there should be 0 runids in temp location
        temp_runid.mkdir(parents=True)

    if fail_type == "multi":  # makes there be two run_ids in the same location
        temp_runid2 = temp_dir.joinpath("imsi-test")
        temp_runid2.mkdir(parents=True)

    # create setup directory with config file and src to make clean work
    config_dir = cwd.joinpath("imsi-test")
    config_dir.mkdir()

    # mock .imsi state dir
    imsi_config_state = config_dir / ".imsi"
    imsi_config_state.mkdir()

    src = config_dir.joinpath("src")
    src.mkdir()

    config_file = config_dir.joinpath("imsi_configuration_imsi-test.yaml")
    script_location = Path(__file__).parent.resolve()
    source_config = f"{script_location}/imsi_configuration_imsi-test.yaml"

    config_data = OmegaConf.load(source_config)

    config_data["machine"]["storage_dir"] = str(data_dir)
    config_data["machine"]["scratch_dir"] = str(temp_dir)

    OmegaConf.save(config_data, config_file)

    # also pickle the file into .imsi
    with open(imsi_config_state / '.imsi_configuration_imsi-test.pickle', 'wb') as file:
        pickle.dump(config_data, file)

    return config_dir, data_runid, temp_runid


@pytest.mark.parametrize(
    ("args", "directories"), 
    [
    ([],  [True, False, False]),
    (["-s", "-t", "-d"], [False, False, False]),
    (["-s"], [False, True, True]),
    ]
)
def test_clean_run(runner, args, directories):
    with runner.isolated_filesystem():
        setup_dir, data_dir, temp_dir = setup_clean_test()
        result = runner.invoke(cli, ["clean", "--runid_path=imsi-test"] + args)
        assert result.exit_code == 0, result.output
        assert setup_dir.exists() == directories[0], "setup directory incorrect state"
        assert data_dir.exists() == directories[1], "data directory incorrect state"
        assert temp_dir.exists() == directories[2], "temp data directory incorrect state"


@pytest.mark.parametrize(
    ("fail_type", "exit_code", "message"),
    [ 
    ("multi", True, "Found more"),
    ("zero", False, "No runid")
    ]
)
def test_multi_runids(runner, fail_type, exit_code, message):
    with runner.isolated_filesystem():
        setup_dir, data_dir, temp_dir = setup_clean_test(fail_type)
        result = runner.invoke(cli, ["clean", "--runid_path=imsi-test", "-t"])
        assert result.exit_code == exit_code, result.output
        if exit_code == 1:
            assert message in str(result.exception)
        else:
            assert message in str(result.output)


def test_wrk_dir_set(runner):
    try:
        os.environ["WRK_DIR"] = "abc/123/doremi/"
        with runner.isolated_filesystem():
            setup_dir, data_dir, temp_dir = setup_clean_test()
            result = runner.invoke(cli, ["clean", "--runid_path=imsi-test"])
            assert result.exit_code == 1, result.output
            assert "Your 'WRK_DIR' is currently set" in str(result.exception)
    finally:
        os.environ["WRK_DIR"] = ""
