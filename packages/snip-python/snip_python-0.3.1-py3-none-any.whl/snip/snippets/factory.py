from jsonschema import Draft202012Validator

from .base import BaseSnip


def snip_class_factory(name: str, schema: dict):
    """
    Class factory that creates a new class derived from BaseSnip using the provided JSON schema.

    Parameters
    ----------
    schema : dict
        The JSON schema to use for the class creation. Has to be a valid
        snip schema.

    Returns
    -------
    class
        The newly created class derived from BaseSnip.
    """
    # Check if schema is a valid snip schema
    __snip_schema_validator(schema)

    class DynamicSnip(BaseSnip):
        type = name
        pass

    # Set name
    DynamicSnip.__name__ = name

    return DynamicSnip


def __snip_schema_validator(schema: dict):
    """Validate a given schema to be a valid snipschema.

    Is more of a metalevel function that is used to validate
    if a given schema can be used as a snipschema.

    """
    # 1. Check schema is valid jsonschema might raise an exception
    Draft202012Validator.check_schema(schema)

    # 2. Check schema has required keys
    # book_id, data, type
    if schema.get("required") is None or not all(
        key in schema["required"] for key in ["book_id", "data", "type"]
    ):
        raise ValueError(
            "Invalid schema provided. Missing required keys. Must contain 'book_id', 'data' and 'type'."
        )

    # 3. Check that required keys are of correct type
    # book_id is an integer
    # type is a string
    # data is a object

    if "properties" not in schema:
        raise ValueError("Invalid schema provided. Missing 'properties' key.")
    properties = schema["properties"]

    type_mapping = {
        "book_id": "integer",
        "type": "string",
        "data": "object",
    }

    for key, value in type_mapping.items():
        if key not in properties:
            raise ValueError(f"Invalid schema provided. Missing property '{key}'.")
        if "type" not in properties[key]:
            raise ValueError(
                f"Invalid schema provided. Property '{key}' must have a 'type' key."
            )
        if properties[key]["type"] != value:
            raise ValueError(
                f"Invalid schema provided. Property '{key}' must be of type '{value}'."
            )

    return
