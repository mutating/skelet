import sys
from typing import List, Optional
from os.path import join
from tempfile import TemporaryDirectory
from pathlib import Path
from json import dumps as json_dumps

from tomli_w import dumps as toml_dumps
from yaml import dump as yaml_dumps
import pytest


@pytest.fixture
def temporary_dir_path():
    with TemporaryDirectory() as path:
        yield path


@pytest.fixture(params=[str, Path])
def toml_config_path(request, data, temporary_dir_path):
    serialized_data = toml_dumps(data)

    file_path = join(temporary_dir_path, 'file.toml')
    with open(file_path, 'w') as file:
        file.write(serialized_data)

    yield request.param(file_path)


@pytest.fixture(params=[str, Path])
def json_config_path(request, data, temporary_dir_path):
    serialized_data = json_dumps(data)

    file_path = join(temporary_dir_path, 'file.json')
    with open(file_path, 'w') as file:
        file.write(serialized_data)

    yield request.param(file_path)


@pytest.fixture(params=[str, Path])
def yaml_config_path(request, data, temporary_dir_path):
    serialized_data = yaml_dumps(data)

    file_path = join(temporary_dir_path, 'file.yaml')
    with open(file_path, 'w') as file:
        file.write(serialized_data)

    yield request.param(file_path)


@pytest.fixture
def temp_argv(monkeypatch, argv):
    if argv is None:
        argv = []

    result = sys.argv[:1] + argv
    monkeypatch.setattr(sys, "argv", result)
    return result
