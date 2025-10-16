from typing import Any, Dict, List, Optional

from gql.dsl import DSLField, DSLMutation, DSLQuery, dsl_gql
from graphql import GraphQLList, GraphQLNonNull, validate

from stxsdk.enums import RootType
from stxsdk.exceptions import InvalidParameterException
from stxsdk.services.authentication import AuthService
from stxsdk.services.selection import Selection
from stxsdk.typings import BaseResponseType
from stxsdk.utils import format_failure_response, format_success_response

call_type_mapper = {
    RootType.MUTATION.value: DSLMutation,
    RootType.QUERY.value: DSLQuery,
}


class ProxyClient:
    def __init__(self, klass):
        """
        The __init__ function is called when an instance of the class is created.
        It takes one argument, self, which refers to the object itself.
        The __init__ function sets up variables that are part of each instance.
        :parameter self: Refer to the instance of the class
        :parameter klass: Store the class of which the object is an instance
        :returns The object of the class
        """
        self.klass = klass

    def __call__(self, *args, **kwargs):
        """
        The __call__ function is a special method that allows the class to be called as a function.
        It also provides an instance of the object, which can then have its attributes accessed.
        :parameter self: Access the instance of the class that is being created
        :parameter *args: Pass in the arguments that are passed to the class when it is instantiated
        :parameter **kwargs: Pass in the arguments to the function
        :return A new instance of the class that was called
        """
        obj = self.klass(*args, **kwargs)
        for root_type in [RootType.MUTATION.value, RootType.QUERY.value]:
            # getting the root object from the graphql schema
            root_attribute = getattr(obj.dsl_schema, root_type)
            # iterating over the available methods in the schema
            for field in root_attribute._type.fields:
                dsl_field = getattr(root_attribute, field)
                # injecting the available function as a class object with related function name
                setattr(obj, field, ProxyCall(obj, dsl_field))
        return obj


class ProxyCall:
    def __init__(self, proxy, method):
        self.__proxy = proxy
        self.__method = method
        self.__client = proxy.gqlclient
        self.__schema = proxy.dsl_schema
        self.__user = proxy.user

    def clear_method_nodes(self):
        self.method.ast_field.arguments = ()
        self.method.ast_field.selection_set = ()

    def validate_document_schema(self, document):
        """
        validating if the generated document is as per the schema
        :param document: a Document Node which can be later executed or subscribed by a
        :return: None
        """
        validation_errors = validate(self.__client.schema, document)
        if validation_errors:
            raise InvalidParameterException(
                self.__method.name, [str(error) for error in validation_errors]
            )
    
    def unwrap(self, gql_type):
        # Unwrap any non-null wrappers
        while isinstance(gql_type, (GraphQLNonNull,GraphQLList)):
            gql_type = gql_type.of_type
        return gql_type

    def generate_schema_selections(
        self, selection_object: Selection, field_type=None
    ) -> List[DSLField]:
        """
        This function is auto generating schema object selection list from the custom
        Selection objects, Selection objects are used for use ease to avoid using
        graphql schema for selection list.
        :param selection_object: Object containing requested return values
        :param field_type: DSL field type, could be scaler, list, string or int
        :return: List of requested Graphql dsl fields
        """
        selections = []
        field_type = field_type or self.method.field.type
        return_type_name = (
            self.unwrap(field_type.of_type).name
            if isinstance(field_type, (GraphQLList,GraphQLNonNull))
            else field_type.name
        )
        return_dsl_type = getattr(self.schema, return_type_name)
        for value in selection_object.values:
            dsl_field = getattr(return_dsl_type, value)
            selections.append(dsl_field)
        for value, obj in selection_object.nested_values.items():
            dsl_field = getattr(return_dsl_type, value)
            nested_selections = self.generate_schema_selections(
                obj, dsl_field.field.type
            )
            selections.append(dsl_field.select(*nested_selections))
        return selections

    def get_all_schema_selections(self) -> List[DSLField]:
        def get_selections(fields):
            values, nested = [], {}
            for field_name, field_value in fields.items():
                if isinstance(field_value, str):
                    values.append(field_name)
                else:
                    nested[field_name] = get_selections(field_value)
            return Selection(*values, **nested)

        # get all the return fields from schema object
        return_fields = self.__proxy.get_return_fields(self.__method.name)
        # generate the nested selection objects
        selections = get_selections(return_fields)
        # pass the selection objects to get the schema objects
        return self.generate_schema_selections(selections)

    @staticmethod
    def normalize_errors(errors):
        errors = [
            error["message"]
            if isinstance(error, dict) and "message" in error
            else error
            for error in errors
        ]
        return errors

    # this decorator makes sure of the authentication of the requested API
    @AuthService.authenticate
    def __call__(
        self,
        params: Optional[Dict[str, Any]] = None,
        selections: Optional[Selection] = None,
    ) -> BaseResponseType:
        """
        It takes the arguments passed to the method, creates a request object,
        converts it to a GraphQL query, validates it against the schema, and then executes it.
        """
        try:
            params = params if isinstance(params, dict) else {}
            parent = self.__method.parent_type
            proxy_call_type = call_type_mapper[str(parent)]
            # all the proxy call methods are dsl field objects that are used to generate request
            # and these objects persist the request nodes for chain operations, we don't need it
            # in our case, clearing them before making request to avoid parameter conflicts
            self.clear_method_nodes()
            if isinstance(selections, Selection):
                # generating schema selection from the custom selection objects
                selections = self.generate_schema_selections(selections)
            else:
                # if custom selections are not provided then generate schema selection of
                # all the fields as default
                selections = self.get_all_schema_selections()
            # generate graphql schema request object
            request = self.__method(**params).select(*selections)
            # convert schema object to request document
            document = dsl_gql(proxy_call_type(request))
            # validate the generated schema document
            self.validate_document_schema(document)
            # execute the graphql request
            response = self.__client.execute(document)
            return format_success_response(
                data=response,
            )
        # this exception raised on invalid generated document
        except InvalidParameterException as exc:
            return format_failure_response(
                errors=exc.errors,
                message=exc.message,
            )
        # it handles general raised exceptions
        except Exception as exc:
            # normalizing the errors to return fixed error structure
            errors = self.normalize_errors(exc.errors) if hasattr(exc, "errors") else []
            return format_failure_response(
                errors=errors,
                message=errors[0] if errors else str(exc),
            )

    def __repr__(self):
        return self.__method.__repr__()

    @property
    def method(self):
        return self.__method

    @property
    def user(self):
        return self.__user

    @property
    def client(self):
        return self.__client

    @property
    def schema(self):
        return self.__schema

    @property
    def proxy(self):
        return self.__proxy
