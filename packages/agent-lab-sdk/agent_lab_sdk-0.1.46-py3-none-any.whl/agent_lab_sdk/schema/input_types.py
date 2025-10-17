from typing import List, Optional, Any, Literal
from enum import Enum
from pydantic import BaseModel
from pydantic.json_schema import WithJsonSchema


class Visibility(str, Enum):
    """
    Enum representing visibility states for input fields.

    Attributes:
        ALWAYS: Field is always visible
        START: Field is visible only at start
        AFTER_START: Field is visible after start
    """
    ALWAYS = "always"
    START = "start"
    AFTER_START = "after_start"


def MainInput(placeholder: str | None = None, visibility: str | Visibility = Visibility.ALWAYS) -> type:
    """
    Factory function for creating a main input type with optional placeholder.

    Args:
        placeholder: Optional placeholder text for the input field
        visibility: Visibility state of the field (default: "always")

    Returns:
        Type annotation for main input field
    """
    return WithJsonSchema({
        "type": "main-input",
        "placeholder": placeholder,
        "visibility": visibility.value if isinstance(visibility, Visibility) else visibility,
    })


def StringInput(default: str | None = None, title: str | None = None, description: str | None = None,
                hidden: bool | None = False, depends: str | None = None, visibility: str | Visibility = Visibility.ALWAYS) -> type:
    """
    Factory function for creating a string input type.

    Args:
        default: Default value for the string input
        title: Title for the string input
        description: Description text for the string input
        hidden: Whether the input should be hidden in the UI
        depends: Specifies the parameter that this value depends on or is derived from.
        visibility: Visibility state of the field (default: "always")

    Returns:
        Type annotation for string input field
    """
    return WithJsonSchema({
        "type": "input-string",
        "default": default,
        "title": title,
        "description": description,
        "hidden": hidden,
        "depends": depends,
        "visibility": visibility.value if isinstance(visibility, Visibility) else visibility,
    })


def StringArrayInput(placeholder: str | None = None, title: str | None = None, description: str | None = None,
                     group: str | None = None, hidden: bool | None = False, depends: str | None = None, visibility: str | Visibility = Visibility.ALWAYS) -> type:
    """
    Factory function for creating a string array input type.

    Args:
        placeholder: Placeholder text for the input field
        title: Title for the string array input
        description: Description text for the string array input
        group: Group name for organizing inputs in the UI
        hidden: Whether the input should be hidden in the UI
        depends: Specifies the parameter that this value depends on or is derived from.
        visibility: Visibility state of the field (default: "always")

    Returns:
        Type annotation for string array input field
    """
    return WithJsonSchema({
        "type": "string[]",
        "placeholder": placeholder,
        "title": title,
        "description": description,
        "group": group,
        "hidden": hidden,
        "depends": depends,
        "visibility": visibility.value if isinstance(visibility, Visibility) else visibility,
    })


def StringArrayInputInline(placeholder: str | None = None, title: str | None = None, description: str | None = None,
                     group: str | None = None, hidden: bool | None = False, depends: str | None = None, visibility: str | Visibility = Visibility.ALWAYS) -> type:
    """
    Factory function for creating a string array input inline type.

    Args:
        placeholder: Placeholder text for the input field
        title: Title for the string array input
        description: Description text for the string array input
        group: Group name for organizing inputs in the UI
        hidden: Whether the input should be hidden in the UI
        depends: Specifies the parameter that this value depends on or is derived from.
        visibility: Visibility state of the field (default: "always")

    Returns:
        Type annotation for string array input field
    """
    return WithJsonSchema({
        "type": "string[]-inline",
        "placeholder": placeholder,
        "title": title,
        "description": description,
        "group": group,
        "hidden": hidden,
        "depends": depends,
        "visibility": visibility.value if isinstance(visibility, Visibility) else visibility,
    })


def NumberInput(default: float | None = None, title: str | None = None, description: str | None = None,
                hidden: bool | None = False, depends: str | None = None, visibility: str | Visibility = Visibility.ALWAYS) -> type:
    """
    Factory function for creating a number input type.

    Args:
        default: Default value for the number input
        title: Title for the number input
        description: Description text for the number input
        hidden: Whether the input should be hidden in the UI
        depends: Specifies the parameter that this value depends on or is derived from.
        visibility: Visibility state of the field (default: "always")

    Returns:
        Type annotation for number input field
    """
    return WithJsonSchema({
        "type": "input-number",
        "default": default,
        "title": title,
        "description": description,
        "hidden": hidden,
        "depends": depends,
        "visibility": visibility.value if isinstance(visibility, Visibility) else visibility,
    })


class SelectOption(BaseModel):
    """
    Model representing an option in a select input.
    
    Attributes:
        label: Display label for the option
        value: Actual value of the option
        description: Optional description for the option
    """
    label: str
    value: str
    description: Optional[str] = None


