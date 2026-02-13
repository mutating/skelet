from typing import List

from skelet import EnvSource, JSONSource, TOMLSource, YAMLSource
from skelet.sources.abstract import AbstractSource


def for_tool(tool_name: str) -> List[AbstractSource]:
    return EnvSource.for_library(tool_name) + TOMLSource.for_library(tool_name) + YAMLSource.for_library(tool_name) + JSONSource.for_library(tool_name)  # type: ignore[return-value, operator]
