from os.path import join
from tempfile import TemporaryDirectory
from pathlib import Path

from tomli_w import dumps
import pytest


@pytest.fixture
def temporary_dir_path():
    with TemporaryDirectory() as path:
        yield path

@pytest.fixture(params=[str, Path])
def config_path(request, data, temporary_dir_path):
    serialized_data = dumps(data)

    file_path = join(temporary_dir_path, 'file.toml')
    with open(file_path, 'w') as file:
        file.write(serialized_data)

    yield request.param(file_path)
