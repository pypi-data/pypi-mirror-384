import enum
from datetime import date
from typing import Any, Dict, Type, Union, get_args, get_origin

from pydantic import BaseModel


def find_yaml(text):
    def get_indentation(line):
        return len(line) - len(line.lstrip())

    lines = text.split("\n")
    start_index = -1
    end_index = -1

    # Find the start index
    for i, line in enumerate(lines):
        if line.strip() == "```yaml":
            start_index = i + 1
            break

    # If we didn't find the start, return the original text
    if start_index == -1:
        return ""

    end_start_index = len(lines)
    # Check if there is another yaml block starting ```yaml
    for i in range(start_index + 1, len(lines), 1):
        if lines[i] == "```yaml":
            end_start_index = i

    # Find the end index, searching from the end
    for i in range(end_start_index, start_index, -1):
        if lines[i - 1].strip() == "```":
            end_index = i
            break

    if end_index == start_index + 1:
        return ""
    elif end_index == -1:
        return ""

    # Extract YAML content
    yaml_lines = lines[start_index : end_index - 1]

    min_indent = get_indentation(lines[start_index])

    # Remove the minimum indentation from each line
    yaml_content = "\n".join(
        line[min_indent:] if line.strip() else "" for line in yaml_lines
    )

    return yaml_content.strip()


def build_comment_with_options(json_schema_extra: dict) -> str:
    """
    Build a comment string from json_schema_extra, including options if present.

    Args:
        json_schema_extra: Dictionary containing comment and optionally options

    Returns:
        Formatted comment string with options appended if they exist
    """
    if not json_schema_extra:
        return ""

    comment_parts = []

    # Add main comment if present and valid
    if "comment" in json_schema_extra:
        comment = json_schema_extra["comment"]
        # Only add comment if it's a non-None value
        if comment is not None:
            # Convert non-string comments to string
            comment_parts.append(str(comment))

    # Add options if present
    if "options" in json_schema_extra:
        options = json_schema_extra["options"]
        if options and isinstance(options, (list, tuple)):
            options_str = ", ".join(str(opt) for opt in options)
            comment_parts.append(f"(options: {options_str})")

    if comment_parts:
        return f" # {' '.join(comment_parts)}"

    return ""


def pydantic_to_yaml_example(model_class: Type[BaseModel]) -> str:
    """
    Convert a Pydantic model class to a YAML representation with example values.

    Args:
        model_class: A class that inherits from pydantic.BaseModel

    Returns:
        A string containing the YAML representation with examples
    """
    try:
        if not issubclass(model_class, BaseModel):
            raise TypeError("Input must be a Pydantic BaseModel class")
    except TypeError as e:
        # Handle case where user passed an instance instead of a class
        if "issubclass() arg 1 must be a class" in str(e):
            raise TypeError(
                "Input must be a Pydantic BaseModel class, not an instance"
            ) from e
        # Re-raise original error if it's something else
        raise

    # Process each field to create the YAML with examples
    yaml_lines = []

    for field_name, model_field in model_class.model_fields.items():
        # Build comment with options if present
        comment = build_comment_with_options(model_field.json_schema_extra)

        # Get example from field
        example = (
            model_field.json_schema_extra.get("example")
            if model_field.json_schema_extra
            else None
        )

        # Process the example to handle Pydantic models and enums
        example = process_example_value(example)

        # If no example is provided, generate a default one based on the type
        if example is None:
            example = generate_default_example(model_field.annotation)

        # Generate YAML for this field with proper indentation
        field_annotation = model_field.annotation
        field_yaml = format_field_yaml(field_name, example, comment, field_annotation)
        yaml_lines.extend(field_yaml)

    return "\n".join(yaml_lines)


def pydantic_to_yaml(model_class: Type[BaseModel]) -> str:
    """
    Convert a Pydantic model class to a YAML representation.

    Args:
        model_class: A class that inherits from pydantic.BaseModel
    """
    return pydantic_to_yaml_example(model_class)


def format_field_yaml(
    field_name: str,
    value: Any,
    comment: str = "",
    field_annotation: Any = None,
    indent: int = 0,
) -> list:
    """
    Format a field and its value as YAML with proper indentation.

    Args:
        field_name: The name of the field
        value: The value to format
        comment: Optional comment to add
        field_annotation: The type annotation of the field
        indent: Current indentation level

    Returns:
        List of YAML lines
    """
    indent_str = " " * indent
    lines = []

    # Handle different value types
    if isinstance(value, list):
        lines.append(f"{indent_str}{field_name}:{comment}")
        # Extract list item type from annotation
        list_item_type = None
        if field_annotation:
            origin = get_origin(field_annotation)
            if origin is list:
                args = get_args(field_annotation)
                if args:
                    list_item_type = args[0]
        lines.extend(format_list_yaml(value, indent + 2, list_item_type))
    elif isinstance(value, dict):
        lines.append(f"{indent_str}{field_name}:{comment}")
        # Check if this dict represents a BaseModel
        nested_model_class = None
        if (
            field_annotation
            and isinstance(field_annotation, type)
            and issubclass(field_annotation, BaseModel)
        ):
            nested_model_class = field_annotation
        lines.extend(format_dict_yaml(value, indent + 2, nested_model_class))
    else:
        yaml_value = format_scalar_yaml(value)
        lines.append(f"{indent_str}{field_name}: {yaml_value}{comment}")

    return lines