def SelectInput(items: List[Any] = [], title: str | None = None, group: str | None = None, default: str | None = None,
                hidden: bool | None = False, depends: str | None = None, visibility: str | Visibility = Visibility.ALWAYS) -> type:
    """
    Factory function for creating a select input type.

    Args:
        items: List of SelectOption objects or dictionaries
        title: Title for the select input
        group: Group name for organizing inputs in the UI
        default: Default selected value
        hidden: Whether the input should be hidden in the UI
        depends: Specifies the parameter that this value depends on or is derived from.
        visibility: Visibility state of the field (default: "always")

    Returns:
        Type annotation for select input field
    """
    return WithJsonSchema({
        "type": "select",
        "title": title,
        "items": items,
        "group": group,
        "default": default,
        "hidden": hidden,
        "depends": depends,
        "visibility": visibility.value if isinstance(visibility, Visibility) else visibility,
    })


def CheckboxInput(title: str | None = None, group: str | None = None, description: str | None = None,
                  default: bool | None = False, hidden: bool | None = False, depends: str | None = None, visibility: str | Visibility = Visibility.ALWAYS) -> type:
    """
    Factory function for creating a checkbox input type.

    Args:
        title: Title for the checkbox
        group: Group name for organizing inputs in the UI
        description: Description text for the checkbox
        default: Default checked state
        hidden: Whether the input should be hidden in the UI
        depends: Specifies the parameter that this value depends on or is derived from.
        visibility: Visibility state of the field (default: "always")

    Returns:
        Type annotation for checkbox input field
    """
    return WithJsonSchema({
        "type": "checkbox",
        "title": title,
        "group": group,
        "description": description,
        "default": default,
        "hidden": hidden,
        "depends": depends,
        "visibility": visibility.value if isinstance(visibility, Visibility) else visibility,
    })


def SwitchInput(title: str | None = None, group: str | None = None, description: str | None = None,
                  default: bool | None = False, hidden: bool | None = False, depends: str | None = None, visibility: str | Visibility = Visibility.ALWAYS) -> type:
    """
    Factory function for creating a switch input type.

    Args:
        title: Title for the switch
        group: Group name for organizing inputs in the UI
        description: Description text for the switch
        default: Default checked state
        hidden: Whether the input should be hidden in the UI
        depends: Specifies the parameter that this value depends on or is derived from.
        visibility: Visibility state of the field (default: "always")

    Returns:
        Type annotation for switch input field
    """
    return WithJsonSchema({
        "type": "switch",
        "title": title,
        "group": group,
        "description": description,
        "default": default,
        "hidden": hidden,
        "depends": depends,
        "visibility": visibility.value if isinstance(visibility, Visibility) else visibility,
    })


def FileInput(title: str | None = None, file_extensions: str | None = None, group: str | None = None,
              hidden: bool | None = False, depends: str | None = None, view: Literal["button", "dropzone"] | None = None,
              visibility: str | Visibility = Visibility.ALWAYS) -> type:
    """
    Factory function for creating a single file input type.

    Args:
        title: Title for the file input
        file_extensions: Comma-separated list of allowed file extensions (e.g., ".pdf,.txt")
        group: Group name for organizing inputs in the UI
        hidden: Whether the input should be hidden in the UI
        depends: Specifies the parameter that this value depends on or is derived from.
        view: View mode for the file input ("button" or "dropzone")
        visibility: Visibility state of the field (default: "always")

    Returns:
        Type annotation for file input field
    """
    return WithJsonSchema({
        "type": "file",
        "title": title,
        "fileExtensions": file_extensions,
        "group": group,
        "hidden": hidden,
        "depends": depends,
        "view": view,
        "visibility": visibility.value if isinstance(visibility, Visibility) else visibility,
    })


def FilesInput(title: str | None = None, file_extensions: str | None = None, group: str | None = None,
               hidden: bool | None = False, depends: str | None = None, limit: int | None = 10,
               view: Literal["button", "dropzone"] | None = None, visibility: str | Visibility = Visibility.ALWAYS) -> type:
    """
    Factory function for creating a multiple files input type.

    Args:
        title: Title for the files input
        file_extensions: Comma-separated list of allowed file extensions (e.g., ".pdf,.txt")
        group: Group name for organizing inputs in the UI
        hidden: Whether the input should be hidden in the UI
        depends: Specifies the parameter that this value depends on or is derived from.
        limit: Limit count files.
        view: View mode for the files input ("button" or "dropzone")
        visibility: Visibility state of the field (default: "always")

    Returns:
        Type annotation for files input field
    """
    return WithJsonSchema({
        "type": "files",
        "title": title,
        "fileExtensions": file_extensions,
        "group": group,
        "hidden": hidden,
        "depends": depends,
        "limit": limit,
        "view": view,
        "visibility": visibility.value if isinstance(visibility, Visibility) else visibility,
    })
