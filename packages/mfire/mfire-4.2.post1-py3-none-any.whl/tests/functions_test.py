from typing import Any

import numpy as np
import xarray as xr

from mfire.utils.mfxarray import DataArray


def assert_identically_close(a: Any, b: Any):
    assert isinstance(a, type(b))
    if a is None:
        assert b is None
    elif isinstance(a, (list, tuple)):
        for a_elem, b_elem in zip(a, b):
            assert_identically_close(a_elem, b_elem)
    elif isinstance(a, (xr.Dataset, DataArray)):
        if isinstance(a, DataArray):
            assert a.shape == b.shape
        xr.testing.assert_allclose(a, b)
        assert a.attrs == b.attrs
        for coord in a.coords:
            assert a[coord].attrs == b[coord].attrs

        if isinstance(a, xr.DataArray):
            assert a.name == b.name, f"Name are different: {a.name} != {b.name}"
    elif isinstance(a, np.ndarray):
        np.testing.assert_allclose(a, b)
    elif isinstance(a, float):
        if not np.isnan(a):
            np.testing.assert_allclose(a, b)
        else:
            assert np.isnan(b)
    else:
        assert a == b
