import pytest

from skelet.sources.abstract import AbstractSource


def test_cant_instantiate_abstract_class():
    with pytest.raises(TypeError):
        AbstractSource()
