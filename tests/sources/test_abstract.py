import pytest
from full_match import match

from skelet.sources.abstract import AbstractSource


def test_cant_instantiate_abstract_class():
    with pytest.raises(TypeError, match=match("Can't instantiate abstract class AbstractSource with abstract method __getitem__")):
        AbstractSource()
