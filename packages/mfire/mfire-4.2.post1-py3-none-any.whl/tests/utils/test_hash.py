import pytest

from mfire.utils import MD5


class TestMD5:
    def test_obj_with_string(self):
        md5 = MD5("test")
        assert md5.obj == b"test"

    @pytest.mark.parametrize("test_file", [{"content": "test"}], indirect=True)
    def test_obj_with_file(self, test_file):
        md5 = MD5(test_file)
        assert md5.obj == b"test"

    @pytest.mark.parametrize("test_file", [{"content": "test"}], indirect=True)
    def test_hash(self, test_file, assert_equals_result):
        md5 = MD5(test_file)
        assert_equals_result(md5.hash)
