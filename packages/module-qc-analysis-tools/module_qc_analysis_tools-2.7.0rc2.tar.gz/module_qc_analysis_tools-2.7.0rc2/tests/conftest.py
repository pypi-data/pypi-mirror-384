import pathlib

# shutil is nicer, but doesn't work: https://bugs.python.org/issue20849
from functools import partial
from shutil import copytree as _copytree

import pytest

copytree = partial(_copytree, dirs_exist_ok=True)


@pytest.fixture
def datadir(tmp_path, request):
    """
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    """
    # this gets the module name (e.g. /path/to/module-qc-analysis-tools/tests/test_cli.py)
    # and then gets the directory by removing the suffix (e.g. /path/to/module-qc-analysis-tools/tests/test_cli)
    test_dir = pathlib.Path(request.module.__file__).with_suffix("")

    if test_dir.is_dir():
        copytree(test_dir, str(tmp_path))

    return tmp_path


@pytest.fixture
def testdata(request):
    """
    Fixture responsible for providing a folder of common test data but does not make a copy.
    """
    return pathlib.Path(request.module.__file__).parent.joinpath("data")
