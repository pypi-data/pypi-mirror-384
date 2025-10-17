from nodie.constants import html_tag_mappers


class Attributes:
    def __init__(self, attributes: dict[str, str], tag_name: str) -> None:
        self.attributes = self.introspect_attributes(tag_name, attributes)

    def attributes_to_html_string(self) -> str:
        """Combine all node attributes into a single HTML attribute string.

        Converts the node's attributes dictionary into a properly formatted HTML
        attribute string suitable for inclusion in HTML tags. Each attribute is
        formatted as key='value' and multiple attributes are separated by spaces.

        Returns:
            str: A formatted HTML attribute string containing all node attributes,
                or an empty string if no attributes exist. For example, if the node
                has attributes {'class': 'container', 'id': 'main'}, this returns
                "class='container' id='main'".
        """
        combined_attributes = " ".join(
            f"{key}='{value}'" for key, value in self.attributes.items()
        )
        return combined_attributes if combined_attributes else ""

    def remove_attrs(self) -> None:
        """Remove all attributes from this node.

        Clears the node's attributes dictionary by setting it to an empty dictionary.
        This effectively removes all HTML attributes that were previously assigned
        to this node, resetting it to have no attributes.

        Returns:
            None: This method modifies the node's attributes in place and
            returns nothing.
        """
        self.attributes = {}

    def update_attr(
        self, attribute_name: str, new_value: str, create_new: bool = True
    ) -> None:
        """Update or create an HTML attribute for this node.

        Modifies an existing attribute or creates a new one based on the create_new
        parameter. When create_new is True, the attribute will be added regardless
        of whether it already exists. When create_new is False, the attribute will
        only be updated if it already exists in the node's attributes.

        Args:
            attribute_name (str): The name of the HTML attribute to update or create.
            new_value (str): The new value to assign to the specified attribute.
            create_new (bool, optional): Whether to create the attribute if it doesn't
                exist. If True, creates new attributes or updates existing ones. If
                False, only updates attributes that already exist. Defaults to True.

        Returns:
            None: This method modifies the node's attributes in place and
            returns nothing.
        """
        if create_new:
            self.attributes[attribute_name] = new_value
        else:
            if attribute_name in self.attributes:
                self.attributes[attribute_name] = new_value

    def get_attr(self, attribute_name: str) -> str:
        """Retrieve the value of a specific attribute.
        Returns:
            str: The value of the specified attribute, or None if the
            attribute does not exist.
            If the attribute does not exist, this method returns empty string.
        """
        return self.attributes.get(attribute_name, "")

    def remove_attr(self, attribute_name: str) -> None:
        """
        if attribute_name in self.attributes:
            del self.attributes[attribute_name]
        """
        if attribute_name in self.attributes:
            del self.attributes[attribute_name]

    @classmethod
    def introspect_attributes(
        cls, tag_name: str, attributes: dict[str, str]
    ) -> dict[str, str]:
        """Validate and process HTML attributes for a specific tag.

        This method takes a dictionary of attributes and validates them against
        the allowed attributes for the given HTML tag. It filters out invalid
        attributes and processes the values of valid ones through introspection.

        Args:
            tag_name (str): The name of the HTML tag for which attributes are
            being validated.
            attributes (dict[str, str]): A dictionary of attribute names and
            their values
                to be validated and processed.

        Returns:
            dict[str, str]: A dictionary containing only the valid attributes with their
                processed values. Invalid attributes are excluded from the result.
        """
        cleaned_attrs = cls.clean_attrs_names(tag_name, tuple(attributes.keys()))
        return dict(
            filter(
                lambda item: item[0] in cleaned_attrs and item[1] is not None,
                attributes.items(),
            )
        )

    @classmethod
    def clean_attrs_names(
        cls, tag_name: str, attributes: tuple[str, ...]
    ) -> tuple[str, ...]:
        """Filter and validate attribute names for a specific HTML tag.

        This method validates a collection of attribute names against the allowed
        attributes for a given HTML tag. It returns only the valid attribute names
        and prints a warning message for any invalid attributes that are not
        recognized for the specified tag.

        Args:
            tag_name (str): The name of the HTML tag for which attributes are
            being validated.
            attributes (tuple[str, ...]): A tuple of attribute names to be validated
                against the allowed attributes for the specified tag.

        Returns:
            tuple[str, ...]: A tuple containing only the valid attribute names that are
                allowed for the specified HTML tag. Invalid attributes are excluded
                from the result.
        """
        clean_attrs = []
        all_possible_attrs = cls.__combine_all_possible_attributes(tag_name)
        for attr_name in attributes:
            if attr_name in all_possible_attrs:
                clean_attrs.append(attr_name)
            else:
                print(f"Unknown attribute '{attr_name}' for tag '{tag_name}'.")
        return tuple(clean_attrs)

    @classmethod
    def __combine_all_possible_attributes(cls, tag_name: str) -> tuple[str, ...]:
        """Combine all valid attributes for a specific HTML tag.

        This method aggregates all possible attributes that can be applied to a given
        HTML tag by combining global attributes, event attributes, and tag-specific
        attributes. Global and event attributes are applicable to all HTML elements,
        while tag-specific attributes are retrieved from the HTML_TAGS mapping.

        Args:
            tag_name (str): The name of the HTML tag for which to retrieve all
                possible valid attributes.

        Returns:
            tuple[str, ...]: A tuple containing all valid attribute names for the
                specified HTML tag, including global attributes, event attributes,
                and tag-specific attributes. If the tag has no specific attributes
                defined, only global and event attributes are returned.
        """
        full_attrs: tuple[str, ...] = (
            html_tag_mappers.GLOBAL_ATTRIBUTES + html_tag_mappers.EVENT_ATTRIBUTES
        )
        main_attrs = html_tag_mappers.HTML_TAGS.get(tag_name, ())

        if len(main_attrs) == 2:
            full_attrs += main_attrs[0]

        return full_attrs

    def get_unique_id(self) -> str:
        return self.attributes.get("id", "")
