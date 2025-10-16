from datetime import datetime, timedelta

import pytest

from stxsdk.exceptions import AuthenticationFailedException, TokenExpiryException
from stxsdk.services.authentication import AuthService
from stxsdk.storage.user_storage import User
from tests.fixture_data import user, client  # noqa: F401


class TestCheckFor2FA:
    def test_no_session_id_does_not_raise_exception(self):
        user = User()
        user.session_id = None
        user.id = "123"
        AuthService.check_for_2fa(user)

    def test_no_id_does_not_raise_exception(self):
        user = User()
        user.session_id = "abc"
        user.id = None
        AuthService.check_for_2fa(user)

    def test_session_id_and_id_raises_exception(self):
        user = User()
        user.session_id = "abc"
        user.id = "123"

        with pytest.raises(
            AuthenticationFailedException,
            match="Unable to authenticate, Please confirm 2FA.",
        ):
            AuthService.check_for_2fa(user)


class TestCheckForTokenExpiry:
    def test_valid_expiry_does_not_raise_exception(self):
        expiry = datetime.now() + timedelta(minutes=61)
        AuthService.check_for_token_expiry(expiry)

    def test_no_expiry_raise_exception(self):
        with pytest.raises(TokenExpiryException, match="Token is invalid or expired."):
            AuthService.check_for_token_expiry(None)

    def test_expired_expiry_raises_exception(self):
        expiry = datetime.now() - timedelta(minutes=1)

        with pytest.raises(TokenExpiryException, match="Token is invalid or expired."):
            AuthService.check_for_token_expiry(expiry)

    def test_non_datetime_expiry_raises_exception(self):
        expiry = "not a datetime object"

        with pytest.raises(TokenExpiryException, match="Token is invalid or expired."):
            AuthService.check_for_token_expiry(expiry)


class TestSetAuthHeader:
    def test_user_with_token_sets_header(self, user, client):
        user = user()
        user.token = "abc"
        client = client()
        AuthService.set_auth_header(client, user)

        assert client.transport.headers == {"Authorization": "Bearer abc"}

    def test_user_with_no_token_does_not_set_header(self, user, client):
        user = user()
        user.token = None
        client = client()
        AuthService.set_auth_header(client, user)

        assert client.transport.headers is None

    def test_client_with_existing_headers_updates_header(self, user, client):
        user = user()
        user.token = "abc"
        client = client()
        client.transport.headers = {"test": "test_header"}

        AuthService.set_auth_header(client, user)

        assert client.transport.headers == {
            "test": "test_header",
            "Authorization": "Bearer abc",
        }
