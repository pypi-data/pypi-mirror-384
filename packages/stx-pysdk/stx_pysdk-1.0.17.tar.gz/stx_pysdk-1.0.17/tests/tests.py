from stxsdk.services.base import StxClient
from tests.fixture_data import (
    login_return_fields,
    update_profile_return_fields,
    cancel_order_return_fields,
    confirm_order_return_fields,
    new_token_return_fields,
    market_infos_return_fields,
    user_profile_return_fields,
    geo_fencing_return_fields,
)

client = StxClient()


class TestStxClientUtilities:
    def test_login_get_return_fields(self):
        fields = client.get_return_fields("login")
        assert fields == login_return_fields

    def test_updateProfile_get_return_fields(self):
        fields = client.get_return_fields("updateProfile")
        assert fields == update_profile_return_fields

    def test_cancelOrder_get_return_fields(self):
        fields = client.get_return_fields("cancelOrder")
        assert fields == cancel_order_return_fields

    def test_confirmOrder_get_return_fields(self):
        fields = client.get_return_fields("confirmOrder")
        assert fields == confirm_order_return_fields

    def test_newToken_get_return_fields(self):
        fields = client.get_return_fields("newToken")
        assert fields == new_token_return_fields

    def test_marketInfos_get_return_fields(self):
        fields = client.get_return_fields("marketInfos")
        assert fields == market_infos_return_fields

    def test_userProfile_get_return_fields(self):
        fields = client.get_return_fields("userProfile")
        assert fields == user_profile_return_fields

    def test_geoFencingLicense_get_return_fields(self):
        fields = client.get_return_fields("geoFencingLicense")
        assert fields == geo_fencing_return_fields