def format_list_yaml(items: list, indent: int = 0, list_item_type: Any = None) -> list:
    """
    Format a list as YAML with proper indentation.

    Args:
        items: The list to format
        indent: Current indentation level
        list_item_type: The type of items in the list (used for BaseModel comment extraction)

    Returns:
        List of YAML lines
    """
    if not items:
        return [f"{' ' * indent}[]"]

    indent_str = " " * indent
    lines = []

    for item in items:
        if isinstance(item, dict):
            # Handle dictionary items (e.g., from BaseModel.model_dump() or generate_default_example)
            lines.append(f"{indent_str}- ")
            dict_lines = format_dict_yaml(item, indent + 2, list_item_type)
            # Merge the first line with the dash
            if dict_lines:
                first_line = dict_lines[0].strip()
                lines[-1] = f"{indent_str}- {first_line}"
                lines.extend(dict_lines[1:])
        elif isinstance(item, list):
            lines.append(f"{indent_str}- ")
            list_lines = format_list_yaml(item, indent + 2, list_item_type)
            lines.extend(list_lines)
        elif hasattr(item, "__dict__") and not isinstance(
            item, (str, int, float, bool)
        ):
            # Handle Pydantic model instances (fallback case)
            if hasattr(item, "model_dump"):
                obj_dict = item.model_dump(mode="json")
            else:
                obj_dict = item.__dict__

            if obj_dict:
                lines.append(f"{indent_str}- ")
                dict_lines = format_dict_yaml(
                    obj_dict,
                    indent + 2,
                    type(item) if hasattr(type(item), "model_fields") else None,
                )
                if dict_lines:
                    first_line = dict_lines[0].strip()
                    lines[-1] = f"{indent_str}- {first_line}"
                    lines.extend(dict_lines[1:])
            else:
                lines.append(f"{indent_str}- {{}}")
        else:
            scalar_value = format_scalar_yaml(item)
            # Strip quotes for list items to match YAML conventions
            if isinstance(item, str):
                scalar_value = scalar_value.strip('"')
            lines.append(f"{indent_str}- {scalar_value}")

    return lines


def format_dict_yaml(
    data: Dict, indent: int = 0, model_class: Type[BaseModel] = None
) -> list:
    """
    Format a dictionary as YAML with proper indentation.

    Args:
        data: The dictionary to format
        indent: Current indentation level
        model_class: Optional BaseModel class to extract comments from

    Returns:
        List of YAML lines
    """
    if not data:
        return [f"{' ' * indent}{{}}"]

    indent_str = " " * indent
    lines = []

    for key, value in data.items():
        # Build comment with options from model class if provided
        comment = ""
        if (
            model_class
            and hasattr(model_class, "model_fields")
            and key in model_class.model_fields
        ):
            field = model_class.model_fields[key]
            comment = build_comment_with_options(field.json_schema_extra)

        if isinstance(value, dict):
            lines.append(f"{indent_str}{key}:{comment}")
            # Check if this dict represents a nested BaseModel
            nested_model_class = None
            if (
                model_class
                and hasattr(model_class, "model_fields")
                and key in model_class.model_fields
            ):
                field_annotation = model_class.model_fields[key].annotation
                if isinstance(field_annotation, type) and issubclass(
                    field_annotation, BaseModel
                ):
                    nested_model_class = field_annotation
            lines.extend(format_dict_yaml(value, indent + 2, nested_model_class))
        elif isinstance(value, list):
            lines.append(f"{indent_str}{key}:{comment}")
            lines.extend(format_list_yaml(value, indent + 2))
        else:
            scalar_value = format_scalar_yaml(value)
            lines.append(f"{indent_str}{key}: {scalar_value}{comment}")

    return lines


def format_scalar_yaml(value: Any) -> str:
    """
    Format a scalar value for YAML output.

    Args:
        value: The value to format

    Returns:
        Formatted string
    """
    if value is None:
        return "null"
    elif isinstance(value, str):
        # Quote strings
        return f'"{value}"'
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, (set, tuple)):
        return format_scalar_yaml(list(value))

    return str(value)


