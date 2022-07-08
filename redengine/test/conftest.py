
import datetime
import logging
import os
import sys
import time
from pathlib import Path

import pytest
from dateutil.parser import parse as parse_datetime

from redbird.logging import RepoHandler
from redbird.repos import MemoryRepo

import redengine
from redengine import Session
from redengine.core.hook import clear_hooks
from redengine.log.log_record import MinimalRecord

# add helpers to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'helpers'))

# Utils
def get_node_id(request):
    components = request.node.nodeid.split("::")
    filename = components[0]
    test_class = components[1] if len(components) == 3 else None
    test_func_with_params = components[-1]
    test_func = test_func_with_params.split('[')[0]

    filename = filename.replace(".py", "").replace("/", "-")
    if test_class:
        return f'{filename}-{test_class}-{test_func_with_params}'
    else:
        return f'{filename}-{test_func_with_params}'

def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    redengine.session.config.debug = True


def copy_file_to_tmpdir(tmpdir, source_file, target_path):
    target_path = Path(target_path)
    source_path = Path(os.path.dirname(__file__)) / "test_files" / source_file

    fh = tmpdir.join(target_path.name)
    with open(source_path) as f:
        fh.write(f.read())
    return fh

@pytest.fixture(autouse=True)
def sys_paths():
    orig_sys_paths = sys.path.copy()
    yield
    # Setting back the original sys paths so they are not 
    # carried over different tasks.
    sys.path = orig_sys_paths

@pytest.fixture
def script_files(tmpdir):
    for folder in Path("scripts").parts:
        tmpdir = tmpdir.mkdir(folder)
    
    copy_file_to_tmpdir(tmpdir, source_file="succeeding_script.py", target_path="scripts/succeeding_script.py")
    copy_file_to_tmpdir(tmpdir, source_file="failing_script.py", target_path="scripts/failing_script.py")
    copy_file_to_tmpdir(tmpdir, source_file="parameterized_script.py", target_path="scripts/parameterized_script.py")
    copy_file_to_tmpdir(tmpdir, source_file="parameterized_kwargs_script.py", target_path="scripts/parameterized_kwargs_script.py")
    copy_file_to_tmpdir(tmpdir, source_file="syntax_error_script.py", target_path="scripts/syntax_error_script.py")


@pytest.fixture(scope="function", autouse=True)
def session():
    session = Session(config={
        "debug": True,
        "silence_task_prerun": False,
        "silence_cond_check": False,
    }, delete_existing_loggers=True)
    redengine.session = session
    session.set_as_default()

    task_logger = logging.getLogger(session.config.task_logger_basename)
    task_logger.handlers = [
        RepoHandler(repo=MemoryRepo(model=MinimalRecord)),
        logging.StreamHandler(sys.stdout)
    ]

    # enable logger
    # Some tests may disable especially scheduler logger if logging config has
    # "disable_existing_loggers" as True and missing scheduler logger
    logging.getLogger(session.config.task_logger_basename).disabled = False
    logging.getLogger(session.config.scheduler_logger_basename).disabled = False

    # Clear hooks
    clear_hooks()
    return session

@pytest.fixture(scope="session", autouse=True)
def set_loggers():
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(action)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    task_logger = logging.getLogger(redengine.session.config.task_logger_basename)
    task_logger.addHandler(handler)

    yield session

class mockdatetime(datetime.datetime):
    _freezed_datetime = None
    @classmethod
    def now(cls):
        return cls._freezed_datetime

@pytest.fixture
def mock_datetime_now(monkeypatch):
    """Monkey patch datetime.datetime.now
    Returns a function that takes datetime as string as input
    and sets that to datetime.datetime.now()"""
    import datetime
    class mockdatetime(datetime.datetime):
        _freezed_datetime = None
        @classmethod
        def now(cls):
            return cls._freezed_datetime

    def wrapper(dt):
        dt = parse_datetime(dt)

        # Mock datetime.datetime
        mockdatetime._freezed_datetime = mockdatetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond)
        monkeypatch.setattr(datetime, 'datetime', mockdatetime)

        # Mock time.time
        mocktime = dt.timestamp()
        monkeypatch.setattr(time, 'time', lambda: mocktime)

    yield wrapper

@pytest.fixture
def mock_time(monkeypatch):
    """Monkey patch time.time
    Returns a function that takes datetime as string as input
    and sets that to time.time()"""

    def wrapper(dt):
        mocktime = parse_datetime(dt).timestamp()
        monkeypatch.setattr(time, 'time', lambda: mocktime)

    return wrapper

@pytest.fixture
def mock_pydatetime(mock_time, mock_datetime_now):
    """Monkey patch time.time & datetime.datetime.now
    Returns a function that takes datetime as string as input
    and sets that to time.time() and datetime.datetime.now()"""
    
    def wrapper(dt):
        mock_time(dt)
        mock_datetime_now(dt)
    return wrapper

# Mongo Database
@pytest.fixture(scope="function")
def mongo_conn_str():
    conf_path = Path("redengine/test/private.yaml")
    pytest.importorskip("pymongo")
    if not conf_path.is_file():
        pytest.skip("Missing Mongo connection")
    import yaml

    with open(conf_path, 'r') as f:
        conf = yaml.safe_load(f)
    return conf["mongodb"]["conn_str"]

@pytest.fixture(scope="function")
def mongo_client(mongo_conn_str):
    import pymongo
    return pymongo.MongoClient(mongo_conn_str)

@pytest.fixture(scope="function")
def collection(request, mongo_client):
    
    db_name = "pytest"
    col_name = get_node_id(request)

    collection = mongo_client[db_name][col_name]

    # Empty the collection
    collection.delete_many({})

    yield collection
