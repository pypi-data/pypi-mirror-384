from typing import Any

from nodie.constants.html_tag_mappers import HTML_TAGS
from nodie.constants.types import ExternalAttributesType, NodeAttributesType
from nodie.primitives.attributes import Attributes
from nodie.primitives.inline_style_attributes import InlineStyleAttributes


class Children:
    def __init__(self, children: list["HTMLNode | str"]) -> None:
        self.children: list[HTMLNode | str] = children

    def add_child(self, child_node: "HTMLNode | str") -> None:
        if not isinstance(child_node, HTMLNode | str):
            raise TypeError(
                f"Child must be Node or str, got {type(child_node).__name__}"
            )
        self.children.append(child_node)

    def add_children(self, new_children: "tuple[HTMLNode | str,...]") -> None:
        self.children.extend(new_children)

    def remove_child(self, child_node_id: str) -> None:
        self.children = [
            child
            for child in self.children
            if not (isinstance(child, HTMLNode) and child.node_id == child_node_id)
        ]

    def remove_children(self) -> None:
        self.children = []


class HTMLNode:
    def __init__(
        self,
        tag_name: str,
        attributes: Attributes,
        is_self_closed_tag: bool,
        inline_styles: InlineStyleAttributes,
        children: Children,
        attrs_map_identifier: str = "default",
    ):
        self._node_id = attributes.get_unique_id()
        self.tag_name = tag_name
        self.attributes = attributes
        self.inline_styles = inline_styles
        self.children = children
        self.is_self_closed_tag = is_self_closed_tag
        self.attrs_map_identifier = attrs_map_identifier

    @property
    def node_id(self) -> str:
        return self._node_id

    def update_node_id(self) -> None:
        self._node_id = self.attributes.get_unique_id()

    @classmethod
    def from_dict(
        cls,
        interpretable_data: NodeAttributesType,
        attrs_mapper: ExternalAttributesType | None = None,
    ) -> "HTMLNode":
        tag_name = interpretable_data.get("tag_name")

        if not isinstance(tag_name, str):
            raise TypeError("Tag name must be a string, got {type(tag_name).__name__}")

        # Check if the dictionary contains required keys
        if tag_name is None or (tag_values := HTML_TAGS.get(tag_name, None)) is None:
            raise ValueError("Dictionary must contain valid 'tag_name' key")

        is_self_closed_tag = tag_values[1]

        raw_attrs, attrs_identifier = cls.__generate_raw_attributes_from_dict(
            interpretable_data, attrs_mapper
        )

        inline_styles = cls.__create_inline_style_attributes_instance(raw_attrs)
        clean_attrs = cls.__clean_attributes(raw_attrs)

        attributes = Attributes(clean_attrs, tag_name)
        children = interpretable_data.get("children", ())

        if not isinstance(children, tuple | list):
            raise TypeError(
                f"Children must be an iterable, got {type(children).__name__}"
            )

        node = cls(
            tag_name,
            attributes,
            is_self_closed_tag,
            inline_styles=inline_styles,
            attrs_map_identifier=attrs_identifier,
            children=cls.generate_children(children),
        )

        return node

    def get_children(self) -> list["HTMLNode | str"]:
        return self.children.children

    @classmethod
    def generate_children(cls, children: tuple[dict[str, Any] | str, ...]) -> Children:
        children_nodes: list[HTMLNode | str] = []
        for child_data in children:
            if isinstance(child_data, dict):
                children_nodes.append(cls.from_dict(child_data))
            else:
                children_nodes.append(child_data)
        return Children(children_nodes)

    @staticmethod
    def __create_inline_style_attributes_instance(
        raw_attrs: NodeAttributesType,
    ) -> InlineStyleAttributes:
        if "style" not in raw_attrs:
            return InlineStyleAttributes({})

        style_attrs = raw_attrs["style"]

        if not isinstance(style_attrs, dict):
            raise ValueError("Style attribute must be a dictionary")

        return InlineStyleAttributes(style_attrs)

    @classmethod
    def __generate_raw_attributes_from_dict(
        cls,
        interpretable_data: dict[str, Any],
        attrs_mapper: dict[str, NodeAttributesType] | None = None,
    ) -> tuple[NodeAttributesType, str]:
        if not attrs_mapper:
            return interpretable_data.get("attributes", {}), "default"

        attrs_identifier = interpretable_data.get("attrs_map_identifier")
        if attrs_identifier is None:
            print("attrs_map_identifier not found, set 'default'")
            attrs_identifier = "default"

        mapped_attrs: NodeAttributesType = attrs_mapper.get(attrs_identifier, {})
        return mapped_attrs, attrs_identifier

    @classmethod
    def __clean_attributes(
        cls, raw_attrs: dict[str, str | dict[str, str]]
    ) -> dict[str, str]:
        clean_attrs: dict[str, str] = {
            key: value
            for key, value in raw_attrs.items()
            if key != "style" and isinstance(value, str)
        }
        return clean_attrs