def generate_default_example(type_annotation):
    """Generate a default example value based on the type."""
    origin = get_origin(type_annotation)
    args = get_args(type_annotation)

    # Handle Optional types
    if origin is Union and type(None) in args:
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return generate_default_example(non_none_args[0])

    # Handle BaseModel classes
    if isinstance(type_annotation, type) and issubclass(type_annotation, BaseModel):
        example_dict = {}
        for field_name, model_field in type_annotation.model_fields.items():
            # Get example from field
            example = (
                model_field.json_schema_extra.get("example")
                if model_field.json_schema_extra
                else None
            )

            # If no example is provided, generate a default one based on the type
            if example is None:
                example = generate_default_example(model_field.annotation)

            example_dict[field_name] = example

        return example_dict

    # Handle List
    if origin is list:
        if args:
            return [
                generate_default_example(args[0]),
                generate_default_example(args[0]),
            ]
        return []

    # Handle Dict
    if origin is dict:
        if len(args) >= 2:
            key_type, value_type = args[0], args[1]

            # Handle nested dictionary types like Dict[str, Dict[str, List[str]]]
            if get_origin(value_type) is dict and len(get_args(value_type)) >= 2:
                sub_key_type, sub_value_type = get_args(value_type)

                # Create a more realistic nested example
                key1 = generate_default_example(key_type)
                key2 = f"{key1}_2" if isinstance(key1, str) else key1

                # Handle nested list in dictionary
                if get_origin(sub_value_type) is list:
                    list_item_type = get_args(sub_value_type)[0]
                    sub_dict = {
                        generate_default_example(sub_key_type): [
                            generate_default_example(list_item_type),
                            generate_default_example(list_item_type),
                        ],
                        f"{generate_default_example(sub_key_type)}_2": [
                            generate_default_example(list_item_type),
                            generate_default_example(list_item_type),
                        ],
                    }
                    return {key1: sub_dict, key2: sub_dict}
                else:
                    sub_dict = {
                        generate_default_example(
                            sub_key_type
                        ): generate_default_example(sub_value_type),
                        f"{generate_default_example(sub_key_type)}_2": generate_default_example(
                            sub_value_type
                        ),
                    }
                    return {key1: sub_dict, key2: sub_dict}

            # Handle Dict[str, List[str]]
            elif get_origin(value_type) is list:
                list_item_type = get_args(value_type)[0]
                key1 = generate_default_example(key_type)
                key2 = f"{key1}_2" if isinstance(key1, str) else key1
                return {
                    key1: [
                        generate_default_example(list_item_type),
                        generate_default_example(list_item_type),
                    ],
                    key2: [
                        generate_default_example(list_item_type),
                        generate_default_example(list_item_type),
                    ],
                }

            # Simple Dict[K, V]
            else:
                key1 = generate_default_example(key_type)
                key2 = f"{key1}_2" if isinstance(key1, str) else key1
                return {
                    key1: generate_default_example(value_type),
                    key2: generate_default_example(value_type),
                }
        return {}

    # Handle Set
    if origin is set:
        if args:
            # For complex types that generate dicts, convert to a list representation
            example_item = generate_default_example(args[0])
            if isinstance(example_item, dict):
                # Sets can't contain dicts, so represent as a list in YAML
                return [example_item]
            return {example_item}
        return set()

    # Handle Tuple
    if origin is tuple:
        return tuple(generate_default_example(arg) for arg in args) if args else ()

    # Handle Enum
    if isinstance(type_annotation, type) and issubclass(type_annotation, enum.Enum):
        return list(type_annotation)[0].value

    # Handle basic types
    if type_annotation is str:
        return "example string"
    elif type_annotation is int:
        return 42
    elif type_annotation is float:
        return 3.14
    elif type_annotation is bool:
        return True
    elif type_annotation is date:
        return "2023-01-01"

    # Default fallback
    return None


def process_example_value(value: Any) -> Any:
    """
    Process an example value to handle Pydantic models, enums, and other special types.

    Args:
        value: The raw example value to process

    Returns:
        Processed value suitable for YAML serialization
    """
    if value is None:
        return None

    # Handle Pydantic model instances
    if isinstance(value, BaseModel):
        # Convert to dict with mode='json' to properly serialize enums
        return value.model_dump(mode="json")

    # Handle enum instances
    if isinstance(value, enum.Enum):
        return value.value

    # Handle lists
    if isinstance(value, list):
        return [process_example_value(item) for item in value]

    # Handle dictionaries
    if isinstance(value, dict):
        return {k: process_example_value(v) for k, v in value.items()}

    # Handle tuples
    if isinstance(value, tuple):
        return tuple(process_example_value(item) for item in value)

    # Handle sets
    if isinstance(value, set):
        return {process_example_value(item) for item in value}

    # Return other values as-is
    return value
