from typing import Any

from nodie.constants.css_properties import CSS_PROPERTIES
from nodie.helpers.helpers import normalize_string_values


class InlineStyleAttributes:
    """Validator and manager for inline CSS styles.

    Validates CSS property names and values, ensuring they conform to
    standard CSS specifications.
    """

    def __init__(self, styles: dict[str, str]) -> None:
        """Initialize inline styles with validation.

        Args:
            styles: Dictionary of CSS property-value pairs
        """
        self.styles = self.validate_styles(styles)

    @classmethod
    def validate_styles(cls, styles: dict[str, str]) -> dict[str, str]:
        """Validate CSS properties and their values.

        Args:
            styles: Dictionary of CSS property-value pairs to validate

        Returns:
            Dictionary containing only valid CSS properties with cleaned values
        """
        validated_styles = {}

        for property_name, value in styles.items():
            if property_name in CSS_PROPERTIES:
                normalized_property = property_name.strip().lower()

                if cleaned_value := cls.clean_style_value(value):
                    validated_styles[normalized_property] = cleaned_value
            else:
                print(f"Warning: Invalid property '{property_name}'.")

        return validated_styles

    @staticmethod
    def clean_style_value(value: Any) -> str:
        """Clean and validate a CSS property value.

        Args:
            value: The CSS value to clean

        Returns:
            Cleaned string value, or empty string if invalid
        """
        if value is None:
            return ""

        str_value = str(value).strip()

        dangerous_patterns = ["javascript:", "expression(", "<script"]

        for pattern in dangerous_patterns:
            if pattern.lower() in str_value.lower():
                print(f"Warning: Potentially dangerous value '{str_value}' rejected.")
                return ""

        return str_value

    def to_string(self) -> str:
        """Convert styles dictionary to CSS string format.

        Returns:
            String representation of styles in CSS format (property: value;)
        """
        if not self.styles:
            return ""

        style_parts = [f"{prop}: {value}" for prop, value in self.styles.items()]
        return f" style='{'; '.join(style_parts) + ';'}' "

    def update_attr(
        self, attribute_name: str, value: str, create_new: bool = True
    ) -> None:
        """Update or add a CSS property.

        Args:
            attribute_name: Name of the CSS property
            value: Value for the property
            create_new: Whether to create new property if it doesn't exist
        """
        normalized_property = normalize_string_values(attribute_name)

        if not create_new and normalized_property not in self.styles:
            return

        cleaned_value = self.clean_style_value(value)
        if cleaned_value:
            if normalized_property in CSS_PROPERTIES:
                self.styles[normalized_property] = cleaned_value
            else:
                print(f"Warning: Invalid property '{attribute_name}'.")

    def remove_attr(self, attribute_name: str) -> None:
        """Remove a CSS property from styles.

        Args:
            attribute_name: Name of the CSS property to remove
        """
        normalized_property = attribute_name.strip().lower()
        self.styles.pop(normalized_property, None)

    def remove_attrs(self) -> None:
        """Remove all styles."""
        self.styles = {}

    def get_attr(self, attribute_name: str) -> str:
        """Get value of a specific CSS property.

        Args:
            attribute_name: Name of the CSS property

        Returns:
            Value of the property, or empty string if not found
        """
        normalized_property = normalize_string_values(attribute_name)
        return self.styles.get(normalized_property, "")
