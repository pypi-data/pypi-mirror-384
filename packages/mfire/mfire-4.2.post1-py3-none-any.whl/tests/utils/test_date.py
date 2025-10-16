from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.settings.constants import LANGUAGES
from mfire.utils.date import LOCAL_TIMEZONE, Datetime, Timedelta
from tests.functions_test import assert_identically_close

# numpy.random seed
np.random.seed(42)


class TestDatetime:
    def test_init(self):
        dates = [
            Datetime(2021, 4, 17),
            Datetime(year=2021, month=4, day=17),
            Datetime("20210417"),
            Datetime("20210417T000000"),
            Datetime("2021-04-17 00:00:00"),
            Datetime("2021-04-17 00:00:00"),
            Datetime("2021-04-17T00:00:00+00:00"),
            Datetime("2021-04-17T00:00:00Z"),
            Datetime(b"\x07\xe5\x04\x11\x00\x00\x00\x00\x00\x00"),
            Datetime(datetime(2021, 4, 17)),
            Datetime(1618617600.0),
            Datetime("2021-04-17T01:00:00+01:00"),
            Datetime(2021, 4, 17, 1, tzinfo=timezone(timedelta(hours=1))),
            Datetime(
                b"\x07\xe5\x04\x11\x01\x00\x00\x00\x00\x00",
                tzinfo=timezone(timedelta(hours=1)),
            ),
            Datetime(xr.DataArray(datetime(2021, 4, 17))),
        ]
        assert all(isinstance(d, Datetime) for d in dates)
        assert all(d == dates[0] for d in dates)

        with pytest.raises(ValueError, match="Datetime value unknown"):
            Datetime(set())

    def test_properties(self, assert_equals_result):
        d0 = Datetime(2021, 12, 21, 18, 44, 56)
        assert d0.rounded == Datetime(2021, 12, 21, 18)
        assert d0.midnight == Datetime(2021, 12, 21)
        assert str(d0) == "2021-12-21T18:44:56+00:00"
        assert d0.as_datetime == datetime(2021, 12, 21, 18, 44, 56, tzinfo=timezone.utc)
        assert d0.is_synoptic()
        assert d0.calendar_date == Datetime(2021, 12, 21)

        assert_equals_result(
            {
                language: {
                    "weekday_name": d0.weekday_name(language),
                    "month_name": d0.month_name(language),
                    "literal_day": d0.literal_day(language),
                    "moment_name": d0.moment(language).get("name"),
                }
                for language in LANGUAGES
            }
        )

    def test_is_same_day(self):
        d0 = Datetime(2021, 12, 21, 18, 44, 56)
        d1 = Datetime(2021, 12, 22, 18, 44, 56)
        d2 = Datetime(2021, 12, 21, 20, 44, 56)

        assert not d0.is_same_day(d1)
        assert not d1.is_same_day(d2)
        assert d0.is_same_day(d2)

    def test_describe(self, assert_equals_result):
        d0 = Datetime(2021, 12, 21, 18, 44, 56)
        d1 = Datetime(2021, 12, 20, 18)
        d2 = Datetime(2021, 12, 14, 23)
        d3 = Datetime(2021, 12, 22, 1)
        d4 = Datetime(2021, 12, 22, 23)

        assert_equals_result(
            {
                language: [
                    d0.describe_day(d0, language),
                    d0.describe_day(d1, language),
                    d0.describe_day(d2, language),
                    d0.describe_moment(d0, language),
                    d0.describe_moment(d1, language),
                    d0.describe(d0, language),
                    d0.describe(d1, language),
                    d0.describe(d2, language),
                    d2.describe(d1, language),
                    d3.describe(d0, language),
                    d3.describe(d1, language),
                    d3.describe(d3, language),
                    d4.describe(d3, language),
                ]
                for language in LANGUAGES
            }
        )

    def test_timezone(self):
        assert Datetime().tzinfo == timezone.utc
        assert Datetime(2021, 1, 1).tzinfo == timezone.utc
        assert Datetime.now().tzinfo == LOCAL_TIMEZONE
        assert Datetime(2021, 1, 1) == Datetime(2021, 1, 1, tzinfo=timezone.utc)
        d0 = Datetime(2021, 1, 1, 1, tzinfo=timezone(timedelta(hours=1)))
        assert d0 == Datetime(2021, 1, 1)
        assert d0.utc == d0

    def test_xarray_sel(self):
        # tests data arrays
        da0 = xr.DataArray(
            np.arange(24),
            dims="valid_time",
            coords={
                "valid_time": [Datetime(2021, 1, 1, i).as_np_dt64 for i in range(24)]
            },
        )
        vals = [6, 8, 1, 9, 12]
        da1 = da0.isel(valid_time=15)
        da2 = da0.isel(valid_time=vals)
        da3 = da0.isel(valid_time=slice(vals[0], vals[-1]))

        # selection using utc Datetimes
        dt_list = [Datetime(2021, 1, 1, i) for i in vals]
        assert_identically_close(
            da1, da0.sel(valid_time=Datetime(2021, 1, 1, 15).without_tzinfo)
        )
        assert_identically_close(
            da2, da0.sel(valid_time=[dt.as_np_dt64 for dt in dt_list])
        )
        assert_identically_close(
            da3,
            da0.sel(
                valid_time=slice(
                    dt_list[0].without_tzinfo,
                    (dt_list[-1] - Timedelta(hours=1)).without_tzinfo,
                )
            ),
        )
        assert_identically_close(
            da3,
            da0.sel(
                valid_time=slice(
                    dt_list[0].as_np_dt64,
                    (dt_list[-1] - Timedelta(microseconds=1)).as_np_dt64,
                )
            ),
        )  # cas où une borne du slice n'est pas dans l'index : besoin de comparer
        # entre tz-naive et aware si on utilise pas des np_datetime64

        # selection using local Datetimes
        for shift in (4, 1, 2, 6, -1, -2, -8):
            local_delta = timedelta(hours=shift)
            local_tz = timezone(local_delta)
            local_dt_list = [
                Datetime(2021, 1, 1, i, tzinfo=local_tz) + local_delta for i in vals
            ]
            local_dt = Datetime(2021, 1, 1, 15, tzinfo=local_tz) + local_delta
            assert_identically_close(da1, da0.sel(valid_time=local_dt.without_tzinfo))
            assert_identically_close(
                da2, da0.sel(valid_time=[dt.as_np_dt64 for dt in local_dt_list])
            )
            assert_identically_close(
                da3,
                da0.sel(
                    valid_time=slice(
                        local_dt_list[0].without_tzinfo,
                        (local_dt_list[-1] - Timedelta(hours=1)).without_tzinfo,
                    )
                ),
            )
            assert_identically_close(
                da3,
                da0.sel(
                    valid_time=slice(
                        local_dt_list[0].as_np_dt64,
                        (local_dt_list[-1] - Timedelta(microseconds=1)).as_np_dt64,
                    )
                ),
            )  # cas où une borne du slice n'est pas dans l'index : besoin de comparer
            # entre tz-naive et aware si on utilise pas des np_datetime64

    def test_format_bracket_str(self):
        d0 = Datetime(2023, 3, 1, 5)
        assert d0.format_bracket_str("[date+3]") == "2023-03-04T00:00:00+00:00"
        assert d0.format_bracket_str(3) == 3


