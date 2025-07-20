from mcp.server import Server
from mcp.types import Tool
import inspect
import typing
from typing import (
    _AnnotatedAlias,
)  # Using _AnnotatedAlias for isinstance check

TOOL_REGISTRY = []


def register(func):
    """
    Decorator to register a function in the TOOL_REGISTRY.
    The function's metadata (name, docstring, signature) will be used
    for tool creation.
    """
    TOOL_REGISTRY.append(func)
    return func


def _generate_schema_from_func(func):
    """
    Generates a JSON schema for the input parameters of a function
    based on type hints and Annotated metadata.
    """
    sig = inspect.signature(func)
    props = {}
    required = []

    for name, param in sig.parameters.items():
        if name == "self":  # Skip 'self' for methods
            continue
        # Skip 'client' or other injected params if they were not meant to be user-facing
        if name == "client":
            continue

        hint = param.annotation
        description = ""

        # Check if the type hint is Annotated
        is_annotated = isinstance(hint, _AnnotatedAlias)

        if is_annotated:
            # First metadata argument in Annotated is usually the description string
            if (
                hasattr(hint, "__metadata__")
                and hint.__metadata__
                and isinstance(hint.__metadata__[0], str)
            ):
                description = hint.__metadata__[0]
            actual_type = hint.__origin__  # The actual type (e.g., str, int)
        else:
            actual_type = hint

        # Determine JSON schema type based on Python type
        js_type = "string"  # Default
        if actual_type == int:
            js_type = "integer"
        elif actual_type == float:
            js_type = "number"
        elif actual_type == bool:
            js_type = "boolean"
        elif actual_type == list:
            js_type = "array"
        elif actual_type == dict:
            js_type = "object"
        # Handle Optional types for js_type (e.g. Optional[int] is still "integer" in schema, nullability handled by 'required')
        elif (
            hasattr(actual_type, "__origin__")
            and actual_type.__origin__ is typing.Union
        ):  # Checks for Union, common in Optional
            non_none_args = [t for t in actual_type.__args__ if t is not type(None)]
            if (
                len(non_none_args) == 1
            ):  # This is how Optional[X] looks (Union[X, NoneType])
                optional_type = non_none_args[0]
                if optional_type == int:
                    js_type = "integer"
                elif optional_type == float:
                    js_type = "number"
                elif optional_type == bool:
                    js_type = "boolean"
                elif optional_type == list:
                    js_type = "array"
                elif optional_type == dict:
                    js_type = "object"

        props[name] = {"type": js_type}
        if description:
            props[name]["description"] = description

        # Determine if parameter is required
        is_optional_type = (
            hasattr(actual_type, "__origin__")
            and actual_type.__origin__ is typing.Union
            and type(None) in actual_type.__args__
        )
        if param.default == inspect.Parameter.empty and not is_optional_type:
            required.append(name)

    schema = {"type": "object", "properties": props}
    if required:
        schema["required"] = required
    return schema


def register_all_tools(server: Server, tool_instances=None):
    """
    Registers all functions from TOOL_REGISTRY with the MCP server.
    Functions are bound to the appropriate instance if tool_instances are provided.
    tool_instances can be a single object or a list of objects.
    The TOOL_REGISTRY is cleared ONCE after processing all registered functions.
    """
    if not hasattr(server, "tools") or server.tools is None:
        server.tools = []

    instances_to_process = []
    if tool_instances:
        if isinstance(tool_instances, list):
            instances_to_process.extend(tool_instances)
        else:
            instances_to_process.append(tool_instances)

    for func_to_register in TOOL_REGISTRY:
        bound_func = None
        owning_instance = None

        # Try to bind to an instance if instances are provided
        if instances_to_process:
            for instance in instances_to_process:
                # Check if func_to_register (unbound method) is part of this instance's class
                class_method = getattr(type(instance), func_to_register.__name__, None)
                if class_method is func_to_register:
                    bound_func = getattr(
                        instance, func_to_register.__name__
                    )  # Bind to instance
                    owning_instance = instance
                    break

        # If not bound, it could be a standalone function
        if not bound_func:
            sig = inspect.signature(func_to_register)
            if (
                not sig.parameters or "self" not in sig.parameters
            ):  # Check it's not an unbound method
                bound_func = func_to_register
            else:
                # Unbound method whose instance wasn't in tool_instances
                # print(f"Warning: Method {func_to_register.__qualname__} was registered but its instance was not provided. Skipping.")
                continue  # Skip this function

        tool_name = func_to_register.__name__
        # Clean up name for internal methods (e.g., _create_envelope_impl -> create_envelope)
        if owning_instance and tool_name.startswith("_"):
            tool_name = tool_name.lstrip("_").replace("_impl", "")

        docstring = inspect.getdoc(func_to_register) or ""
        description = (
            docstring.splitlines(False)[0] if docstring else f"Tool: {tool_name}"
        )

        input_schema = _generate_schema_from_func(func_to_register)

        tool = Tool(
            name=tool_name,
            description=description,
            func=bound_func,
            inputSchema=input_schema,
        )
        server.tools.append(tool)

    # TOOL_REGISTRY.clear() # Do not clear, as modules are imported only once.
