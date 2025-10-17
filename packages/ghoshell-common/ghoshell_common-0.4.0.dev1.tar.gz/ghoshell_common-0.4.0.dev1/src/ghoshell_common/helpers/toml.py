import tomlkit
from tomlkit import table, comment, TOMLDocument
from tomlkit.items import Table
from pydantic import BaseModel
from typing import Type, List, Optional, Union, Dict, Any
from .modules import generate_import_path

__all__ = ['read_model_from_toml', 'read_toml_dict', 'from_pydantic_to_toml', 'dump_pydantic_model_to_toml']


def read_toml_dict(toml_file_fp: str | bytes) -> dict:
    doc = tomlkit.parse(toml_file_fp)
    return doc.unwrap()


def read_model_from_toml(toml_file_fp: str | bytes, model: Type[BaseModel]) -> BaseModel:
    data = read_toml_dict(toml_file_fp)
    return model(**data)


def from_pydantic_to_toml(value: BaseModel) -> TOMLDocument:
    """
    Convert Pydantic model to TOML using JSON schema as structure guide.

    Wrote by Deepseek v3.1
    """
    doc = TOMLDocument()
    doc.add(comment(f" Generated from  pydantic BaseModel {generate_import_path(value.__class__)}"))
    schema = value.model_json_schema()
    data = value.model_dump()

    # Process the root level
    _process_schema_node(schema, data, doc, "")

    return doc


def dump_pydantic_model_to_toml(value: BaseModel) -> str:
    """
    syntax sugar
    """
    return tomlkit.dumps(from_pydantic_to_toml(value))


def _process_schema_node(
        node_schema: Dict[str, Any],
        node_data: Any,
        toml_container: Union[TOMLDocument, Table],
        path: str
) -> None:
    """Process a schema node recursively."""

    # Handle object types
    if node_schema.get('type') == 'object' or 'properties' in node_schema:
        _process_object_node(node_schema, node_data, toml_container, path)

    # Handle array types
    elif node_schema.get('type') == 'array':
        _process_array_node(node_schema, node_data, toml_container, path)

    # Handle simple types and references
    else:
        _process_leaf_node(node_schema, node_data, toml_container, path)


def _process_object_node(
        schema: Dict[str, Any],
        data: Dict[str, Any],
        parent_container: Union[TOMLDocument, Table],
        path: str
) -> None:
    """Process an object node and its properties."""

    # Add object description
    description = schema.get('description')
    if description:
        parent_container.add(comment(description))
        parent_container.add(comment(""))

    properties = schema.get('properties', {})

    for field_name, field_schema in properties.items():
        if field_name not in data or data[field_name] is None:
            continue

        field_value = data[field_name]
        field_path = f"{path}.{field_name}" if path else field_name

        # Resolve references
        if '$ref' in field_schema:
            def_name = field_schema['$ref'].split('/')[-1]
            definitions = schema.get('$defs', {})
            field_schema = definitions.get(def_name, field_schema)

        # Add field description
        field_description = field_schema.get('description')
        if field_description:
            parent_container.add(comment(field_description))

        # Create table for nested objects
        if (field_schema.get('type') == 'object' or
                'properties' in field_schema or
                '$ref' in field_schema):

            if isinstance(field_value, dict):
                nested_table = table()
                parent_container[field_name] = nested_table
                _process_schema_node(field_schema, field_value, nested_table, field_path)
            else:
                parent_container[field_name] = field_value
        else:
            # Simple value
            parent_container[field_name] = field_value

        # Add separator
        parent_container.add(comment(""))


def _process_array_node(
        schema: Dict[str, Any],
        data: List[Any],
        parent_container: Union[TOMLDocument, Table],
        path: str
) -> None:
    """Process array nodes."""
    # For arrays, we just add the value directly
    # TOML doesn't support complex objects in arrays well
    parent_container[path.split('.')[-1]] = data


def _process_leaf_node(
        schema: Dict[str, Any],
        data: Any,
        parent_container: Union[TOMLDocument, Table],
        path: str
) -> None:
    """Process leaf nodes (simple values)."""
    field_name = path.split('.')[-1] if '.' in path else path
    parent_container[field_name] = data
