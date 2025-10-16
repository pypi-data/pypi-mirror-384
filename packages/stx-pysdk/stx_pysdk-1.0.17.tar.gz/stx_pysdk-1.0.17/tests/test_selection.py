from tests.fixture_data import selection  # noqa: F401


class TestSelection:
    def test_args_saved_to_values(self, selection):
        s = selection(1, 2, 3)
        assert s.values == (1, 2, 3)

    def test_kwargs_saved_to_nested_values(self, selection):
        s = selection(key1=1, key2=2, key3=3)
        assert s.nested_values == {"key1": 1, "key2": 2, "key3": 3}

    def test_args_and_kwargs_saved_correctly(self, selection):
        s = selection(1, 2, 3, key1=1, key2=2, key3=3)
        assert s.values == (1, 2, 3)
        assert s.nested_values == {"key1": 1, "key2": 2, "key3": 3}
