import pytest

import mfire.utils.mfxarray as xr
from mfire.settings.constants import LANGUAGES
from mfire.utils.wwmf import Wwmf
from tests.functions_test import assert_identically_close


class TestWwmf:
    @pytest.mark.parametrize(
        "wwmf,expected",
        [
            (49, True),
            (59, True),
            (98, True),
            (0, False),
            (50, False),
            (xr.DataArray([85, 99, 60]), xr.DataArray([True, True, False])),
        ],
    )
    def test_is_severe(self, wwmf, expected):
        assert_identically_close(Wwmf.is_severe(wwmf), expected)

    @pytest.mark.parametrize(
        "wwmf,expected",
        [
            (30, True),
            (50, False),
            (xr.DataArray([31, 40]), xr.DataArray([True, False])),
        ],
    )
    def test_is_visibility(self, wwmf, expected):
        assert_identically_close(Wwmf.is_visibility(wwmf), expected)

    @pytest.mark.parametrize(
        "wwmf,expected",
        [
            (40, True),
            (30, False),
            (xr.DataArray([41, 31]), xr.DataArray([True, False])),
        ],
    )
    def test_is_precipitation(self, wwmf, expected):
        assert_identically_close(Wwmf.is_precipitation(wwmf), expected)

    @pytest.mark.parametrize(
        "wwmf,expected",
        [
            (58, True),
            (60, True),
            (61, True),
            (62, True),
            (63, True),
            (77, True),
            (49, False),
            (70, False),
            (
                xr.DataArray([78, 80, 81, 82, 83, 90]),
                xr.DataArray([True, True, True, True, True, False]),
            ),
        ],
    )
    def test_is_snow(self, wwmf, expected):
        assert_identically_close(Wwmf.is_snow(wwmf), expected)

    @pytest.mark.parametrize(
        "wwmf,expected",
        [
            (40, True),
            (49, True),
            (50, True),
            (51, True),
            (53, True),
            (58, True),
            (59, True),
            (70, True),
            (71, True),
            (73, True),
            (78, True),
            (93, True),
            (60, False),
            (90, False),
            (xr.DataArray([52, 72, 77, 80]), xr.DataArray([True, True, True, False])),
        ],
    )
    def test_is_rain(self, wwmf, expected):
        assert_identically_close(Wwmf.is_rain(wwmf), expected)

    @pytest.mark.parametrize(
        "wwmf,expected",
        [
            (70, True),
            (71, True),
            (72, True),
            (73, True),
            (78, True),
            (80, True),
            (81, True),
            (83, True),
            (84, True),
            (85, True),
            (60, False),
            (xr.DataArray([77, 82, 92, 90]), xr.DataArray([True, True, True, False])),
        ],
    )
    def test_is_shower(self, wwmf, expected):
        assert_identically_close(Wwmf.is_shower(wwmf), expected)

    @pytest.mark.parametrize(
        "wwmf,expected",
        [
            (84, True),
            (90, True),
            (91, True),
            (92, True),
            (97, True),
            (98, True),
            (60, False),
            (80, False),
            (xr.DataArray([85, 93, 99, 70]), xr.DataArray([True, True, True, False])),
        ],
    )
    def test_is_thunderstorm(self, wwmf, expected):
        assert_identically_close(Wwmf.is_thunderstorm(wwmf), expected)

    @pytest.mark.parametrize(
        "wwmf,expected",
        [
            (49, True),
            (59, True),
            (60, False),
            (xr.DataArray([49, 59, 70]), xr.DataArray([True, True, False])),
        ],
    )
    def test_is_ice(self, wwmf, expected):
        assert_identically_close(Wwmf.is_ice(wwmf), expected)

    @pytest.mark.parametrize(
        "wwmf,concatenate",
        [
            # Tests of concatenation
            ([32, 50], True),
            ([32, 50], False),
            # Basic tests
            ([70], True),
            ([51, 52], True),
            # Lot of WWMF codes
            ([51, 61, 71, 81, 91], True),
        ],
    )
    def test_label(self, wwmf, concatenate, assert_equals_result):
        assert_equals_result(
            {
                language: Wwmf(language=language).label(*wwmf, concatenate=concatenate)
                for language in LANGUAGES
            }
        )

    def test_families(self):
        assert Wwmf.families() == set()
        assert Wwmf.families(30, 85, 78) == {
            Wwmf.Family.VISIBILITY,
            Wwmf.Family.SHOWER,
            Wwmf.Family.SNOW,
            Wwmf.Family.THUNDERSTORM,
            Wwmf.Family.RAIN,
        }
        assert Wwmf.families(Wwmf.Subgrp.A1) == {Wwmf.Family.RAIN}
        assert Wwmf.families(Wwmf.Subgrp.A1, 98) == {
            Wwmf.Family.RAIN,
            Wwmf.Family.THUNDERSTORM,
        }


class TestWwmfSubgrp:
    def test_get_b_wwmf(self):
        assert Wwmf.Subgrp.get_b_wwmf() == [49, 59, 84, 85, 98, 99]
