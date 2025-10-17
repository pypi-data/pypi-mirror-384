from typing import TypeVar

AttrValue = str | int | float | bool

T = TypeVar("T", bound=AttrValue)

ExternalAttributesType = dict[str, dict[str, str | dict[str, str]]]
NodeAttributesType = dict[str, str | dict[str, str]]
