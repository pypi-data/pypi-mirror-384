import os
from typing import Any, Dict, List, Optional

from gql import Client
from gql.dsl import DSLSchema
from gql.transport.requests import RequestsHTTPTransport
from graphql import GraphQLList

from stxsdk.config.channels import CHANNELS
from stxsdk.config.configs import Configs
from stxsdk.exceptions import ClientInitiateException
from stxsdk.services.channel import Channel
from stxsdk.services.proxy import ProxyClient
from stxsdk.services.schema import load_schema_from_path
from stxsdk.storage.user_storage import User
from stxsdk.enums import ChannelEvents, Channels


@ProxyClient
class StxClient:
    """
    The StxClient class is a wrapper around the STX graphql HTTP API
    This client includes all the available http request methods that are
    extracted from the schema.graphql
    This class is decorated with ProxyClient decorator class that is
    responsible for extracting and injecting the available API methods
    This class is using HttpTransport for the communication with the API server
    """

    def __init__(self, env: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> None:
        """
        :param env: API environment
        :param config: graphql schema file path
        """
        api_environment = env or os.getenv("API_ENV") or Configs.API_ENV
        host = Configs.ENV_HOSTS.get(api_environment)
        if host is None:
            raise ClientInitiateException(f"Unknown API environment: {api_environment}")
        defaults = {
            "env": api_environment,
            "url": Configs.GRAPHQL_URL.format(host=host),
            "schema": load_schema_from_path("schema.graphql", api_environment),
        }
        # creating settings dict data structure for storing client configs
        settings = dict(defaults)
        config = config if isinstance(config, dict) else {}
        # overriding the default config with the customly passed config
        settings.update(config)
        # injecting the configuration as attribute to the object
        for key, value in settings.items():
            setattr(self, key, value)
        if not self.url:
            raise ClientInitiateException("API Url not set.")
        if not self.schema:
            raise ClientInitiateException("Invalid schema or schema not found.")
        # creating transport object to the client class to handle the
        # http requests to the graphql server
        transport = RequestsHTTPTransport(url=self.url, verify=True, retries=3)
        # here Client is the wrapper class for generating the graphql queries
        self.gqlclient = Client(transport=transport, schema=self.schema)
        # dsl schema takes the raw schema and provides the object based schema
        self.dsl_schema = DSLSchema(self.gqlclient.schema)
        # here User is a singleton user object, shared by all the StxClient objects
        self.user = User()

    def get_operations(self) -> List[str]:
        """
        This function returns the list of available API operations
        """
        schema = self.gqlclient.schema
        return list(schema.mutation_type.fields) + list(schema.query_type.fields)

    def get_return_fields(self, method_name: str) -> Dict[str, Any]:
        """
        This function returns the available return values of the requested operation
        :param method_name: name of the operation
        """

        def get_fields(fields):
            """
            It takes fields as an argument and iterates over it, for each field:
                If the field has sub-fields, it calls get_fields recursively on the sub-fields
                and sets the result as the value for the field name in the return_fields dictionary.
                If the field is a GraphQLList, it calls get_fields on the fields of the list element type
                and sets the result as the value for the field name in the return_fields dictionary.
                Otherwise, it sets the string representation of the field type as the value for the
                field name in the return_fields dictionary.
            """
            return_fields = {}
            for field_name, field_obj in fields.items():
                # if the field type is a nested object, it contains objects of scaler fields
                if hasattr(field_obj.type, "fields"):
                    return_fields[field_name] = get_fields(field_obj.type.fields)
                # if the field type is a list of nested objects
                elif isinstance(field_obj.type, GraphQLList):
                    # its a fail-safe check for the condition where the object is nested object
                    # because the above condition is only checking for list condition not
                    # the object itself and object could be a singular type
                    # eg. GraphQLList([NestedObject]) | GraphQLList([ScalerObject])
                    if hasattr(field_obj.type.of_type, "fields"):
                        return_fields[field_name] = get_fields(
                            field_obj.type.of_type.fields
                        )
                else:
                    # it handles the scaler type fields
                    return_fields[field_name] = str(field_obj.type)
            return return_fields

        # if the method doesn't exist in the object with the input name
        if not hasattr(self, method_name):
            raise AttributeError()
        # get the attribute reference from the client object,
        # here each attribute is the proxy
        method = getattr(self, method_name).method
        method_type = method.field.type
        type_fields = (
            method_type.of_type.fields
            if isinstance(method_type, GraphQLList)
            else method_type.fields
        )
        return get_fields(type_fields)


class StxChannelClient:
    """
    This class is a wrapper around the Phoenix Channel that allows to call the
    Channel class methods as if they were methods of the `StxChannelClient` class
    It uses the custom layer for the two-way communication with the websocket server
    via provided phoenix channels.
    This class is used for the Async implementation of the channels
    """

    def __init__(
        self, env: Optional[str] = None, config: Optional[Dict[str, Any]] = None
    ):
        self.url = None
        api_environment = env or os.getenv("API_ENV") or Configs.API_ENV
        host = Configs.ENV_HOSTS.get(api_environment)
        if host is None:
            raise ClientInitiateException(f"Unknown API environment: {api_environment}")
        defaults = {"url": Configs.WS_URL.format(host=host)}
        settings = dict(defaults)
        config = config if isinstance(config, dict) else {}
        settings.update(config)
        for key, value in settings.items():
            setattr(self, key, value)
        if not self.url:
            raise ClientInitiateException("API Url not set.")
        self.__proxy = StxClient(env=api_environment)
        self.user = User()
        self.__load_operations()
        self.run_heartbeat()

    def __load_operations(self):
        """
        This function dynamically injects the available channel operation in client object
        """
        for channel_method, config in CHANNELS.items():
            for operation, channel_command in config["operations"].items():
                # creates the channel objects with their relative commands
                channel = Channel(self, channel_command)
                # set the channel object's handler reference to the client object
                setattr(self, f"{channel_method}_{operation}", channel.channel_handler)

    def run_heartbeat(self):
        """
        This function runs the heartbeat command
        """
        command = f'["null", "3", "{Channels.PHONEIX.value}", "{ChannelEvents.HEARTBEAT.value}", ""]'
        channel = Channel(self, command)
        setattr(self, f"{ChannelEvents.HEARTBEAT.value}", channel.channel_handler)


    def login(self, params):
        return self.__proxy.login(params=params)

    def confirm2Fa(self, params):
        return self.__proxy.confirm2Fa(params=params)
