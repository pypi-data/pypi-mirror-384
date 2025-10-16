from stxsdk.storage.singleton import SingletonMeta


class TestSingletonMeta:
    def test_only_one_instance_created(self):
        class TestClass(metaclass=SingletonMeta):
            pass

        instance1 = TestClass()
        instance2 = TestClass()

        assert instance1 is instance2

    def test_different_classes_have_different_instances(self):
        class TestClass1(metaclass=SingletonMeta):
            pass

        class TestClass2(metaclass=SingletonMeta):
            pass

        instance1 = TestClass1()
        instance2 = TestClass2()

        assert instance1 is not instance2

    def test_instance_created_with_arguments(self):
        class TestClass(metaclass=SingletonMeta):
            def __init__(self, value=None):
                self.value = value

        instance1 = TestClass(1)
        instance2 = TestClass()

        assert instance1.value == 1
        assert instance2.value == 1

        # now change value of instance1, instance2's value should change
        instance1.value = 10

        assert instance1.value == 10
        assert instance2.value == 10
