from nodie import HTMLNode
from nodie.primitives.attributes import Attributes
from nodie.primitives.inline_style_attributes import InlineStyleAttributes
from nodie.primitives.node import Children


def test_create_html_node_instance_with_all_parameters() -> None:
    # Arrange
    tag_name = "div"
    attrs_dict = {"class": "test-class", "id": "test-id"}
    attributes = Attributes(attrs_dict, tag_name)
    inline_styles = InlineStyleAttributes({"color": "red"})
    children = Children([])
    is_self_closed_tag = False
    attrs_map_identifier = "custom"

    # Act
    node = HTMLNode(
        tag_name=tag_name,
        attributes=attributes,
        is_self_closed_tag=is_self_closed_tag,
        inline_styles=inline_styles,
        children=children,
        attrs_map_identifier=attrs_map_identifier,
    )

    # Assert
    assert node.tag_name == tag_name
    assert node.attributes == attributes
    assert node.inline_styles == inline_styles
    assert node.children == children
    assert node.is_self_closed_tag == is_self_closed_tag
    assert node.attrs_map_identifier == attrs_map_identifier
    assert isinstance(node.node_id, str)
    assert len(node.node_id) > 0
