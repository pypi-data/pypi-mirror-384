import copy
from typing import Callable
from unittest.mock import patch

import numpy as np
import pytest

from mfire.text.synthesis.wind_reducers.gust_summary_builder import GustSummaryBuilder
from mfire.utils.date import Datetime
from tests.text.utils import generate_valid_time

from .factories import (
    CompositeFactory1x1,
    CompositeFactory1x2,
    CompositeFactory1x7,
    CompositeFactory2x2,
    CompositeFactory3x2,
    CompositeFactory5x2,
)

COMPLEX_CASES_WITHOUT_RG_MAX_PARAMS: list = [
    # Case 1:
    # gust_max_raw = 99.0
    # The Q90 is computed from [60, 70, 75, 98, 99] => Q90 = 98.6
    # => gust_max = 100.0
    # gust_max_da = [[11, 20], [30, 40], [50, 60], [70, 75], [98, 99]]
    # I_0 = [80, 100] contains 2/10 = 20% of data_max_da points => OK
    # Q90 >= 80 for the terms 0 and
    (
        generate_valid_time(periods=4),
        [
            [[10.0, 20.0], [30.0, 40.0], [50.0, 60.0], [70.0, 75.0], [90.0, 99.0]],
            [[10.0, 20.0], [30.0, 40.0], [50.0, 60.0], [70.0, 75.0], [20.0, 31.0]],
            [[11.0, 12.0], [13.0, 14.0], [15.0, 16.0], [17.0, 74.0], [98.0, 90.0]],
            [[10.0, 20.0], [30.0, 40.0], [50.0, 60.0], [61.0, 62.0], [63.0, 64.0]],
        ],
    ),
    # Case 2:
    # gust_max_raw = 99.0
    # The Q90 is computed from [51, 60, 76, 77, 89, 109] => Q90 = 99.0
    # => gust_max = 100.0
    # gust_max_da = [[10, 20], [30, 40], [51, 60], [76, 77], [89, 109]]
    # I_0 = [80, 100] contains 1/10 = 10% of data_max_da points => NOK
    # I_1 = [70, 90] contains raf_max and 3/10 = 30% of data_max_da points => OK
    # Q90 >= 70 for the 2first term
    (
        generate_valid_time(periods=4),
        [
            [[10.0, 20.0], [30.0, 40.0], [50.0, 60.0], [70.0, 75.0], [71.0, 109.0]],
            [[10.0, 20.0], [30.0, 40.0], [50.0, 60.0], [76.0, 77.0], [89.0, 79.0]],
            [[1.0, 2.0], [3.0, 4.0], [51.0, 6.0], [1.0, 0.0], [2.0, 70.0]],
            [[10.0, 20.0], [30.0, 40.0], [50.0, 60.0], [61.0, 62.0], [63.0, 64.0]],
        ],
    ),
    # Case 2:
    # gust_max_raw = 120.0
    # The Q90 is computed from [51, 55, 56, 59, 71, 120] => Q90 = 95.5
    # => gust_max = 100.0
    # gust_max_da = [[10, 20], [30, 40], [51, 55], [56, 59], [71, 128]]
    # I_0 = [80, 100] contains 0/10 = 0% of data_max_da points => NOK
    # I_1 = [70, 90] contains 1/10 = 10% of data_max_da points => NOK
    # I_2 = [60, 80] contains 1/10 = 10% of data_max_da points => NOK
    # I_3 = [50, 70] contains 6/10 = 60% of data_max_da points => OK
    # Q90 >= 50 for all terms 3
    (
        generate_valid_time(periods=4),
        [
            [[10.0, 20.0], [30.0, 40.0], [51.0, 55.0], [56.0, 59.0], [66.0, 120.0]],
            [[10.0, 20.0], [30.0, 40.0], [51.0, 52.0], [53.0, 54.0], [71.0, 58.0]],
            [[1.0, 2.0], [3.0, 4.0], [51.0, 6.0], [1.0, 0.0], [2.0, 45.0]],
            [[10.0, 20.0], [30.0, 40.0], [51.0, 51.0], [52.0, 51.0], [56.0, 64.0]],
        ],
    ),
    # Case 3:
    # gust_max_raw = 99.0
    # The Q90 is computed from [99] => Q90 = 99.0
    # => gust_max = 100.0
    # [80, 100] contains 1/10 = 20% of data_max_da points => NOK
    # [70, 90] contains 0/10 = 20% of data_max_da points => NOK
    # [60, 80] contains 0/10 = 20% of data_max_da points => NOK
    # [50, 70] contains 0/10 = 40% of data_max_da points => NOK
    # => no interval found
    # Q90 >= 50 for the 2 first terms
    (
        generate_valid_time(periods=4),
        [
            [[10.0, 20.0], [30.0, 40.0], [41.0, 45.0], [46.0, 49.0], [46.0, 99.0]],
            [[10.0, 20.0], [30.0, 40.0], [41.0, 42.0], [43.0, 44.0], [41.0, 58.0]],
            [[1.0, 2.0], [3.0, 4.0], [41.0, 6.0], [1.0, 0.0], [2.0, 45.0]],
            [[10.0, 20.0], [30.0, 40.0], [41.0, 31.0], [22.0, 21.0], [26.0, 24.0]],
        ],
    ),
    # Case 2:
    # gust_max_raw = 70.0
    # The Q90 is computed from [51, 55, 56, 59, 71, 72] => Q90 = 71.5
    # => gust_max = 70.0
    # gust_max_da = [[10, 20], [30, 40], [51, 55], [56, 59], [71, 72]]
    # I_0 = [50, 70] contains 6/10 = 60% of data_max_da points => NOK
    (
        generate_valid_time(periods=4),
        [
            [[10.0, 20.0], [30.0, 40.0], [51.0, 55.0], [56.0, 59.0], [66.0, 72.0]],
            [[10.0, 20.0], [30.0, 40.0], [51.0, 52.0], [53.0, 54.0], [71.0, 58.0]],
            [[1.0, 2.0], [3.0, 4.0], [51.0, 6.0], [1.0, 0.0], [2.0, 45.0]],
            [[10.0, 20.0], [30.0, 40.0], [51.0, 51.0], [52.0, 51.0], [56.0, 64.0]],
        ],
    ),
]

