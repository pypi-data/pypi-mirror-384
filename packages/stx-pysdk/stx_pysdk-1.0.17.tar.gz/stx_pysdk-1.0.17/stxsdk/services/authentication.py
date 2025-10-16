import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Optional

from gql.dsl import DSLMutation, dsl_gql

from stxsdk.config.configs import Configs
from stxsdk.enums import RootType
from stxsdk.exceptions import AuthenticationFailedException, TokenExpiryException
from stxsdk.services.selection import Selection
from stxsdk.storage.user_storage import User
from stxsdk.utils import format_failure_response, format_success_response


class AuthService:
    @staticmethod
    def check_for_2fa(user: User) -> None:
        """
        A user can have session_id only when 2fa is required otherwise it will be None
        If the user has a session_id and an id, then raise an exception
        :parameter user: The user object that is being authenticated
        :return: None
        """
        if user.session_id and user.id:
            raise AuthenticationFailedException(
                "Unable to authenticate, Please confirm 2FA."
            )

    @staticmethod
    def check_for_token_expiry(expiry: Optional[datetime]) -> None:
        """
        Checking if the user token is valid or expired. token expiry time is 60 minutes
        :parameter expiry: datetime object
        :return: None
        """
        if not isinstance(expiry, datetime) or expiry <= datetime.now():
            raise TokenExpiryException("Token is invalid or expired.")

    @staticmethod
    def set_auth_header(client, user: User) -> None:
        """
        Set the Authorization header for the client.
        If the headers attribute of the client.transport object is empty or None,
            it sets the Authorization header to the value of auth_header.
        If the headers attribute of the client.transport object contains the Authorization header,
            it replaces the old one.
        If the headers attribute of the client.transport object does not contain the Authorization header,
            it sets the Authorization header to the value of auth_header.
        :parameter client: The client to set the Authorization header for.
        :parameter user: The user to set the Authorization header for.
        :returns None
        """
        if user.token:
            auth_header = {"Authorization": f"Bearer {user.token}"}
            if not client.transport.headers:
                client.transport.headers = auth_header
            else:
                client.transport.headers.update(**auth_header)

    @staticmethod
    def refresh_token(proxy_call):
        """
        It refreshes the user auth token using refresh_token, if the refresh_token
        is also expired then closes the connection with Auth failure exception.
        :parameter proxy_call: Proxy Call object with related method
        :returns None
        """
        try:
            # get the refresh token method from schema
            refresh_token_method = getattr(
                getattr(proxy_call.schema, RootType.MUTATION.value),
                Configs.REFRESH_TOKEN_API,
            )
            # generate request with stored refresh token
            request = refresh_token_method(
                **{"refreshToken": proxy_call.user.refresh_token}
            )
            # set return values
            request = request.select(
                *[
                    proxy_call.schema.LoginResult.token,
                    proxy_call.schema.LoginResult.refreshToken,
                    proxy_call.schema.LoginResult.currentLoginAt,
                ],
            )
            document = dsl_gql(DSLMutation(request))
            response = proxy_call.client.execute(document)
            tokens = response[Configs.REFRESH_TOKEN_API]
            # set the new token and refresh token to the user object with expiry of 59 mins
            params = {
                "token": tokens["token"],
                "refresh_token": tokens["refreshToken"],
                # token expiry time is 60 minutes, setting it to 59 minutes for failsafe
                "expiry": datetime.now() + timedelta(minutes=59),
            }
            proxy_call.user.set_params(params)
        except Exception as exc:
            # on refresh token failure, resetting user attributes to None
            proxy_call.user.clear()
            raise AuthenticationFailedException(
                "Refresh token is expired/invalid, please login."
            ) from exc

    @staticmethod
    def format_login_params(
        params: Dict[str, Optional[str]]
    ) -> Dict[str, Dict[str, Optional[str]]]:
        return {
            "credentials": {
                "email": params.get("email") or os.getenv("EMAIL"),
                "password": params.get("password") or os.getenv("PASSWORD"),
            }
        }

    @staticmethod
    def format_confirm2fa_params(
        params: Dict[str, Optional[str]], user: User
    ) -> Dict[str, Optional[str]]:
        return {
            "code": params.get("code"),
            "email": user.email,
            "sessionId": user.session_id,
        }

    @staticmethod
    def extract_email(params):
        return params.get("credentials", {}).get("email", params.get("email", None))

    @classmethod
    def execute_auth_api(cls, method, proxy_call, **kwargs):
        """
        It wraps the logic for handling different types of exceptions in a try-except block.
        If an exception is caught, it raises an AuthenticationFailedException with the appropriate error message.
        If no exception is caught, it sets the params dictionary and the message variable
        based on the login flow if its 2FA or simple authentication
        :param method: requested operation
        :param proxy_call: client object
        :param kwargs: method passed parameters
        :return:
        """
        kwargs["selections"] = Selection(
            "userId",
            "userUid",
            "sessionId",
            "token",
            "refreshToken",
            "promptTwoFactorAuth",
        )
        user = proxy_call.user
        # Store the params for each authentication method in a dict
        auth_method_params = {
            Configs.LOGIN_API: cls.format_login_params(kwargs["params"]),
            Configs.CONFIRM_2FA: cls.format_confirm2fa_params(kwargs["params"], user),
        }
        user = proxy_call.user
        if proxy_call.method.name == Configs.LOGIN_API:
            user.clear()
        elif proxy_call.method.name == Configs.CONFIRM_2FA:
            # checking if the user has no session id set and requested for confirm2fa
            if not user.session_id and not user.email:
                raise AuthenticationFailedException(
                    "",
                    errors=[
                        {"message": "No session id or email found. Please login first."}
                    ],
                )

        # Set the params for the current authentication method
        kwargs["params"] = auth_method_params.get(proxy_call.method.name, {})

        try:
            # execute the authentication API
            response = method(proxy_call, **kwargs)
        except Exception as exc:
            error_msg = exc.errors[0]["message"] if hasattr(exc, "errors") else str(exc)
            raise AuthenticationFailedException(error_msg) from exc

        if not response["success"]:
            raise AuthenticationFailedException(response["message"], response["errors"])

        data = response["data"][proxy_call.method.name]
        # checks if the user has 2FA enabled, then set session id and return prompt message
        # informing to execute confirm2fa request with the received code
        if data["promptTwoFactorAuth"]:
            params = {
                "id": data["userId"],
                "session_id": data["sessionId"],
                "email": cls.extract_email(kwargs["params"]),
            }
            message = (
                "2-Factor Authentication Required, "
                "you'll receive code via email, pass that code in confirm2Fa to complete authentication."
            )
        else:
            # if user has no 2fa enabled then set the returned token data
            params = {
                "id": data["userId"],
                "uid": data["userUid"],
                "token": data["token"],
                "refresh_token": data["refreshToken"],
                # token expiry time is 60 minutes, setting it to 59 minutes for failsafe
                "expiry": datetime.now() + timedelta(minutes=59),
                "session_id": None,
                "email": cls.extract_email(kwargs["params"]),
            }
            message = "Login Successful"
        proxy_call.user.set_params(params)
        return format_success_response(data=None, message=message)

    @classmethod
    def authenticate(cls, method):
        """
        This method is responsible for the authentication of the API before executing any operation
        It first tries to execute the checks for the 2-factor authentication and the token expiry.
        If any of these checks fail, it handles the exception and returns the appropriate response.
        If the checks for 2-factor authentication and token expiry pass, it sets the Authorization header
        and then executes the method or the execute_auth_api method depending on whether the requested method
        is an authentication method or not.
        :param method: requested method
        :return: return wrapped method after authentication
        """

        @wraps(method)
        def wrapper(proxy_call, **kwargs):  # pylint: disable=R1710
            user = proxy_call.user
            try:
                # check if the requested method is auth method [login, confirm2fa]
                if proxy_call.method.name not in [
                    Configs.LOGIN_API,
                    Configs.CONFIRM_2FA,
                    Configs.REGISTER_API
                ]:
                    # check if the user has 2 fa enabled and verified the login with 2fa
                    # without 2fa confirmation no token can be available
                    cls.check_for_2fa(user)
                    # check for token expiry and raises exception if the current token is expired
                    cls.check_for_token_expiry(user.expiry)
            except TokenExpiryException:
                # in case of expired token, refreshes the token
                if user.refresh_token and isinstance(user.refresh_token, str):
                    cls.refresh_token(proxy_call)
                else:
                    return format_failure_response(
                        errors=[], message="Unable to authenticate, Please login again."
                    )
            except AuthenticationFailedException as exc:
                return format_failure_response(errors=exc.errors, message=exc.message)
            except Exception as exc:
                return format_failure_response(errors=[], message=str(exc))

            # set the token in the header as Bearer token
            # format: Authentication: Bearer <token>
            cls.set_auth_header(proxy_call.client, user)

            # if the requested method is of auth api don't check for any validation
            # and calls the API
            try:
                return (
                    cls.execute_auth_api(method, proxy_call, **kwargs)
                    if proxy_call.method.name
                    in [Configs.LOGIN_API, Configs.CONFIRM_2FA]
                    else method(proxy_call, **kwargs)
                )
            except AuthenticationFailedException as exc:
                return format_failure_response(errors=exc.errors, message=exc.message)

        return wrapper
