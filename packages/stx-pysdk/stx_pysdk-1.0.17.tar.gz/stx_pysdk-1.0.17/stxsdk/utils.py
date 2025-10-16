import requests
from typing import List, Optional
from stxsdk.typings import DataType, FailureResponse, SuccessResponse
from stxsdk.config.configs import Configs


def format_failure_response(
    errors: List[str], message: Optional[str] = None
) -> FailureResponse:
    return FailureResponse(
        success=False, data=None, errors=errors, message=message or "Request Failed"
    )


def format_success_response(
    data: DataType, message: Optional[str] = None
) -> SuccessResponse:
    return SuccessResponse(
        success=True,
        data=data,
        errors=None,
        message=message or "Request Processed Successfully",
    )

def get_latest_graphql_version(env: str):

    url = Configs.BASE_URL.format(host=Configs.ENV_HOSTS.get(env))+"/api_version"
    response = requests.get(url)
    if response.ok:
        version = response.json().get("api_version", "")
        if version:
            version = "v"+version
    else:
        version = Configs.GRAPHQL_VERSION
    return version
