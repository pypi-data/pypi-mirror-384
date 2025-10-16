from tempfile import TemporaryDirectory

import pytest


@pytest.fixture(scope="session", autouse=True)
def changetmp(request):
    with TemporaryDirectory(prefix="pytest-<project-name>-") as temp_dir:
        request.config.option.basetemp = temp_dir
        yield
