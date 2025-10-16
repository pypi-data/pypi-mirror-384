from typing import Any, Dict, List, Optional, Union

from typing_extensions import TypedDict

DataType = Optional[Union[List[Dict[str, Any]], Dict[str, Any]]]


class BaseResponseType(TypedDict):
    success: bool
    data: DataType
    errors: Optional[List[str]]
    message: str


class FailureResponse(BaseResponseType):
    pass


class SuccessResponse(BaseResponseType):
    pass


class ChannelMessage(TypedDict):
    closed: bool
    message_received: bool
    message: str
    data: Optional[List[Union[str, None, Dict[str, Any]]]]
