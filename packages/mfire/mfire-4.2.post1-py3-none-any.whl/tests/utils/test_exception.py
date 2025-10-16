from mfire.utils.exception import PrometheeError


class _ErrorClassFactory:
    def __str__(self):
        raise ValueError()


class TestPrometheeError:
    def test_init(self):
        error = PrometheeError("following error:", a=2)
        assert str(error) == "following error: a=2."

        error = PrometheeError("following error:", a=_ErrorClassFactory(), b=None)
        assert str(error) == "following error:"
