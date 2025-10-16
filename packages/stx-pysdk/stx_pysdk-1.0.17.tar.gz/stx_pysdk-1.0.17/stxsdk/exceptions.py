from typing import List, Optional


class BaseCustomException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def __str__(self) -> str:
        return self.message


class InvalidSchemaFileException(BaseCustomException):
    def __init__(self, file: str, message: str) -> None:
        message = f"Failed to load file {file} with exception: {message}"
        super().__init__(message)


class ClientInitiateException(BaseCustomException):
    def __init__(self, message: str) -> None:
        message = f"Failed to initiate client with exception: {message}"
        super().__init__(message)


class InvalidParameterException(BaseCustomException):
    def __init__(self, request_name: str, errors: List[str]) -> None:
        message = f"Failed to process {request_name} request because of invalid parameter selection"
        self.errors = errors
        super().__init__(message)


class TokenExpiryException(BaseCustomException):
    pass


class Invalid2FACodeException(BaseCustomException):
    pass


class AuthenticationFailedException(BaseCustomException):
    def __init__(self, message: str, errors: Optional[List[str]] = None) -> None:
        self.errors = errors or []
        super().__init__(message)
