from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from shapely import box

from mfire.utils.json import JsonFile
from tests.composite.factories import PeriodCompositeFactory


class TestJsonFile:
    content = {
        "a": PeriodCompositeFactory(),
        "b": datetime(2023, 3, 1),
        "c": slice(2, 4, 1),
        "d": np.ndarray((1,), buffer=np.array([1])),
        "e": Path("test"),
        "f": 2.4,
        "g": box(-1, -1, 2, 2),
        "h": pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]}),
    }

    def test_loads(self, test_file):
        assert JsonFile.loads('{"a":1, "b":2}') == {"a": 1, "b": 2}

    @pytest.mark.parametrize(
        "test_file", [{"extension": "json", "content": '{"a":1, "b":2}'}], indirect=True
    )
    def test_load(self, test_file):
        with open(test_file, "r") as f:
            json = JsonFile(f)
            assert json.load() == {"a": 1, "b": 2}

        json = JsonFile(test_file)
        assert json.load() == {"a": 1, "b": 2}

    def test_dumps(self):
        assert JsonFile.dumps({"a": 1, "b": 2}) == '{\n"a": 1,\n"b": 2\n}'

    @pytest.mark.parametrize("test_file", [{"extension": "json"}], indirect=True)
    def test_dump_with_filename(self, test_file, assert_equals_file):
        json = JsonFile(test_file)
        json.dump(self.content)

        assert_equals_file(test_file)

        # Try with a non-Json serializable object
        content = {"a": self}
        with pytest.raises(
            TypeError, match="Object of type TestJsonFile is not JSON serializable"
        ):
            json.dump(content)

    @pytest.mark.parametrize("test_file", [{"extension": "json"}], indirect=True)
    def test_dump_with_file(self, test_file, assert_equals_file):
        with open(test_file, "w") as f:
            json = JsonFile(f)
            json.dump(self.content)
            f.close()

            assert_equals_file(test_file)

        # Try with a non-Json serializable object
        content = {"a": self}
        with pytest.raises(
            TypeError, match="Object of type TestJsonFile is not JSON serializable"
        ):
            json.dump(content)

    @pytest.mark.parametrize(
        "test_file", [{"nbr": 3, "extension": "json"}], indirect=True
    )
    def test_is_equal_to(self, test_file):
        json1 = JsonFile(test_file[0])
        json2 = JsonFile(test_file[1])

        json1.dump({"a": 1, "b": 2})
        json2.dump({"b": 2, "a": 1})
        assert json1 == json2

        json3 = JsonFile(test_file[2])
        json3.dump({"a": 1, "b": 3})
        assert json1 != json3
