
from typing import List, Optional, Any, Dict, Type, TypeVar, Union
from pydantic import Field, BaseModel, create_model

# Use path imports for types
from chronulus_core.types.attribute import ImageFromUrl, ImageFromBytes, ImageFromFile, Image, TextFromFile, Text, PdfFromFile, Pdf

BaseModelSubclass = TypeVar('BaseModelSubclass', bound=BaseModel)


type_mapping = {
    "integer": int,
    "string": str,
    "number": float,
    "boolean": bool,
    "array": List,
    "object": dict,
    "null": type(None),
    "ImageFromUrl": ImageFromUrl,
    "ImageFromBytes": ImageFromBytes,
    "ImageFromFile": ImageFromFile,
    "Image": Image,
    "Text": Text,
    "TextFromFile": TextFromFile,
    "Pdf": Pdf,
    "PdfFromFile": PdfFromFile,
    }


serialization_type_mapping = {
    "integer": int,
    "string": str,
    "number": float,
    "boolean": bool,
    "array": List,
    "object": dict,
    "null": type(None),
    "ImageFromUrl": ImageFromUrl,
    "ImageFromBytes": Image,
    "ImageFromFile": Image,
    "Image": Image,
    "Text": Text,
    "TextFromFile": Text,
    "Pdf": Pdf,
    "PdfFromFile": Pdf,
}


class InputModelInfo(BaseModel):
    validation_schema: dict = Field(description="BaseModel json schema from model_json_schema(mode='validation')")
    serialization_schema: dict = Field(description="BaseModel json schema from model_json_schema(mode='serialization')")


def create_model_from_schema(schema, type_mapping: Dict[str, Type] = type_mapping):

    # Process $defs first to create a mapping of referenced models
    model_definitions = {}
    if "$defs" in schema:
        for def_name, def_schema in schema.get("$defs", {}).items():
            # Recursively create models for each definition
            model_definitions[def_name] = create_model_from_schema(def_schema, type_mapping)
            # Add to type_mapping for future reference resolution
            type_mapping[def_name] = model_definitions[def_name]

    fields = {}
    properties = schema.get("properties", {})

    for field_name, field_schema in properties.items():
        # Create field metadata with description and title if available
        field_metadata = {}
        if "description" in field_schema:
            field_metadata["description"] = field_schema["description"]

        if "title" in field_schema:
            field_metadata["title"] = field_schema["title"]

        # Handle array with items
        if field_schema.get("type") == "array" and "items" in field_schema:
            items_schema = field_schema["items"]

            # Handle item references to definitions
            if "$ref" in items_schema:
                ref_name = items_schema["$ref"].split("/")[-1]
                if ref_name in type_mapping:
                    item_type = type_mapping[ref_name]
                    python_type = List[item_type]
                else:
                    python_type = List[Any]
            else:
                # Handle inline item type
                item_type = items_schema.get("type", "object")
                python_type = List[type_mapping.get(item_type, Any)]

        # Handle anyOf case
        elif "anyOf" in field_schema:
            types = []
            for type_option in field_schema["anyOf"]:
                if type_option.get("type") == "null":
                    continue
                if type_option.get("$ref") is not None:
                    ref_name = type_option.get("$ref").split("/")[-1]
                    python_type = type_mapping.get(ref_name, Any)
                else:
                    python_type = type_mapping.get(type_option.get("type"), Any)

                types.append(python_type)

            # If we found "null" in anyOf, make it Optional
            if any(type_option.get("type") == "null" for type_option in field_schema["anyOf"]):
                python_type = Optional[types[0]] if types else Optional[Any]
            else:
                python_type = types[0] if types else Any
        else:
            # Handle direct references
            if field_schema.get("$ref") is not None:
                ref_name = field_schema.get("$ref").split("/")[-1]
                python_type = type_mapping.get(ref_name, Any)
            else:
                field_type = field_schema.get("type", "object")
                python_type = type_mapping.get(field_type, Any)

        # Handle default values
        if "default" in field_schema:
            field_metadata["default"] = field_schema["default"]

        # Determine if field is required
        is_required = field_name in schema.get("required", [])

        # Create field definition
        if is_required:
            if field_metadata:
                fields[field_name] = (python_type, Field(..., **field_metadata))
            else:
                fields[field_name] = (python_type, ...)
        else:
            default_value = field_metadata.pop("default", None) if "default" in field_metadata else None
            if field_metadata:
                fields[field_name] = (Optional[python_type], Field(default_value, **field_metadata))
            else:
                fields[field_name] = (Optional[python_type], default_value)

    model_name = schema.get("title", "InputItemModel")

    # Pass through model description if available
    model_config = {}
    if "description" in schema:
        model_config["model_description"] = schema["description"]

    # Create the model
    model = create_model(model_name, __config__=type('Config', (), model_config) if model_config else None, **fields)

    return model


def are_models_equivalent_v1(model1: BaseModelSubclass, model2: BaseModelSubclass):
    # Compare JSON schemas
    schema1 = model1.model_json_schema()
    schema2 = model2.model_json_schema()

    schema1s = model1.model_json_schema(mode='serialization')
    schema2s = model2.model_json_schema(mode='serialization')

    # Compare model configs
    config1 = model1.model_config
    config2 = model2.model_config

    # Compare validators (this is trickier)
    validators1 = getattr(model1, "__validators__", {})
    validators2 = getattr(model2, "__validators__", {})

    return schema1 == schema2 and schema1s == schema2s and config1 == config2 and validators1 == validators2


def are_models_equivalent(model1: Union[BaseModelSubclass, BaseModel], model2: Union[BaseModelSubclass, BaseModel]):

    model1_type = model1 if hasattr(model1, '__signature__') else type(model1)
    model2_type = model2 if hasattr(model2, '__signature__') else type(model2)
    model1_sig = str(model1_type.__signature__)
    model2_sig = str(model2_type.__signature__)

    model1_sig_input = model1_sig.replace("chronulus_core.types.attribute", "chronulus_core.types.inputs")
    model1_sig_attr = model1_sig.replace("chronulus_core.types.inputs", "chronulus_core.types.attribute")

    sig_check = (model1_sig == model2_sig) or (model1_sig_input == model2_sig) or (model1_sig_attr == model2_sig)

    # Compare model configs
    config1 = model1.model_config
    config2 = model2.model_config
    config_check = config1 == config2

    # Compare validators (this is trickier)
    validators1 = getattr(model1, "__validators__", {})
    validators2 = getattr(model2, "__validators__", {})
    validator_check = validators1 == validators2

    return sig_check and config_check and validator_check
