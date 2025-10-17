from typing import Protocol


class HtmlAttrProtocol(Protocol):
    def get_attr(self, attribute_name: str) -> str:
        """
        Returns value of the attribute.
        """
        ...

    def remove_attr(self, attribute_name: str) -> None:
        """
        Removes the attribute.
        """
        ...

    def remove_attrs(self) -> None:
        """
        Removes all attributes.
        """
        ...

    def update_attr(
        self, attribute_name: str, new_value: str, create_new: bool = True
    ) -> None:
        """
        Updates the attribute value.
        """
        ...