class TestTimedelta:
    def test_init(self):
        assert isinstance(Timedelta(1, 2, 3), Timedelta)
        assert Timedelta(1) == Timedelta(days=1)
        assert Timedelta(1, 2) == Timedelta(days=1, seconds=2)
        assert Timedelta(1, 2, 3) == Timedelta(days=1, seconds=2, microseconds=3)
        assert isinstance(Timedelta(hours=1), Timedelta)
        assert isinstance(Timedelta(timedelta(days=1)), Timedelta)

        with pytest.raises(ValueError, match="No initial value provided for Timedelta"):
            Timedelta()

    def test_operations(self):
        # Additions
        #   Datetime & Datetime
        assert isinstance(Timedelta(hours=-1) + Datetime(2021, 1, 1), Datetime)
        with pytest.raises(TypeError):
            _ = Datetime(2021, 1, 1, 1) + Datetime(2021, 1, 1)
        #   Datetime & Timedelta
        assert Datetime(2021, 1, 1) + Timedelta(hours=1) == Datetime(2021, 1, 1, 1)
        assert isinstance(Datetime(2021, 1, 1) + Timedelta(hours=1), Datetime)
        assert Datetime(2021, 1, 1) + Timedelta(hours=-1) == Datetime(2020, 12, 31, 23)
        assert isinstance(Datetime(2021, 1, 1) + Timedelta(hours=-1), Datetime)
        assert Timedelta(hours=1) + Datetime(2021, 1, 1) == Datetime(2021, 1, 1, 1)
        assert isinstance(Timedelta(hours=1) + Datetime(2021, 1, 1), Datetime)
        assert Timedelta(hours=-1) + Datetime(2021, 1, 1) == Datetime(2020, 12, 31, 23)
        assert Datetime(2021, 1, 1) + timedelta(hours=1) == Datetime(2021, 1, 1, 1)
        assert isinstance(Datetime(2021, 1, 1) + timedelta(hours=1), Datetime)
        # TO DO : assert datetime(2021,1,1)+Timedelta(hours=1)==Datetime(2021,1,1,1)
        # TO DO : assert isinstance(datetime(2021, 1, 1) + Timedelta(hours=1), Datetime)
        assert timedelta(hours=1) + Datetime(2021, 1, 1) == Datetime(2021, 1, 1, 1)
        assert isinstance(timedelta(hours=1) + Datetime(2021, 1, 1), Datetime)
        # TO DO : assert Timedelta(hours=-1)+datetime(2021,1,1)==Datetime(2020,12,31,23)
        # TO DO :assert isinstance(Timedelta(hours=-1) + datetime(2021, 1, 1), Datetime)
        #   Datetime & {int, float, str}
        with pytest.raises(TypeError):
            _ = Datetime.now() + 1
        with pytest.raises(TypeError):
            _ = Datetime.now() + 3.14
        with pytest.raises(TypeError):
            _ = Datetime.now() + "toto"

        #   Timedelta & Timedelta
        assert Timedelta(hours=1) + Timedelta(days=1) == Timedelta(days=1, hours=1)
        assert isinstance(Timedelta(hours=1) + Timedelta(days=1), Timedelta)
        assert Timedelta(hours=1) + timedelta(hours=1) == Timedelta(hours=2)
        assert isinstance(Timedelta(hours=1) + timedelta(hours=1), Timedelta)
        #   Timedelta & {int, float, str}
        with pytest.raises(TypeError):
            _ = Timedelta(1) + 1
        with pytest.raises(TypeError):
            _ = Timedelta(1) + 3.14
        with pytest.raises(TypeError):
            _ = Timedelta(1) + "toto"

        # subtractions
        #   Datetime & Datetime
        assert Datetime(2021, 1, 1, 1) - Datetime(2021, 1, 1) == Timedelta(hours=1)
        assert isinstance(Datetime(2021, 1, 1, 1) - Datetime(2021, 1, 1), Timedelta)
        assert Datetime(2021, 1, 1) - Datetime(2021, 1, 1, 1) == Timedelta(hours=-1)
        assert isinstance(Datetime(2021, 1, 1) - Datetime(2021, 1, 1, 1), Timedelta)
        with pytest.raises(TypeError):
            _ = Datetime(2021, 1, 1, 1) - datetime(2021, 1, 1)
        with pytest.raises(TypeError):
            _ = datetime(2021, 1, 1) - Datetime(2021, 1, 1, 1) == Timedelta(hours=-1)
        #   Datetime & Timedelta
        assert Datetime(2021, 1, 1, 1) - Timedelta(hours=1) == Datetime(2021, 1, 1)
        assert isinstance(Datetime(2021, 1, 1, 1) - Timedelta(hours=1), Datetime)
        assert Datetime(2021, 1, 1, 1) - timedelta(hours=1) == Datetime(2021, 1, 1)
        assert isinstance(Datetime(2021, 1, 1, 1) - timedelta(hours=1), Datetime)
        # TO DO : assert datetime(2021,1,1,1)-Timedelta(hours=1)==Datetime(2021,1,1)
        # TO DO : assert isinstance(datetime(2021,1,1,1)-Timedelta(hours=1),Datetime)
        assert Datetime(2021, 1, 1) - Timedelta(hours=-1) == Datetime(2021, 1, 1, 1)
        with pytest.raises(TypeError):
            _ = Timedelta(1) - Datetime.now()
        #   Datetime & {int, float, str}
        with pytest.raises(TypeError):
            _ = Datetime.now() - 1
        with pytest.raises(TypeError):
            _ = Datetime.now() - 3.14
        with pytest.raises(TypeError):
            _ = Datetime.now() - "toto"
        #   Timedelta & Timedelta
        assert Timedelta(-1) == -Timedelta(1)
        assert isinstance(-Timedelta(1), Timedelta)
        assert Timedelta(1) - Timedelta(hours=1) == Timedelta(hours=23)
        assert isinstance(Timedelta(1) - Timedelta(hours=1), Timedelta)
        assert Timedelta(hours=1) - Timedelta(1) == Timedelta(hours=-23)
        assert isinstance(Timedelta(hours=1) - Timedelta(1), Timedelta)
        assert Timedelta(1) - timedelta(hours=1) == Timedelta(hours=23)
        assert isinstance(Timedelta(1) - timedelta(hours=1), Timedelta)
        assert timedelta(1) - Timedelta(hours=1) == Timedelta(hours=23)
        assert isinstance(timedelta(1) - Timedelta(hours=1), Timedelta)
        #   Timedelta & {int, float, str}
        with pytest.raises(TypeError):
            _ = Timedelta(1) - 1
        with pytest.raises(TypeError):
            _ = Timedelta(1) - 3.14
        with pytest.raises(TypeError):
            _ = Timedelta(1) - "toto"

        # Multiplications
        #   Timedelta & {int, float}
        assert 42 * Timedelta(1) == Timedelta(42) == Timedelta(1) * 42
        assert (
            3.14 * Timedelta(1) == Timedelta(3.14) == Timedelta(days=3, seconds=12096)
        )
        assert (
            Timedelta(1) * 3.14 == Timedelta(3.14) == Timedelta(days=3, seconds=12096)
        )
        assert isinstance(42 * Timedelta(1), Timedelta)
        assert isinstance(3.14 * Timedelta(1), Timedelta)
        assert isinstance(Timedelta(1) * 42, Timedelta)
        assert isinstance(Timedelta(1) * 3.14, Timedelta)
