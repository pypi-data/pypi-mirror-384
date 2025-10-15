import pytest


class TestDummy:
    def setup_class(self):
        self.x = 1  # pylint: disable=W0201
        self.y = 2  # pylint: disable=W0201

    def test_pass(self):
        if self.x != self.y:
            pytest.xfail("Known issue: x is not equal to y")
        assert True

    @pytest.mark.xfail(reason="Known issue: x is not equal to y")
    def test_pass2(self):
        assert self.x == self.y


print("test_dummy_regular.py")