CASE_WITH_RG_MAX_PARAMS: list = [
    # -----------------------------------------------------------
    # rg_max is None and no separation between plain and mountain
    # -----------------------------------------------------------
    # Q90 of points > 50 is 0 -> sg_max = 0 -> cas 0
    ([[50] * 3] * 2, None, False),
    # rg_max is None
    # Q90 of points > 50 is 80 -> sg_max = 80 > 50
    # [60, 80] contains 3/6 = 50% of data_max_da points -> OK
    # -> case 1
    ([[80] * 3, [41] * 3], None, False),
    # rg_max is None
    # Q90 of points > 50 is 93.8 -> sg_max = 90 > 50
    # [70, 90] contains 0/6 = 0 % of data_max_da points -> NOK
    # [60, 80] contains 1/6 = 16.7 % of data_max_da points -> NOK
    # [50, 70] contains 2/6 = 33.3 % of data_max_da points -> OK
    # -> case 2
    ([[100, 69, 51], [41] * 3], None, False),
    # rg_max is None
    # Q90 of points > 50 is 90 -> sg_max = 70 > 50
    # [50, 70] contains 1/6 = 16.7 % of data_max_da points -> NOK
    # -> case 3
    ([[70, 30, 30], [40] * 3], None, False),
    # ------------------------------------------------------------
    # rg_max = sg_max and no separation between plain and mountain
    # ------------------------------------------------------------
    # Q90 of points > 50 is 80 -> sg_max = 80 > 50
    # [60, 80] contains 3/6 = 50% of data_max_da points -> OK
    # rg_max = sg_max = 80
    # -> case 1
    ([[80] * 3, [41] * 3], 80, False),
    # Q90 of points > 50 is 93.8 -> sg_max = 90 > 50
    # [70, 90] contains 0/6 = 0 % of data_max_da points -> NOK
    # [60, 80] contains 1/6 = 16.7 % of data_max_da points -> NOK
    # [50, 70] contains 2/6 = 33.3 % of data_max_da points -> OK
    # rg_max = sg_max = 90
    # -> case 2
    ([[100, 69, 51], [41] * 3], 90, False),
    # Q90 of points > 50 is 70 -> sg_max = 70 > 50
    # [50, 70] contains 1/6 = 16.7 % of data_max_da points -> NOK
    # rg_max = sg_max = 70
    # -> case 3
    ([[70, 30, 30], [40] * 3], 70, False),
    # --------------------------------------------------------------
    # sg_max <= 50 km/h and no separation between plain and mountain
    # --------------------------------------------------------------
    # Q90 of points > 50 is 0 -> sg_max = 0
    # rg_max = 50 <= 50
    # -> case 0
    ([[50] * 3] * 2, 50, False),
    # Q90 of points > 50 is 0 -> sg_max = 0
    # rg_max = 60 > 50 -> case 0_r
    ([[50] * 3] * 2, 60, False),
    # ---------------------------------------------------------------------
    # sg_max > 50 km/h, rg_max < sg_max and no separation between plain and
    # mountain
    # ---------------------------------------------------------------------
    # Q90 of points > 50 is 80 -> sg_max = 80 > 50
    # [60, 80] contains 3/6 = 50% of data_max_da points -> OK -> sg_case = 1
    # rg_max = 70 < sg_max
    # -> case 1
    ([[80] * 3, [41] * 3], 70, False),
    # Q90 of points > 50 is 93.8 -> sg_max = 90 > 50
    # [70, 90] contains 0/6 = 0 % of data_max_da points -> NOK
    # [60, 80] contains 1/6 = 16.7 % of data_max_da points -> NOK
    # [50, 70] contains 2/6 = 33.3 % of data_max_da points -> OK -> sg_case = 2
    # rg_max = 70 < sg_max
    # -> case 2
    ([[100, 69, 51], [41] * 3], 70, False),
    # Q90 of points > 50 is 90 -> sg_max = 70 > 50
    # [50, 70] contains 1/6 = 16.7 % of data_max_da points -> NOK -> sg_case = 3
    # rg_max = 40 < sg_max
    # -> case 3
    ([[70, 30, 30], [40] * 3], 40, False),
    # Q90 of points > 50 is 90 -> sg_max = 70 > 50
    # [50, 70] contains 1/6 = 16.7 % of data_max_da points -> NOK -> sg_case = 3
    # 50 < rg_max = 60 < sg_max and sg_max - rg_max < 20 km/h -> case 3
    ([[70, 30, 30], [40] * 3], 60, False),
    # Q90 of points > 50 is 90 -> sg_max = 80 > 50
    # [60, 80] contains 1/6 = 16.7 % of data_max_da points -> NOK -> sg_case = 3
    # 50 < rg_max = 60 < sg_max and sg_max - rg_max >= 20 km/h -> case r<s_3
    ([[80, 30, 30], [40] * 3], 60, False),
    # ------------------------------------------------------------------
    # sg_max > 50 km/h, rg_max < sg_max and separation between plain and
    # mountain
    # ------------------------------------------------------------------
    # Q90 of points > 50 is 80 -> sg_max = 80 > 50
    # [60, 80] contains 3/6 = 50% of data_max_da points -> OK -> sg_case = 1
    # rg_max = 40 <= 50 -> case pm_r<s_1_s
    ([[80] * 3, [41] * 3], 40, True),
    # Q90 of points > 50 is 80 -> sg_max = 80 > 50
    # [60, 80] contains 3/6 = 50% of data_max_da points -> OK -> sg_case = 1
    # 50 < rg_max = 60 -> case pm_r<s_1_rs
    ([[80] * 3, [41] * 3], 60, True),
    # Q90 of points > 50 is 93.8 -> sg_max = 90 > 50
    # [70, 90] contains 0/6 = 0 % of data_max_da points -> NOK
    # [60, 80] contains 1/6 = 16.7 % of data_max_da points -> NOK
    # [50, 70] contains 2/6 = 33.3 % of data_max_da points -> OK -> sg_case = 2
    # rg_max = 40 <= y (= 70) -> case pm_r<s_2_s
    ([[100, 69, 51], [41] * 3], 70, True),
    # Q90 of points > 50 is 93.8 -> sg_max = 90 > 50
    # [70, 90] contains 0/6 = 0 % of data_max_da points -> NOK
    # [60, 80] contains 1/6 = 16.7 % of data_max_da points -> NOK
    # [50, 70] contains 2/6 = 33.3 % of data_max_da points -> OK -> sg_case = 2
    # 50 < rg_max = 80 > y (= 70) -> case pm_r<s_2_rs
    ([[100, 69, 51], [41] * 3], 80, True),
    # Q90 of points > 50 is 90 -> sg_max = 70 > 50
    # [50, 70] contains 1/6 = 16.7 % of data_max_da points -> NOK -> sg_case = 3
    # rg_max = 50 <= 50 -> case pm_r<s_3_s
    ([[70, 30, 30], [40] * 3], 50, True),
    # Q90 of points > 50 is 90 -> sg_max = 70 > 50
    # [50, 70] contains 1/6 = 16.7 % of data_max_da points -> NOK -> sg_case = 3
    # rg_max = 60 > 50 -> case pm_r<s_3_rs
    ([[70, 30, 30], [40] * 3], 60, True),
    # ---------------------------------------------------------------------
    # sg_max > 50 km/h, rg_max > sg_max and no separation between plain and
    # mountain
    # ---------------------------------------------------------------------
    # Q90 of points > 50 is 80 -> sg_max = 80 > 50
    # [60, 80] contains 3/6 = 50% of data_max_da points -> OK -> sg_case = 1
    # rg_max = 90 > y (= 80) -> case r>s_1
    ([[80] * 3, [41] * 3], 90, False),
    # Q90 of points > 50 is 60 -> sg_max = 60 > 50
    # [50, 70] contains 3/6 = 50% of data_max_da points -> OK -> sg_case = 1
    # rg_max = 70 <= y (= 70) -> case 1
    ([[60] * 3, [41] * 3], 70, False),
    # Q90 of points > 50 is 93.8 -> sg_max = 90 > 50
    # [70, 90] contains 0/6 = 0 % of data_max_da points -> NOK
    # [60, 80] contains 1/6 = 16.7 % of data_max_da points -> NOK
    # [50, 70] contains 2/6 = 33.3 % of data_max_da points -> OK -> sg_case = 2
    # rg_max = 100 > sg_max and rg_max - sg_max < 20 km/h -> case r>s_2_r
    ([[100, 69, 51], [41] * 3], 100, False),
    # Q90 of points > 50 is 93.8 -> sg_max = 90 > 50
    # [70, 90] contains 0/6 = 0 % of data_max_da points -> NOK
    # [60, 80] contains 1/6 = 16.7 % of data_max_da points -> NOK
    # [50, 70] contains 2/6 = 33.3 % of data_max_da points -> OK -> sg_case = 2
    # rg_max = 110 > sg_max and rg_max - sg_max >= 20 km/h -> case r>s_2_rs
    ([[100, 69, 51], [41] * 3], 110, False),
    # Q90 of points > 50 is 90 -> sg_max = 70 > 50
    # [50, 70] contains 1/6 = 16.7 % of data_max_da points -> NOK -> sg_case = 3
    # rg_max = 80 > sg_max and rg_max - sg_max < 20 km/h -> r>s_3_r
    ([[70, 30, 30], [40] * 3], 80, False),
    # Q90 of points > 50 is 90 -> sg_max = 70 > 50
    # [50, 70] contains 1/6 = 16.7 % of data_max_da points -> NOK -> sg_case = 3
    # rg_max = 90 > sg_max and rg_max - sg_max >= 20 km/h -> r>s_3_rs
    ([[70, 30, 30], [40] * 3], 90, False),
    # ------------------------------------------------------------------
    # sg_max > 50 km/h, rg_max > sg_max and separation between plain and
    # mountain
    # ------------------------------------------------------------------
    # Q90 of points > 50 is 80 -> sg_max = 80 > 50
    # [60, 80] contains 3/6 = 50% of data_max_da points -> OK -> sg_case = 1
    # rg_max = 90 > y (= 80) -> case pm_r>s_1
    ([[80] * 3, [41] * 3], 90, True),
    # Q90 of points > 50 is 60 -> sg_max = 60 > 50
    # [50, 70] contains 3/6 = 50% of data_max_da points -> OK -> sg_case = 1
    # rg_max = 70 <= y (= 70) -> case 1
    ([[60] * 3, [41] * 3], 70, True),
    # Q90 of points > 50 is 93.8 -> sg_max = 90 > 50
    # [70, 90] contains 0/6 = 0 % of data_max_da points -> NOK
    # [60, 80] contains 1/6 = 16.7 % of data_max_da points -> NOK
    # [50, 70] contains 2/6 = 33.3 % of data_max_da points -> OK -> sg_case = 2
    # rg_max = 100 > sg_max -> case pm_r>s_2
    ([[100, 69, 51], [41] * 3], 100, True),
    # Q90 of points > 50 is 90 -> sg_max = 70 > 50
    # [50, 70] contains 1/6 = 16.7 % of data_max_da points -> NOK -> sg_case = 3
    # rg_max = 80 > sg_max -> pm_r>s_3
    ([[70, 30, 30], [40] * 3], 80, True),
]


