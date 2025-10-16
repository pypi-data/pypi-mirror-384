import requests
from pathlib import Path
from graphql import parse
from graphql.error import GraphQLSyntaxError
from stxsdk.exceptions import InvalidSchemaFileException
from stxsdk.config.configs import Configs
from stxsdk.utils import get_latest_graphql_version

def load_schema_from_path(schema_file_name: str, env: str) -> str:
    """
    It loads a schema file from the config directory, parses it, and returns the schema as a string
    :parameter schema_file_name: The name of the schema file to load
    :parameter env: The environment name used for version fetching
    :return: The schema is being returned.
    """
    schema = ""
    version =  get_latest_graphql_version(env)
    if version:
        url = f"{Configs.SCHEMA_PATH}/{version}/{schema_file_name}"
        response = requests.get(url)
        if response.ok:
            schema = response.text
    else:
        path_to_file = f"{Path(__file__).parent.parent}/config/{schema_file_name}"
        with open(path_to_file, "r", encoding="utf-8") as schema_file:
            schema = schema_file.read()
    try:
        parse(schema)
    except GraphQLSyntaxError as exc:
        raise InvalidSchemaFileException("path_to_file", str(exc)) from exc
    return schema