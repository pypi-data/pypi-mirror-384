from pathlib import Path
from contextlib import contextmanager
import os
from asap3.test.pytest_markers import _openkimmodel

import pytest

try:
    from asap3.mpi import world
except ImportError:
    from ase.parallel import world
from ase.parallel import broadcast


# Add markers here instead of in pytest.ini as that file is not always found by pytest
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "core: very important test of core functionality"
    )
    config.addinivalue_line(
        "markers", "slow: test is particularly slow"
    )


### Skip tests marked as slow unless --runslow is given on command line
### See https://docs.pytest.org/en/latest/example/simple.html#control-skipping-of-tests-according-to-command-line-option
def pytest_addoption(parser):
    parser.addoption(
        "--slow", action="store_true", default=False, help="run slow tests"
    )

def pytest_collection_modifyitems(config, items):
    if config.getoption("--slow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --slow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


# Fixtures

@pytest.fixture(scope='session')
def datadir():
    test_basedir = Path(__file__).parent
    return test_basedir / 'testdata'

@pytest.fixture(scope='session')
def cpulayout():
    if world.size == 1:
        return None
    elif world.size == 2:
        return [2,1,1]
    elif world.size == 3:
        return [1,3,1]
    elif world.size == 4:
        return [2,1,2]
    elif world.size == 6:
        return [1,2,3]
    elif world.size == 8:
        return [2,2,2]
    else:
        raise ValueError('Test suit should run on 1, 2, 3, 4, 6 or 8 cores.')

@pytest.fixture(scope='session')
def multicpulayout():
    if world.size == 1:
        return [None]
    elif world.size == 2:
        return [(2,1,1), (1,2,1), (1,1,2)]
    elif world.size == 3:
        return [(3,1,1), (1,1,3)]
    elif world.size == 4:
        return [(1,2,2), (2,1,2), (2,2,1)]
    elif world.size == 8:
        return [(2,2,2), (1,2,4)]
    else:
        raise ValueError("Cannot run on %d CPUs." % (worldsize,))

@pytest.fixture(scope='session')
def openkimmodel():
    'Default OpenKIM model for tests'
    return _openkimmodel

# Run some modules in a temporary folder - copied from GPAW

@contextmanager
def execute_in_tmp_path(request, tmp_path_factory):
    if world.rank == 0:
        # Obtain basename as
        # * request.function.__name__  for function fixture
        # * request.module.__name__    for module fixture
        basename = getattr(request, request.scope).__name__
        path = tmp_path_factory.mktemp(basename)
    else:
        path = None
    path = broadcast(path)
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(cwd)

@pytest.fixture(scope='function')
def in_tmp_dir(request, tmp_path_factory):
    """Run test function in a temporary directory."""
    with execute_in_tmp_path(request, tmp_path_factory) as path:
        yield path


@pytest.fixture(scope='module')
def module_tmp_path(request, tmp_path_factory):
    """Run test module in a temporary directory."""
    with execute_in_tmp_path(request, tmp_path_factory) as path:
        yield path
