import os
from unittest import mock

import pytest

import docker_entrypoint

TEMP_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "temp_env_var.txt")


@pytest.fixture
def set_file_value(request):
    with open(TEMP_FILE, "w") as fp:
        fp.write(request.param)

    yield

    os.remove(TEMP_FILE)


@mock.patch.dict(os.environ, {"WT_USER": "Nathan"})
def test_get_environment_variable_simple():
    """
    Test simple functionality
    """
    assert docker_entrypoint.get_environment_variable("WT_USER") == "Nathan"


@mock.patch.dict(os.environ, {})
def test_get_environment_variable_default():
    """
    Test defaults with no alternates.
    """
    assert (
        docker_entrypoint.get_environment_variable("WT_USER", default="Nathan")
        == "Nathan"
    )
    assert docker_entrypoint.get_environment_variable("WT_USER") is None


@mock.patch.dict(os.environ, {"WT_USER2": "Jeff"})
def test_get_environment_variable_alternates():
    """
    Test alternates.
    """
    assert (
        docker_entrypoint.get_environment_variable("WT_USER", alternates=["WT_USER2"])
        == "Jeff"
    )


@mock.patch.dict(os.environ, {"WT_USER": "Nathan", "WT_USER2": "Jeff"})
def test_get_environment_variable_alternates_primary():
    """
    Test that primary is preferred over alternates.
    """
    assert (
        docker_entrypoint.get_environment_variable("WT_USER", alternates=["WT_USER2"])
        == "Nathan"
    )


@mock.patch.dict(os.environ, {})
def test_get_environment_variable_alternates_default():
    """
    Test that defaults work with alternates.
    """
    assert (
        docker_entrypoint.get_environment_variable(
            "WT_USER", alternates=["WT_USER2"], default="Nathan"
        )
        == "Nathan"
    )


@mock.patch.dict(os.environ, {"WT_USER_FILE": TEMP_FILE})
@pytest.mark.parametrize("set_file_value", ["Nathan"], indirect=True)
def test_get_environment_variable_file(set_file_value):
    """
    Test file functionality
    """
    assert docker_entrypoint.get_environment_variable("WT_USER") == "Nathan"


@mock.patch.dict(os.environ, {"WT_USER_FILE": "/var/not/real"})
def test_get_environment_variable_file_does_not_exist():
    """
    Test file functionality with non existent file
    """
    assert docker_entrypoint.get_environment_variable("WT_USER") is None


@mock.patch.dict(os.environ, {"WT_USER2_FILE": TEMP_FILE})
@pytest.mark.parametrize("set_file_value", ["Nathan"], indirect=True)
def test_get_environment_variable_file_alternates(set_file_value):
    """
    Test file functionality with alternates
    """
    assert (
        docker_entrypoint.get_environment_variable("WT_USER", alternates=["WT_USER2"])
        == "Nathan"
    )


@mock.patch.dict(os.environ, {"POSTGRES_DB": "pg_wt"})
def test_get_environment_variable_real():
    """
    Test a real scenario
    """
    assert (
        docker_entrypoint.get_environment_variable(
            "DB_NAME",
            default="webtrees",
            alternates=["MYSQL_DATABASE", "MARIADB_DATABASE", "POSTGRES_DB"],
        )
        == "pg_wt"
    )
