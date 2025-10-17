"""htmlConv - A Python library for converting and manipulating HTML structures.

This library provides a Node-based approach to working with HTML elements,
allowing for easy creation, manipulation, and conversion of HTML structures.
"""

from nodie.primitives.attributes import Attributes  # noqa: I001
from nodie.primitives.inline_style_attributes import InlineStyleAttributes
from nodie.primitives.node import HTMLNode
from nodie.converters.html_converter import to_html

__version__ = "0.0.2"
__author__ = "Yauheni Buhayeu"
__email__ = "bugaev.zhenka@yandex.by"

__all__ = ["HTMLNode", "Attributes", "InlineStyleAttributes", "to_html"]