class TestGustSummaryBuilder:
    @pytest.mark.parametrize(
        "valid_time, data, units_compo, units_data, data_exp, unit_exp",
        [
            (
                generate_valid_time(periods=2),
                [[[0.0, 1.0], [np.nan, 20.0]], [[4.0, np.nan], [15.0, 18.0]]],
                {"gust": "km/h"},
                {"gust": "km/h"},
                [[[0.0, 1.0], [np.nan, 20.0]], [[4.0, np.nan], [15.0, 18.0]]],
                "km/h",
            ),
            (
                generate_valid_time(periods=2),
                [[[0.0, 1.0], [np.nan, 20.0]], [[4.0, np.nan], [15.0, 18.0]]],
                {"gust": "km/h"},
                {"gust": "m s**-1"},
                3.6
                * np.array(
                    [[[0.0, 1.0], [np.nan, 20.0]], [[4.0, np.nan], [15.0, 18.0]]]
                ),
                "km/h",
            ),
        ],
    )
    def test_units_conversion(
        self, valid_time, data, units_compo, units_data, data_exp, unit_exp
    ):
        # Test the conversion of the gust unit which has to be km/h.
        composite = CompositeFactory2x2().get(
            valid_time=valid_time,
            data_gust=data,
            units_compo=units_compo,
            units_data=units_data,
        )
        dataset = composite.weather_data()
        summary_builder = GustSummaryBuilder(parent=composite, dataset=dataset)

        assert summary_builder.gust_da.units == unit_exp

        values = summary_builder.gust_da.sel(valid_time=valid_time).values
        np.testing.assert_allclose(values, data_exp)

    @pytest.mark.parametrize(
        "valid_time, data",
        [
            (
                generate_valid_time(periods=2),
                [[[0.0, 40.0], [np.nan, 10.5]], [[20.0, 30.0], [np.nan, 40.0]]],
            ),
            (
                generate_valid_time(periods=2),
                [[[0.0, 40.0], [np.nan, 10.5]], [[20.0, 30.0], [40.0, np.nan]]],
            ),
        ],
    )
    def test_mask(self, valid_time, data, assert_equals_result):
        composite = CompositeFactory2x2().get(valid_time=valid_time, data_gust=data)
        dataset = composite.weather_data()
        summary_builder = GustSummaryBuilder(parent=composite, dataset=dataset)

        res: dict = {
            "data": data,
            "points_nbr": summary_builder.dataset.attrs["points_nbr"],
            "mask": summary_builder.mask,
        }

        assert_equals_result(res)

    @pytest.mark.parametrize(
        "valid_time, data",
        [
            (generate_valid_time(periods=1), [np.nan]),
            (generate_valid_time(periods=1), [0.0]),
            (generate_valid_time(periods=1), [50.0]),
            (generate_valid_time(periods=1), [40.0, 110.0]),  # Q90 = 110.0
            (generate_valid_time(periods=1), [54.0, 94.0]),  # Q90 = 90.0
            (generate_valid_time(periods=1), [58.0, 99.0]),  # S90 = 94.9
            (generate_valid_time(periods=1), [59.0, 99.0]),  # S90 = 95.0
            (generate_valid_time(periods=1), [72.0, 103.0]),  # Q90 = 99.9
            (generate_valid_time(periods=1), [51.0, 72.2]),  # Q90 = 69.9
            (generate_valid_time(periods=1), [52.2, 72.2]),  # Q90 = 70.0
            (generate_valid_time(periods=1), [53.0, 72.2]),  # Q90 = 70.1
            (generate_valid_time(periods=1), [51.0, 61.0]),  # Q90 = 60.0
            (
                # The Q90 is computed only y from 60.0, 61.0, 71.0, 80.0, 90.0, 132.0
                # => Q90 = 111.2
                # I_0 = [100, 120] contains 16.7 % of points < 20 %
                # I_1 = [90, 110] contains 16.7 % of points < 20 %
                # I_1 = [80, 100] contains 33.3 % of points >= 20 % => interval found
                generate_valid_time(periods=1),
                [40.0, 60.0, 61.0, 71.0, 80.0, 90.0, 132.0],  # Q90 = 111.2
            ),
        ],
    )
    def test_gust_metadata(self, valid_time, data, assert_equals_result):
        func: Callable

        if len(data) == 1:
            func = CompositeFactory1x1().get_composite_when_term_data_is_one_number
        elif len(data) == 2:
            func = CompositeFactory1x2.get
        else:
            func = CompositeFactory1x7.get

        composite = func(valid_time=valid_time, data_gust=data)

        dataset = composite.weather_data()
        summary_builder = GustSummaryBuilder(parent=composite, dataset=dataset)

        res: dict = {
            "data": data,
            "gust_max_raw": summary_builder.dataset.attrs["gust_max_raw"],
            "sg_max": summary_builder.sg_max,
            "bound_inf_init": summary_builder._initialize_bound_inf(),
        }

        assert_equals_result(res)

    @staticmethod
    def check_compute(
        composite_factory,
        valid_time,
        gust_data: list | np.ndarray,
        assert_equals_result,
    ) -> GustSummaryBuilder:
        # Check GustSummaryBuilder.compute() method.
        composite = composite_factory().get(valid_time=valid_time, data_gust=gust_data)
        dataset = composite.weather_data()
        summary_builder = GustSummaryBuilder(parent=composite, dataset=dataset)
        summary_builder.compute(Datetime(2023, 1, 2, 0, 0, 0))

        res: dict = {
            "input": {"valid_time": [str(v) for v in valid_time], "data": gust_data},
            "output": {
                "points_nbr": summary_builder.dataset.attrs["points_nbr"],
                "gust_max_da": summary_builder.gust_max_da.values,
                "gust_max_raw": summary_builder.dataset.attrs["gust_max_raw"],
                "sg_max": summary_builder.sg_max,
                "rg_max": summary_builder.rg_max,
                "summary": summary_builder.summary,
            },
        }

        case = summary_builder.case

        # If case 0, then assert_equals_result
        if case == "0":
            assert_equals_result(res)
            return summary_builder

        # Else add more elements in output before comparing
        bound_sup = summary_builder.summary.get("bound_sup")
        if bound_sup is not None:
            bound_inf = summary_builder.summary.get("bound_inf")
            res["output"].update(
                {
                    "gust_q90": summary_builder.dataset["gust_q90"].values,
                    "period": str(summary_builder._find_gust_period(bound_inf)),
                    "percent": summary_builder.compute_percent_coverage_of_interval(
                        bound_inf, bound_sup
                    ),
                }
            )
        else:
            if summary_builder.sg_max > 50:
                bound_inf = summary_builder.summary.get("bound_inf")
                assert bound_inf == 50.0
                res["output"].update(
                    {
                        "gust_q90": summary_builder.dataset["gust_q90"].values,
                        "period": str(summary_builder._find_gust_period(bound_inf)),
                    }
                )

        assert_equals_result(res)

        return summary_builder

    @pytest.mark.parametrize(
        "valid_time, gust_data",
        [
            # Case 0
            (
                generate_valid_time(periods=2),
                [[[0.0, 40.0], [np.nan, 10.5]], [[20.0, 30.0], [np.nan, 20.5]]],
            ),
            # Case 0
            (generate_valid_time(periods=1), [[0.0, 40.1], [np.nan, 10.5]]),
            # Case 0
            (generate_valid_time(periods=1), [[0.0, 20.0], [49.9, 10.5]]),
            # Case 0
            (generate_valid_time(periods=1), [[0.0, 20.0], [50.0, 10.5]]),
            # Case 2
            (generate_valid_time(periods=1), [[70.0, 70.0], [70.0, 70.0]]),
        ],
    )
    def test_compute_2x2_no_risk_gust(
        self, valid_time, gust_data: list | np.ndarray, assert_equals_result
    ):
        # Test the compute method on 2x2 grids without risk gust.
        factory = CompositeFactory2x2
        self.check_compute(factory, valid_time, gust_data, assert_equals_result)

    @pytest.mark.parametrize(
        "valid_time, gust_data", COMPLEX_CASES_WITHOUT_RG_MAX_PARAMS
    )
    def test_compute_5x2_no_risk_gust(
        self, valid_time, gust_data: list | np.ndarray, assert_equals_result
    ):
        # Test the compute method on 5x2 grids without risk gust.
        factory = CompositeFactory5x2
        self.check_compute(factory, valid_time, gust_data, assert_equals_result)

    @pytest.mark.parametrize(
        "risk_infos",
        [
            {},
            {"plain_max": 54.99},
            {"plain_max": 55.01},
            {"plain_max": 54.0, "pm_sep": False},
            {"plain_max": 55.0, "pm_sep": True},
            {"mountain_max": 54.99},
            {"mountain_max": 55.01},
            {"mountain_max": 54.0, "pm_sep": False},
            {"mountain_max": 55.0, "pm_sep": True},
            {"plain_max": 41.0, "mountain_max": 54.99},
            {"plain_max": 64.99, "mountain_max": 31},
            {"plain_max": 41.0, "mountain_max": 54.99, "pm_sep": False},
            {"plain_max": 64.99, "mountain_max": 31, "pm_sep": True},
            # Risk gust max reached in plain and mountain
            {"plain_max": 42.0, "mountain_max": 49.9, "pm_sep": True},
            # Risk gust max reached in mountain and not in plain
            {"plain_max": 42.0, "mountain_max": 50.0, "pm_sep": True},
            {
                "plain_max": 42.0,
                "mountain_max": 44.9,
                "pm_sep": True,
                "activated_risk": False,
            },
            {
                "plain_max": 42.0,
                "mountain_max": 44.9,
                "pm_sep": True,
                "activated_risk": True,
            },
            {
                "plain_max": 42.0,
                "mountain_max": 45.0,
                "pm_sep": True,
                "activated_risk": False,
            },
            {
                "plain_max": 42.0,
                "mountain_max": 45.0,
                "pm_sep": True,
                "activated_risk": True,
            },
        ],
    )
    def test_compute_rg_max_2x2(self, risk_infos: dict, assert_equals_result):
        # Test the compute method on 2x2 grids with risk gust.
        risk_infos_input: dict = copy.deepcopy(risk_infos)

        with patch(
            "mfire.text.synthesis.wind_reducers.gust_summary_builder."
            "GustSummaryBuilder._get_risk_infos",
            lambda builder, compo: risk_infos,
        ):
            composite = CompositeFactory2x2.get(
                valid_time=generate_valid_time(periods=2)
            )
            dataset = composite.weather_data()
            summary_builder = GustSummaryBuilder(parent=composite, dataset=dataset)

            res: dict = {
                "input": {"risk_infos": risk_infos_input},
                "output": {"risk_infos": risk_infos, "rg_max": summary_builder.rg_max},
            }

            assert_equals_result(res)

    @pytest.mark.parametrize("gust_data, rg_max, pm_sep", CASE_WITH_RG_MAX_PARAMS)
    def test_compute_3x2_with_risk_gust(
        self, gust_data, rg_max, pm_sep, assert_equals_result
    ):
        # Test the compute method on 3x2 grids with risk gust.

        # The max of the risk gust is reached in the plain. So if there is a separation
        # between the plain and the mountain, 'zone' ahs to be "en plaine" and 'zone_c'
        # has to be "sur les hauteurs".
        with patch(
            "mfire.text.synthesis.wind_reducers.gust_summary_builder."
            "GustSummaryBuilder._get_risk_infos",
            lambda builder, compo: {"plain_max": rg_max, "pm_sep": pm_sep},
        ):
            factory = CompositeFactory3x2
            valid_time = generate_valid_time(periods=1)
            summary_builder: GustSummaryBuilder = self.check_compute(
                factory, valid_time, gust_data, assert_equals_result
            )

            if pm_sep is True:
                assert summary_builder.risk_infos["zone"] == "en plaine"
                assert summary_builder.risk_infos["zone_c"] == "sur les hauteurs"
            else:
                for key in ["zone", "zone_c"]:
                    assert key not in summary_builder.risk_infos
