from apppy.fastql.annotation.error import fastql_type_error
from apppy.fastql.annotation.interface import fastql_type_interface


# NOTE: Do not use GraphQLError directly
# instead use GraphQLClientError or GraphQLServerError
@fastql_type_interface
class GraphQLError(BaseException):
    """Generic base class for any error raised in a GraphQL API"""

    code: str

    def __init__(self, code: str):
        self.code: str = code


@fastql_type_interface
class GraphQLClientError(GraphQLError):
    """Base class for any GraphQL error raised related to bad client input"""

    def __init__(self, code: str = "generic_client_error"):
        super().__init__(code)


@fastql_type_interface
class GraphQLServerError(GraphQLError):
    """Base class for any GraphQL error raised related to internal server processing"""

    def __init__(self, code: str = "generic_server_error"):
        super().__init__(code)


@fastql_type_error
class TypedIdInvalidPrefixError(GraphQLClientError):
    """Raised when a TypedId encounters an invalid prefix"""

    id: str
    id_type: str

    def __init__(self, id: str, id_type: str):
        super().__init__("typed_id_invalid_prefix")
        self.id = id
        self.id_type = id_type
