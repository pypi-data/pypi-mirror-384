import os
import jsonschema
import json
import sys

from shoestring_assembler.interface.events import FatalError, Update
from functools import cache


schema_dir = os.path.dirname(os.path.realpath(__file__))


class MetaSchema:

    @classmethod
    def validate(cls, meta_content):
        meta_schema = load_schema("meta.schema.json")
        schema_validate(meta_content, meta_schema)


class RecipeSchema:
    @classmethod
    def validate(cls, recipe_content):
        recipe_schema = load_schema("recipe.schema.json")
        schema_validate(recipe_content, recipe_schema)


@cache
def load_schema(schema):
    schema_location = os.path.join(schema_dir, schema)

    try:
        with open(
            schema_location, "rb"
        ) as file:
            # description="Loading Schema..."
            schema = json.load(file)
            return schema
    except FileNotFoundError:
        raise FatalError(
            f"Unable to find {schema.split('.',1)[0]} schema. Expected to find it at: {schema_location}"
        )


def schema_validate(config, schema):
    jsonschema.validate(
        instance=config,
        schema=schema,
        format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER,
    )
