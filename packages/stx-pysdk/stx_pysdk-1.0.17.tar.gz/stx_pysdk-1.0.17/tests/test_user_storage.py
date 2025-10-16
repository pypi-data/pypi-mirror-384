from datetime import datetime
from tests.fixture_data import user  # noqa: F401


class TestUser:
    def test_only_one_instance_created(self, user):
        instance1 = user()
        instance2 = user()

        assert instance1 is instance2

    def test_set_params(self, user):
        attributes = {
            "id": "123",
            "uid": "456",
            "session_id": "789",
            "token": "abc",
            "refresh_token": "zxc",
            "expiry": datetime.now(),
            "email": "test@example.com",
        }
        instance = user()
        instance.set_params(attributes)

        assert instance.id == "123"
        assert instance.uid == "456"
        assert instance.session_id == "789"
        assert instance.token == "abc"
        assert instance.refresh_token == "zxc"
        assert instance.email == "test@example.com"
