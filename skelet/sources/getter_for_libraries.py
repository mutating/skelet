from typing import List

from skelet.sources.abstract import AbstractSource
from skelet import EnvSource, TOMLSource, JSONSource, YAMLSource


def for_tool(tool_name: str) -> List[AbstractSource]:
    return EnvSource.for_library(tool_name) + TOMLSource.for_library(tool_name) + YAMLSource.for_library(tool_name) + JSONSource.for_library(tool_name)  # type: ignore[return-value, operator]
