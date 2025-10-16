from collections import defaultdict
from datetime import datetime, timedelta
from unittest.mock import patch

import numpy as np
import pytest

from mfire.utils.date import Timedelta
from tests.composite.factories import (
    SynthesisCompositeInterfaceFactory,
    SynthesisModuleFactory,
)
from tests.text.synthesis.factories import WeatherBuilderFactory, WeatherReducerFactory


class TestWeatherReducer:
    """
    This test ensures that the good isolated phenomenon are excluded,
    severe phenomenon are not excluded, indicated localisation for snow, ...
    Thresholds are bigger in order to see the exclusions
    """

    def _reducer(
        self,
        codes: list,
        valid_time: list,
        requiredDT: float = 0.05,
        requiredDHmax: float = 0.05,
        **kwargs,
    ):
        np.random.seed(0)
        lat = kwargs.pop("lat", None) or [30, 31]
        lon = kwargs.pop("lon", None) or [40, 41]
        geos_descr = kwargs.pop("geos_descriptive", None) or [
            [[1] * len(lon)] * len(lat)
        ]
        altitude = kwargs.pop("altitude", None) or [[0] * len(lon)] * len(lat)

        # add useless data since data of first valid time will be deleted
        # but in some cases this data stays and so period begin 1 day before
        delta = (
            valid_time[1] - valid_time[0] if len(valid_time) > 1 else Timedelta(hours=1)
        )
        valid_time = [valid_time[0] - delta] + valid_time
        codes = [codes[0]] + codes

        data_vars = {
            "wwmf": (
                ["valid_time", "latitude", "longitude"],
                codes,
                {"units": kwargs.pop("units", None) or "wwmf"},
            )
        }
        if lpn := kwargs.pop("lpn", []):
            lpn = [lpn[0]] + lpn  # add useless data
            data_vars["lpn"] = (
                ["valid_time", "latitude", "longitude"],
                lpn,
                {"units": "m"},
            )

        composite = SynthesisModuleFactory.create_factory(
            geos_descriptive=geos_descr,
            valid_time=valid_time,
            lon=lon,
            lat=lat,
            data_vars=data_vars,
            altitude=altitude,
            **kwargs,
        )

        reducer = WeatherReducerFactory(parent=composite)
        reducer.densities["DT"]["required"] = defaultdict(lambda: requiredDT)
        reducer.densities["DHmax"]["required"] = defaultdict(lambda: requiredDHmax)
        return reducer

    def _compute(self, **kwargs):
        reducer = self._reducer(**kwargs)
        return {language: reducer.compute() for language in reducer.iter_languages()}

    def test_1_valid_time(self, assert_equals_result):
        valid_time = [datetime(2023, 3, 1)]
        lon, lat = [40], [35]
        assert_equals_result(
            self._compute(codes=[[[0]]], lon=lon, lat=lat, valid_time=valid_time)
        )

    @patch("mfire.localisation.area_algebra.MIN_IOU_THRESHOLD", 1)
    @pytest.mark.parametrize(
        "codes,show_lpn",
        [
            # No possible loc since all IoL < 0.2 => altitudes are taken
            ([[0, 0, 0], [60, 0, 0], [0, 0, 0]], False),
            # No possible loc since all IoL < 0.2 => best loc is taken
            ([[0, 0, 0], [60, 0, 0], [0, 0, 0]], True),
            # When IoL < 0.2 and the difference between the lowest point of TS and
            # map < 100m #38200
            ([[0, 0, 0], [0, 0, 0], [0, 60, 0]], False),
            # When IoL < 0.2 and no snow
            ([[0, 0, 0], [50, 0, 0], [0, 0, 0]], False),
            # Loc 2 isn't taken since IoL = 1/6 < 0.2
            ([[60, 0, 0], [0, 0, 0], [0, 0, 0]], False),
            # Loc 2 is taken since IoL > 0.2
            ([[60, 60, 0], [0, 0, 0], [0, 0, 0]], False),
            # Several loc
            ([[60, 0, 60], [0, 0, 60], [0, 0, 60]], False),
            # all domain is taken
            ([[60, 60, 60], [60, 60, 60], [60, 60, 60]], False),
            # Only loc 3
            ([[60, 60, 0], [60, 60, 0], [60, 60, 0]], False),
            # Loc 3 and 1 are taken but these zones cover all domain
            ([[60, 60, 60], [60, 60, 0], [60, 60, 0]], False),
        ],
    )
    def test_localisation_rules(self, codes, show_lpn, assert_equals_result):
        lon = [40, 41, 42]
        lat = [35, 36, 37]
        valid_time = [datetime(2023, 3, 1), datetime(2023, 3, 2)]

        geos_descriptive = [
            [[0, 0, 1], [0, 0, 1], [0, 0, 1]],
            [[1, 1, 0], [0, 0, 0], [0, 0, 0]],
            [[1, 1, 0], [1, 1, 0], [1, 1, 0]],
        ]
        altitude = [[160, 125, 345], [241, 160, 368], [30, 50, 389]]

        reducer = self._reducer(
            codes=2 * [codes],
            lpn=[[[0, 0, 0]] * 3] * 2,  # to avoid TS correction
            lon=lon,
            lat=lat,
            valid_time=valid_time,
            geos_descriptive=geos_descriptive,
            altitude=altitude,
            requiredDT=0,  # in order to not exclude isolated point
            requiredDHmax=0,  # in order to not exclude isolated point
        )
        reducer.show_lpn_factory = show_lpn
        assert_equals_result(
            {language: reducer.compute() for language in reducer.iter_languages()}
        )

    @pytest.mark.parametrize(
        "codes",
        [
            # Indicated phenomenon must last at least 3h
            [
                [[33], [33]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
            ],
            [
                [[33], [33]],
                [[33], [33]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
            ],
            [
                [[33], [33]],
                [[33], [33]],
                [[33], [33]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
            ],
            # No discontinuity if interruption less than 3 hours
            [
                [[33], [33]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[33], [33]],
                [[33], [33]],
            ],
            [
                [[33], [33]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[33], [33]],
                [[33], [33]],
                [[33], [33]],
            ],
            [
                [[33], [33]],
                [[33], [33]],
                [[0], [0]],
                [[0], [0]],
                [[33], [33]],
                [[33], [33]],
                [[33], [33]],
            ],
            [
                [[33], [33]],
                [[33], [33]],
                [[33], [33]],
                [[0], [0]],
                [[33], [33]],
                [[33], [33]],
                [[33], [33]],
            ],
            [
                [[33], [33]],
                [[0], [0]],
                [[33], [33]],
                [[0], [0]],
                [[33], [33]],
                [[0], [0]],
                [[33], [33]],
            ],
            [
                [[33], [33]],
                [[0], [0]],
                [[33], [33]],
                [[0], [0]],
                [[0], [0]],
                [[33], [33]],
                [[33], [33]],
            ],
        ],
    )
    def test_temporality_rules(self, codes, assert_equals_result):
        # This test handles the following temporality rules:
        # * if the duration is  less than 3h it is not be considered
        # * if ts lasts all the time the temporality isn't indicated
        valid_time = [
            datetime(2023, 3, 1, 10),
            datetime(2023, 3, 1, 11),
            datetime(2023, 3, 1, 12),
            datetime(2023, 3, 1, 13),
            datetime(2023, 3, 1, 14),
            datetime(2023, 3, 1, 15),
            datetime(2023, 3, 1, 16),
        ]
        lon, lat = [40], [35, 36]

        assert_equals_result(
            self._compute(codes=codes, lon=lon, lat=lat, valid_time=valid_time)
        )

    @pytest.mark.parametrize("codes", [[70], [51, 52], [51, 61, 71, 81, 91]])
    def test_grouping_rules(self, codes, assert_equals_result):
        valid_time = [datetime(2023, 3, 1), datetime(2023, 3, 2)]

        lon, lat = list(range(len(codes))), [35]
        codes = [[codes], [codes]]

        assert_equals_result(
            self._compute(codes=codes, lon=lon, lat=lat, valid_time=valid_time)
        )

    @pytest.mark.parametrize(
        "duration,codes",
        [
            # 1 severe TS
            (3, [[[49, 0], [0, 0]], [[0, 0], [0, 0]]]),
            (3, [[[59, 59], [0, 0]], [[0, 0], [0, 0]]]),
            (3, [[[0, 0], [0, 85]], [[0, 0], [0, 0]]]),
            (3, [[[0, 98], [0, 0]], [[0, 0], [0, 0]]]),
            (3, [[[0, 0], [0, 0]], [[99, 0], [0, 99]]]),
            # 2TS: 1 severe + 1 not severe
            (3, [[[49, 0], [0, 0]], [[70, 0], [0, 0]]]),
            (3, [[[85, 91], [0, 0]], [[0, 0], [0, 0]]]),
            # 3TS: 1 severe + 2 not severe
            (3, [[[49, 59], [70, 0]], [[0, 0], [0, 0]]]),
            (3, [[[49, 59], [0, 0]], [[70, 0], [0, 0]]]),
            (3, [[[49, 0], [70, 0]], [[59, 0], [0, 0]]]),
            (3, [[[49, 61], [70, 0]], [[0, 0], [0, 0]]]),
            # Short severe phenomena
            (1, [[[49, 0], [0, 0]], [[0, 0], [0, 0]]]),
            (2, [[[59, 59], [0, 0]], [[0, 0], [0, 0]]]),
            (1, [[[85, 91], [0, 0]], [[0, 0], [0, 0]]]),
            (2, [[[49, 61], [70, 0]], [[0, 0], [0, 0]]]),
        ],
    )
    def test_severe_phenomenon(self, duration, codes, assert_equals_result):
        valid_time = [
            datetime(2023, 3, 1),
            datetime(2023, 3, 1, duration),
            datetime(2023, 3, 1, 2 * duration),
        ]

        # to avoid that the phenomenon is over all the period
        codes.append([[0, 0], [0, 0]])

        # We change the requiredDT and requiredDHmax to be able to see the exclusion
        assert_equals_result(
            self._compute(
                codes=codes, valid_time=valid_time, requiredDT=0.3, requiredDHmax=0.5
            )
        )

    @pytest.mark.parametrize(
        "units,codes",
        [
            # No TS
            ("wwmf", [[[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]]]),
            ("w1", [[[0, -1], [0, 0]], [[0, -1], [0, 0]]]),
            ("wwmf", [[[1, 15], [20, 25]], [[27, 29], [7, 0]]]),
            ("wwmf", [[[3, 3], [3, 3]], [[3, 3], [3, 3]]]),
            ("wwmf", [[[1, 1], [1, 1]], [[3, 3], [3, 3]]]),
            ("wwmf", [[[1, 1], [1, 1]], [[6, 6], [6, 3]]]),
            # DT<50% and DHmax<50% => excluded since isolated
            ("wwmf", [[[90, 0], [0, 0]], [[0, 90], [0, 0]]]),
            ("w1", [[[0, 0], [0, 18]], [[0, 0], [18, 0]]]),
            ("wwmf", [[[90, 0], [0, 0]], [[90, 31], [0, 0]]]),
            ("w1", [[[0, 0], [0, 17]], [[0, 17], [2, 0]]]),
        ],
    )
    @pytest.mark.parametrize("nebulosity", [True, False])
    def test_0_ts(self, units, codes, nebulosity, assert_equals_result):
        valid_time = [datetime(2023, 3, 1), datetime(2023, 3, 2)]

        # We change the requiredDT and requiredDHmax to be able to see the exclusion
        assert_equals_result(
            self._compute(
                codes=codes,
                units=units,
                valid_time=valid_time,
                requiredDT=0.5,
                requiredDHmax=0.5,
                nebulosity=nebulosity,
            )
        )

    @pytest.mark.parametrize(
        "units,codes",
        [
            # DT>30% + DHmax>50% => not isolated
            ("wwmf", [[[50, 50], [50, 50]], [[50, 50], [50, 50]]]),
            ("w1", [[[9, 9], [9, 9]], [[9, 9], [9, 9]]]),
            ("wwmf", [[[50, 50], [50, 50]], [[0, 0], [0, 0]]]),
            ("w1", [[[0, 0], [0, 0]], [[9, 9], [9, 9]]]),
            # DT<30% + DHmax>50% => not isolated
            ("wwmf", [[[33, 33], [0, 0]], [[0, 0], [0, 0]]]),
            ("w1", [[[0, 0], [0, 0]], [[0, 5], [5, 0]]]),
            ("wwmf", [[[33, 33], [62, 62]], [[0, 0], [0, 0]]]),
            ("w1", [[[20, 0], [0, 20]], [[0, 5], [5, 0]]]),
            ("wwmf", [[[33, 33], [62, 62]], [[33, 0], [62, 0]]]),
            ("w1", [[[20, 5], [0, 20]], [[0, 5], [5, 20]]]),
            ("wwmf", [[[31, 32], [60, 62]], [[33, 0], [61, 0]]]),
            ("w1", [[[19, 4], [0, 20]], [[0, 5], [6, 21]]]),
            # Test the localisation (with snow code)
            ("wwmf", [[[0, 0], [58, 58]], [[0, 0], [58, 58]]]),
            ("w1", [[[13, 13], [13, 13]], [[0, 0], [0, 0]]]),
            # Test of code with nebulosity replacement
            ("wwmf", [[[72, 72], [72, 72]], [[0, 0], [0, 0]]]),
            ("wwmf", [[[73, 73], [73, 73]], [[0, 0], [0, 0]]]),
            ("wwmf", [[[0, 78], [0, 78]], [[0, 0], [78, 78]]]),
            ("wwmf", [[[82, 82], [82, 0]], [[0, 82], [0, 0]]]),
            ("wwmf", [[[83, 83], [83, 83]], [[0, 0], [0, 0]]]),
            # 2TS but one with DT<30%
            ("wwmf", [[[50, 50], [50, 50]], [[31, 50], [31, 50]]]),
            # 2TS but one with DT<30% and DHmax<50%
            ("wwmf", [[[50, 50], [50, 50]], [[31, 50], [0, 50]]]),
        ],
    )
    def test_1_ts(self, units, codes, assert_equals_result):
        valid_time = [datetime(2023, 3, 1), datetime(2023, 3, 2), datetime(2023, 3, 3)]
        altitude = [[1045, 1501], [2040, 2509]]

        # to avoid that the phenomenon is over all the period
        codes.append([[0, 0], [0, 0]])

        # We change the requiredDT and requiredDHmax to be able to see the exclusion
        assert_equals_result(
            self._compute(
                codes=codes,
                units=units,
                valid_time=valid_time,
                altitude=altitude,
                requiredDT=0.3,
                requiredDHmax=0.5,
            )
        )

    @pytest.mark.parametrize(
        "units,codes",
        [
            # 2TS with different families
            ("wwmf", (50, 31)),
            ("w1", (3, 9)),
            # Localisation with snow
            ("wwmf", (31, 60)),
            ("w1", (13, 2)),
            ("wwmf", (62, 63)),
            ("w1", (16, 17)),
        ],
    )
    def test_2_ts_different_families(self, units, codes, assert_equals_result):
        # This test handles simple cases with 2 TS over 2 valid_time.
        valid_time = [datetime(2023, 3, 1), datetime(2023, 3, 2), datetime(2023, 3, 3)]
        altitude = [[1070], [2099]]

        lon, lat = [40], [35, 36]
        codes = [
            [[codes[0]], [codes[0]]],
            [[codes[1]], [codes[1]]],
            [[0], [0]],  # to avoid that the phenomenon is over all the period
        ]
        assert_equals_result(
            self._compute(
                codes=codes,
                lon=lon,
                lat=lat,
                units=units,
                valid_time=valid_time,
                altitude=altitude,
            )
        )

    @pytest.mark.parametrize(
        "units,codes,durations",
        [
            # 2 TS not severe with 2 (<3) hours of covering and
            # 0.2 (<0.25) proportion of coverage => 2 distinct TS
            ("wwmf", (70, 61), (10, 2, 10)),
            ("w1", (2, 6), (10, 2, 10)),
            # 2 TS not severe with 4 (>3) hours of covering and
            # 0.2 (<0.25) proportion of coverage => 2 distinct TS
            ("wwmf", (70, 61), (20, 4, 20)),
            ("w1", (2, 6), (20, 4, 20)),
            # 2 TS not severe with 2 (<3) hours of covering and
            # 0.5 (>0.25) proportion of coverage => 2 distinct TS
            ("wwmf", (70, 61), (4, 2, 4)),
            ("w1", (2, 6), (4, 2, 4)),
            # 2 TS not severe with 4 (>3) hours of covering and
            # 0.4 (>0.25) proportion of coverage => same TS
            ("wwmf", (70, 61), (10, 4, 10)),
            ("w1", (2, 6), (10, 4, 10)),
            # 2 precipitation TS which 1 severe with 0.4 (>0.25) proportion of
            # intersection  => 2 distinct TS
            # Notice that if it was not severe it would consider as same TS
            ("wwmf", (70, 98), (10, 4, 10)),
            # 2 precipitation TS which 1 severe with 0.78 (>0.75) proportion of
            # intersection  => same TS
            ("wwmf", (70, 98), (1, 7, 1)),
        ],
    )
    def test_2_ts_same_families(self, units, codes, durations, assert_equals_result):
        # This test handles 2 TS  with valid_time which duration is given.
        # The first and second period lasts duration[0] and the third one duration[1].
        d0 = datetime(2023, 3, 1)
        valid_time = [
            d0,
            d0 + timedelta(hours=durations[0]),
            d0 + timedelta(hours=durations[0] + durations[1]),
            d0 + timedelta(hours=durations[0] + durations[1] + durations[2]),
        ]

        lon, lat = [40], [35, 36]
        codes = [
            [[0], [0]],
            [[codes[0]], [codes[0]]],
            [[codes[0]], [codes[1]]],
            [[codes[1]], [codes[1]]],
        ]
        assert_equals_result(
            self._compute(
                codes=codes, lon=lon, lat=lat, units=units, valid_time=valid_time
            )
        )

    @pytest.mark.parametrize(
        "codes,durations",
        [
            # 3 visibility TS
            ((30, 32, 33), (1, 4)),
            ((30, 32, 33), (4, 1)),
            # 3 precipitation TS with 2 subfamily
            ((51, 52, 60), (1, 4)),
            ((51, 58, 70), (4, 1)),
            # 3 precipitation TS with 1 subfamily
            ((51, 52, 53), (1, 4)),
            ((61, 62, 63), (4, 1)),
            ((70, 71, 77), (1, 4)),
            # 3 precipitation TS with 2 precipitations + 1 visibility
            ((32, 71, 77), (1, 4)),
            ((32, 70, 61), (4, 1)),
            ((71, 32, 77), (1, 4)),
            # 3 precipitation TS with 2 visibilities + 1 precipitation
            ((32, 33, 77), (4, 1)),
            ((32, 30, 61), (1, 4)),
            ((32, 77, 33), (4, 1)),
            # Phenomenon which can't be grouped by pair (according to their temporality)
            ((51, 71, 52), (2, 2)),
        ],
    )
    def test_3_ts_temporalities(self, codes, durations, assert_equals_result):
        # This test handles 3 phenomenon with two of same temporality to ensure that
        # they will be well put together.
        valid_time = [
            datetime(2023, 3, 1, 0),
            datetime(2023, 3, 1, 3),
            datetime(2023, 3, 1, 3 + durations[0]),
            datetime(2023, 3, 1, 3 + durations[0] + durations[1]),
            datetime(2023, 3, 1, 3 + durations[0] + durations[1] + 3),
        ]

        lon, lat = [40], [35, 36]
        codes = [
            [[0], [0]],
            [[codes[0]], [codes[0]]],
            [[codes[0]], [codes[1]]],
            [[codes[1]], [codes[2]]],
            [[codes[2]], [codes[2]]],
        ]
        assert_equals_result(
            self._compute(codes=codes, lon=lon, lat=lat, valid_time=valid_time)
        )

    @pytest.mark.parametrize(
        "codes",
        [
            # >3 visibility TS
            ([[[31, 32], [33, 38]], [[0, 0], [0, 0]]]),
            ([[[31, 32], [33, 38]], [[31, 39], [0, 0]]]),
            # 3 visibility TS and 1 precipitation
            ([[[31, 32], [33, 60]], [[0, 0], [0, 0]]]),
            # 2 visibility TS and 2 precipitation
            ([[[31, 61], [33, 60]], [[0, 0], [0, 0]]]),
            # 1 visibility TS and 3 precipitation
            ([[[31, 62], [63, 60]], [[0, 0], [0, 0]]]),
            # >3 precipitation TS and no severe
            ([[[51, 61], [70, 71]], [[0, 0], [0, 0]]]),
            ([[[51, 61], [70, 71]], [[80, 0], [0, 0]]]),
            ([[[51, 61], [70, 71]], [[80, 91], [0, 0]]]),
            ([[[51, 61], [70, 71]], [[80, 90], [70, 0]]]),
            ([[[51, 61], [70, 71]], [[80, 90], [50, 60]]]),
            # >3 precipitation TS and at least 1 severe
            ([[[51, 61], [70, 71]], [[98, 0], [0, 0]]]),
            ([[[51, 61], [70, 71]], [[98, 99], [0, 0]]]),
            ([[[51, 61], [70, 84]], [[98, 71], [0, 85]]]),
            ([[[51, 52], [70, 85]], [[98, 0], [0, 0]]]),
            # several precipitation + visibility TS
            ([[[51, 32], [0, 0]], [[0, 0], [84, 92]]]),
            ([[[51, 32], [33, 71]], [[80, 0], [0, 0]]]),
            ([[[51, 32], [33, 71]], [[33, 91], [83, 92]]]),
            ([[[51, 32], [33, 71]], [[33, 91], [83, 38]]]),
            ([[[51, 32], [33, 71]], [[33, 91], [83, 98]]]),
            # If there is only 2 visibilities with 31 (Haze)
            # => the code and temporality of haze aren't included
            ([[[31, 32], [60, 61]], [[31, 0], [0, 0]]]),
            # If there is at least 3 visibilities with 31 (Haze)
            # => the temporality of haze isn't included
            ([[[31, 32], [33, 61]], [[31, 60], [0, 0]]]),
            ([[[31, 32], [33, 38]], [[31, 60], [61, 0]]]),
        ],
    )
    def test_more_than_3_ts_temporalities(self, codes, assert_equals_result):
        valid_time = [datetime(2023, 3, 1), datetime(2023, 3, 2), datetime(2023, 3, 3)]

        # to avoid that the phenomenon is over all the period
        codes.append([[0, 0], [0, 0]])
        assert_equals_result(self._compute(codes=codes, valid_time=valid_time))

    @pytest.mark.parametrize(
        "code_j3,code_j4", [(50, 51), (60, 62), (90, 93), (58, 0), (63, 0), (92, 0)]
    )
    def test_handle_straddling_j3j4(self, code_j3, code_j4, assert_equals_result):
        # Handling of replacement code for straddling situation J3/J4 is tested.
        valid_time = [datetime(2023, 3, 1), datetime(2023, 3, 10)]

        assert_equals_result(
            self._compute(
                lon=[40],
                lat=[30],
                codes=[[[code_j3]], [[code_j4]]],
                valid_time=valid_time,
            )
        )

    @pytest.mark.parametrize(
        "codes,has_risk",
        [
            # Fog with not enough density
            ([[[32, 0]], [[0, 32]], [[0, 32]]], None),  # no fog
            ([[[32, 0]], [[0, 32]], [[0, 32]]], False),  # no fog
            ([[[32, 0]], [[0, 32]], [[0, 32]]], True),  # locally fog
            # Without fog with temporality in synthesis
            ([[[32, 32]], [[32, 32]], [[0, 0]]], None),  # no fog
            ([[[32, 32]], [[32, 32]], [[0, 0]]], False),  # no fog
            ([[[32, 32]], [[32, 32]], [[0, 0]]], True),  # temporally
            # With fog in synthesis
            ([[[32, 32]], [[32, 32]], [[32, 32]]], None),  # fog
            ([[[32, 32]], [[32, 32]], [[32, 32]]], True),  # fog
            ([[[32, 32]], [[32, 32]], [[32, 32]]], False),  # fog
            ([[[32, 33]], [[32, 33]], [[33, 32]]], False),  # locally
            ([[[39, 33]], [[39, 33]], [[33, 39]]], False),  # locally
        ],
    )
    def test_fog_risk(self, codes, has_risk, assert_equals_result):
        # Handling of fog risk is tested - see #38534
        valid_time = [datetime(2023, 3, 1, i) for i in range(3)]

        assert_equals_result(
            self._compute(
                lon=[30, 31],
                lat=[40],
                codes=codes,
                valid_time=valid_time,
                requiredDT=0.6,
                requiredDHmax=0.6,
                interface=SynthesisCompositeInterfaceFactory(
                    has_risk=lambda x, y, z: has_risk
                ),
            )
        )

    @pytest.mark.parametrize(
        "code,lpn,has_snow_risk,has_lpn_field",
        [
            # Lpn not indicated
            (60, 4025, True, True),  # with snow risk
            (0, 4025, False, True),  # without snow points
            (60, 4025, False, False),  # without lpn field
            # Lpn indicated > alt min
            (60, 800, False, True),
            # Lpn indicated < alt min
            (60, 1200, False, True),
        ],
    )
    def test_process_lpn(
        self, code, lpn, has_snow_risk, has_lpn_field, assert_equals_result
    ):
        np.random.seed(0)
        assert_equals_result(
            self._compute(
                lon=[30, 31],
                lat=[40],
                codes=[[[code, 0]]] * 2,
                valid_time=[datetime(2023, 3, 1), datetime(2023, 3, 2)],
                interface=SynthesisCompositeInterfaceFactory(
                    has_risk=lambda x, y, z: has_snow_risk,
                    has_field=lambda x, y, z: has_lpn_field,
                ),
                lpn=[[[lpn, lpn]]] * 2,
                altitude=[[np.inf, 1000]],  # np.inf to avoid LPN correction
            )
        )


class TestWeatherBuilder:
    def test_compute_without_condition(self):
        builder = WeatherBuilderFactory(
            parent=SynthesisModuleFactory(check_condition_factory=lambda _: False)
        )
        assert builder.compute() is None

    def test_template_key(self):
        builder = WeatherBuilderFactory(reduction_factory=[{"key": "A"}, {"key": "B"}])
        assert builder.template_key == ["A", "B"]

    @pytest.mark.parametrize(
        "reduction,expected",
        [
            ([{"key": "0xTS"}], "Temps sec."),
            ([{"key": "0xTS_nebulosity", "lab": "Ciel clair"}], "Ciel clair."),
            (
                [
                    {
                        "key": "0xTS_nebulosity_following",
                        "lab": "Ciel clair devenant nuageux",
                        "temp": "cet après-midi",
                    }
                ],
                "Ciel clair devenant nuageux cet après-midi.",
            ),
            (
                [
                    {"key": "0xTS_nebulosity", "lab": "Ciel voilé"},
                    {"key": "LPN", "low": 100},
                ],
                "Ciel voilé. Limite pluie-neige au plus bas vers 100 m.",
            ),
            ([{"key": "1xTS", "lab": "Label"}], "Label."),
            ([{"key": "1xTS_temp", "lab": "Label", "temp": "Temp"}], "Temp, Label."),
        ],
    )
    def test_compute(self, reduction, expected):
        np.random.seed(0)
        builder = WeatherBuilderFactory(reduction_factory=reduction)
        assert builder.compute() == expected

    def _builder(
        self,
        codes: list,
        valid_time: list,
        requiredDT: float = 0.05,
        requiredDHmax: float = 0.05,
        **kwargs,
    ):
        np.random.seed(0)
        lat = kwargs.pop("lat", None) or [30, 31]
        lon = kwargs.pop("lon", None) or [40, 41]
        geos_descr = kwargs.pop("geos_descriptive", None) or [
            [[1] * len(lon)] * len(lat)
        ]
        altitude = kwargs.pop("altitude", None) or [[0] * len(lon)] * len(lat)

        # add useless data since data of first valid time will be deleted
        delta = (
            valid_time[1] - valid_time[0] if len(valid_time) > 1 else Timedelta(hours=1)
        )
        valid_time = [valid_time[0] - delta] + valid_time
        codes = [codes[0]] + codes

        data_vars = {
            "wwmf": (
                ["valid_time", "latitude", "longitude"],
                codes,
                {"units": kwargs.pop("units", None) or "wwmf"},
            )
        }
        if lpn := kwargs.pop("lpn", []):
            lpn = [lpn[0]] + lpn  # add useless data
            data_vars["lpn"] = (
                ["valid_time", "latitude", "longitude"],
                lpn,
                {"units": "m"},
            )

        composite = SynthesisModuleFactory.create_factory(
            geos_descriptive=geos_descr,
            valid_time=valid_time,
            lon=lon,
            lat=lat,
            data_vars=data_vars,
            altitude=altitude,
            **kwargs,
        )

        builder = WeatherBuilderFactory(parent=composite)
        builder.reducer.densities["DT"]["required"] = defaultdict(lambda: requiredDT)
        builder.reducer.densities["DHmax"]["required"] = defaultdict(
            lambda: requiredDHmax
        )
        return builder

    def _compute(self, **kwargs):
        builder = self._builder(**kwargs)
        return {language: builder.compute() for language in builder.iter_languages()}

    def test_1_valid_time(self, assert_equals_result):
        valid_time = [datetime(2023, 3, 1)]
        lon, lat = [40], [35]
        assert_equals_result(
            self._compute(codes=[[[0]]], lon=lon, lat=lat, valid_time=valid_time)
        )

    @patch("mfire.localisation.area_algebra.MIN_IOU_THRESHOLD", 1)
    @pytest.mark.parametrize(
        "codes,show_lpn",
        [
            # No possible loc since all IoL < 0.2 => altitudes are taken
            ([[0, 0, 0], [60, 0, 0], [0, 0, 0]], False),
            # No possible loc since all IoL < 0.2 => best loc is taken
            ([[0, 0, 0], [60, 0, 0], [0, 0, 0]], True),
            # When IoL < 0.2 and the difference between the lowest point of TS and
            # map < 100m #38200
            ([[0, 0, 0], [0, 0, 0], [0, 60, 0]], False),
            # When IoL < 0.2 and no snow
            ([[0, 0, 0], [50, 0, 0], [0, 0, 0]], False),
            # Loc 2 isn't taken since IoL = 1/6 < 0.2
            ([[60, 0, 0], [0, 0, 0], [0, 0, 0]], False),
            # Loc 2 is taken since IoL > 0.2
            ([[60, 60, 0], [0, 0, 0], [0, 0, 0]], False),
            # Several loc
            ([[60, 0, 60], [0, 0, 60], [0, 0, 60]], False),
            # all domain is taken
            ([[60, 60, 60], [60, 60, 60], [60, 60, 60]], False),
            # Only loc 3
            ([[60, 60, 0], [60, 60, 0], [60, 60, 0]], False),
            # Loc 3 and 1 are taken but these zones cover all domain
            ([[60, 60, 60], [60, 60, 0], [60, 60, 0]], False),
        ],
    )
    def test_localisation_rules(self, codes, show_lpn, assert_equals_result):
        lon = [40, 41, 42]
        lat = [35, 36, 37]
        valid_time = [datetime(2023, 3, 1), datetime(2023, 3, 2)]

        geos_descriptive = [
            [[0, 0, 1], [0, 0, 1], [0, 0, 1]],
            [[1, 1, 0], [0, 0, 0], [0, 0, 0]],
            [[1, 1, 0], [1, 1, 0], [1, 1, 0]],
        ]
        altitude = [[100, 125, 345], [241, 10, 368], [-200, -150, 389]]

        builder = self._builder(
            codes=2 * [codes],
            lpn=[[[0, 0, 0]] * 3] * 2,  # to avoid TS correction
            lon=lon,
            lat=lat,
            valid_time=valid_time,
            geos_descriptive=geos_descriptive,
            altitude=altitude,
            requiredDT=0,  # in order to not exclude isolated point
            requiredDHmax=0,  # in order to not exclude isolated point
        )
        builder.reducer.show_lpn_factory = show_lpn
        assert_equals_result(
            {language: builder.compute() for language in builder.iter_languages()}
        )

    @pytest.mark.parametrize(
        "codes",
        [
            # Indicated phenomenon must last at least 3h
            [
                [[33], [33]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
            ],
            [
                [[33], [33]],
                [[33], [33]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
            ],
            [
                [[33], [33]],
                [[33], [33]],
                [[33], [33]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
            ],
            # No discontinuity if interruption less than 3 hours
            [
                [[33], [33]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[33], [33]],
                [[33], [33]],
            ],
            [
                [[33], [33]],
                [[0], [0]],
                [[0], [0]],
                [[0], [0]],
                [[33], [33]],
                [[33], [33]],
                [[33], [33]],
            ],
            [
                [[33], [33]],
                [[33], [33]],
                [[0], [0]],
                [[0], [0]],
                [[33], [33]],
                [[33], [33]],
                [[33], [33]],
            ],
            [
                [[33], [33]],
                [[33], [33]],
                [[33], [33]],
                [[0], [0]],
                [[33], [33]],
                [[33], [33]],
                [[33], [33]],
            ],
            [
                [[33], [33]],
                [[0], [0]],
                [[33], [33]],
                [[0], [0]],
                [[33], [33]],
                [[0], [0]],
                [[33], [33]],
            ],
            [
                [[33], [33]],
                [[0], [0]],
                [[33], [33]],
                [[0], [0]],
                [[0], [0]],
                [[33], [33]],
                [[33], [33]],
            ],
        ],
    )
    def test_temporality_rules(self, codes, assert_equals_result):
        # This test handles the temporality rule: if the duration is less than 3h it is
        # not be considered.
        valid_time = [
            datetime(2023, 3, 1, 10),
            datetime(2023, 3, 1, 11),
            datetime(2023, 3, 1, 12),
            datetime(2023, 3, 1, 13),
            datetime(2023, 3, 1, 14),
            datetime(2023, 3, 1, 15),
            datetime(2023, 3, 1, 16),
        ]
        lon, lat = [40], [35, 36]
        assert_equals_result(
            self._compute(codes=codes, lon=lon, lat=lat, valid_time=valid_time)
        )

    @pytest.mark.parametrize("codes", [[70], [51, 52], [51, 61, 71, 81, 91]])
    def test_grouping_rules(self, codes, assert_equals_result):
        valid_time = [datetime(2023, 3, 1), datetime(2023, 3, 2)]

        lon, lat = list(range(len(codes))), [35]
        codes = [[codes], [codes]]

        assert_equals_result(
            self._compute(codes=codes, lon=lon, lat=lat, valid_time=valid_time)
        )

    @pytest.mark.parametrize(
        "duration,codes",
        [
            # 1 severe TS
            (3, [[[49, 0], [0, 0]], [[0, 0], [0, 0]]]),
            (3, [[[59, 59], [0, 0]], [[0, 0], [0, 0]]]),
            (3, [[[0, 0], [0, 85]], [[0, 0], [0, 0]]]),
            (3, [[[0, 98], [0, 0]], [[0, 0], [0, 0]]]),
            (3, [[[0, 0], [0, 0]], [[99, 0], [0, 99]]]),
            # 2TS: 1 severe + 1 not severe
            (3, [[[49, 0], [0, 0]], [[70, 0], [0, 0]]]),
            (3, [[[85, 91], [0, 0]], [[0, 0], [0, 0]]]),
            # 3TS: 1 severe + 2 not severe
            (3, [[[49, 59], [70, 0]], [[0, 0], [0, 0]]]),
            (3, [[[49, 59], [0, 0]], [[70, 0], [0, 0]]]),
            (3, [[[49, 0], [70, 0]], [[59, 0], [0, 0]]]),
            (3, [[[49, 61], [70, 0]], [[0, 0], [0, 0]]]),
            # Short severe phenomena
            (1, [[[49, 0], [0, 0]], [[0, 0], [0, 0]]]),
            (2, [[[59, 59], [0, 0]], [[0, 0], [0, 0]]]),
            (1, [[[85, 91], [0, 0]], [[0, 0], [0, 0]]]),
            (2, [[[49, 61], [70, 0]], [[0, 0], [0, 0]]]),
        ],
    )
    def test_severe_phenomenon(self, duration, codes, assert_equals_result):
        valid_time = [
            datetime(2023, 3, 1),
            datetime(2023, 3, 1, duration),
            datetime(2023, 3, 1, 2 * duration),
        ]

        # to avoid that the phenomenon is over all the period
        codes.append([[0, 0], [0, 0]])

        # We change the requiredDT and requiredDHmax to be able to see the exclusion
        assert_equals_result(
            self._compute(
                codes=codes, valid_time=valid_time, requiredDT=0.3, requiredDHmax=0.5
            )
        )

    @pytest.mark.parametrize(
        "units,codes",
        [
            # No TS
            ("wwmf", [[[-1, -1], [-1, -1]], [[-1, -1], [-1, -1]]]),
            ("w1", [[[0, -1], [0, 0]], [[0, -1], [0, 0]]]),
            ("wwmf", [[[1, 15], [20, 25]], [[27, 29], [7, 0]]]),
            ("wwmf", [[[3, 3], [3, 3]], [[3, 3], [3, 3]]]),
            ("wwmf", [[[1, 1], [1, 1]], [[3, 3], [3, 3]]]),
            ("wwmf", [[[1, 1], [1, 1]], [[6, 6], [6, 3]]]),
            # DT<50% and DHmax<50% => excluded since isolated
            ("wwmf", [[[90, 0], [0, 0]], [[0, 90], [0, 0]]]),
            ("w1", [[[0, 0], [0, 18]], [[0, 0], [18, 0]]]),
            ("wwmf", [[[90, 0], [0, 0]], [[90, 31], [0, 0]]]),
            ("w1", [[[0, 0], [0, 17]], [[0, 17], [2, 0]]]),
        ],
    )
    @pytest.mark.parametrize("nebulosity", [True, False])
    def test_0_ts(self, units, codes, nebulosity, assert_equals_result):
        valid_time = [datetime(2023, 3, 1), datetime(2023, 3, 2)]

        # We change the requiredDT and requiredDHmax to be able to see the exclusion
        assert_equals_result(
            self._compute(
                codes=codes,
                units=units,
                valid_time=valid_time,
                requiredDT=0.5,
                requiredDHmax=0.5,
                nebulosity=nebulosity,
            )
        )

    @pytest.mark.parametrize(
        "units,valid_time,codes",
        [
            # DT>30% and DHmax>50% => not isolated
            (
                "wwmf",
                [datetime(2023, 3, 1, 8, 0, 0), datetime(2023, 3, 1, 11, 0, 0)],
                [[[50, 50], [50, 50]], [[50, 50], [50, 50]]],
            ),
            (
                "w1",
                [datetime(2023, 3, 1, 8, 0, 0), datetime(2023, 3, 1, 20, 0, 0)],
                [[[9, 9], [9, 9]], [[9, 9], [9, 9]]],
            ),
            (
                "wwmf",
                [datetime(2023, 3, 1, 14, 0, 0), datetime(2023, 3, 1, 20, 0, 0)],
                [[[50, 50], [50, 50]], [[0, 0], [0, 0]]],
            ),
            (
                "w1",
                [datetime(2023, 3, 1, 19, 0, 0), datetime(2023, 3, 1, 22, 0, 0)],
                [[[0, 0], [0, 0]], [[9, 9], [9, 9]]],
            ),
            # DT<30% + DHmax>50% => not isolated
            (
                "wwmf",
                [datetime(2023, 3, 1), datetime(2023, 3, 2)],
                [[[33, 33], [0, 0]], [[0, 0], [0, 0]]],
            ),
            (
                "w1",
                [datetime(2023, 3, 1), datetime(2023, 3, 2)],
                [[[0, 0], [0, 0]], [[0, 5], [5, 0]]],
            ),
            (
                "wwmf",
                [datetime(2023, 3, 1), datetime(2023, 3, 2)],
                [[[33, 33], [62, 62]], [[0, 0], [0, 0]]],
            ),
            (
                "w1",
                [datetime(2023, 3, 1), datetime(2023, 3, 2)],
                [[[20, 0], [0, 20]], [[0, 5], [5, 0]]],
            ),
            (
                "wwmf",
                [datetime(2023, 3, 1), datetime(2023, 3, 2)],
                [[[33, 33], [62, 62]], [[33, 0], [62, 0]]],
            ),
            (
                "w1",
                [datetime(2023, 3, 1), datetime(2023, 3, 2)],
                [[[20, 5], [0, 20]], [[0, 5], [5, 20]]],
            ),
            (
                "wwmf",
                [datetime(2023, 3, 1), datetime(2023, 3, 2)],
                [[[31, 32], [60, 62]], [[33, 0], [61, 0]]],
            ),
            (
                "w1",
                [datetime(2023, 3, 1), datetime(2023, 3, 2)],
                [[[19, 4], [0, 20]], [[0, 5], [6, 21]]],
            ),
            # Test the localisation (with snow code)
            (
                "wwmf",
                [datetime(2023, 3, 1, 23, 0, 0), datetime(2023, 4, 1, 4, 0, 0)],
                [[[0, 0], [58, 58]], [[0, 0], [58, 58]]],
            ),
            (
                "wwmf",
                [datetime(2023, 3, 1, 23, 0, 0), datetime(2023, 4, 1, 4, 0, 0)],
                [[[58, 58], [58, 0]], [[58, 58], [58, 58]]],
            ),
            (
                "w1",
                [datetime(2023, 3, 1, 23, 30, 0), datetime(2023, 5, 1, 15, 0, 0)],
                [[[13, 13], [13, 13]], [[0, 0], [0, 0]]],
            ),
            # Code replacement test with nebulosity
            # Test of code with nebulosity replacement
            (
                "wwmf",
                [datetime(2023, 3, 1), datetime(2023, 3, 2)],
                [[[72, 72], [72, 72]], [[0, 0], [0, 0]]],
            ),
            (
                "wwmf",
                [datetime(2023, 3, 1), datetime(2023, 3, 2)],
                [[[73, 73], [73, 73]], [[0, 0], [0, 0]]],
            ),
            (
                "wwmf",
                [datetime(2023, 3, 1), datetime(2023, 3, 2)],
                [[[0, 78], [0, 78]], [[0, 0], [78, 78]]],
            ),
            (
                "wwmf",
                [datetime(2023, 3, 1), datetime(2023, 3, 2)],
                [[[82, 82], [82, 0]], [[0, 82], [0, 0]]],
            ),
            (
                "wwmf",
                [datetime(2023, 3, 1), datetime(2023, 3, 2)],
                [[[83, 83], [83, 83]], [[0, 0], [0, 0]]],
            ),
        ],
    )
    def test_1_ts(self, units, valid_time, codes, assert_equals_result):
        # This test ensures that the good isolated phenomenon are excluded.
        # The threshold (50%) is bigger in order to see the exclusions
        altitude = [[1045, 1501], [2040, 2509]]

        # to avoid that the phenomenon is over all the period
        valid_time.append(valid_time[-1] + timedelta(hours=1))
        codes.append([[0, 0], [0, 0]])

        # We change the requiredDT and requiredDHmax to be able to see the exclusion
        assert_equals_result(
            self._compute(
                codes=codes,
                units=units,
                valid_time=valid_time,
                altitude=altitude,
                requiredDT=0.3,
                requiredDHmax=0.5,
            )
        )

    @pytest.mark.parametrize(
        "units,codes",
        [
            # 2TS with different families
            ("wwmf", (50, 31)),
            ("w1", (3, 9)),
            # Localisation with snow
            ("wwmf", (31, 60)),
            ("w1", (13, 2)),
            ("wwmf", (62, 63)),
            ("w1", (16, 17)),
        ],
    )
    def test_2_ts_different_families(self, units, codes, assert_equals_result):
        # This test handles simple cases with 2 TS over 2 valid_time.
        valid_time = [datetime(2023, 3, 1), datetime(2023, 3, 2), datetime(2023, 3, 3)]
        altitude = [[1070], [2099]]

        lon, lat = [40], [35, 36]
        codes = [
            [[codes[0]], [codes[0]]],
            [[codes[1]], [codes[1]]],
            [[0], [0]],  # to avoid that the phenomenon is over all the period
        ]
        assert_equals_result(
            self._compute(
                codes=codes,
                lon=lon,
                lat=lat,
                units=units,
                valid_time=valid_time,
                altitude=altitude,
            )
        )

    @pytest.mark.parametrize(
        "units,codes,durations",
        [
            # 2 TS not severe with 2 (<3) hours of covering and
            # 0.2 (<0.25) proportion of coverage => 2 distinct TS
            ("wwmf", (70, 61), (10, 2, 10)),
            ("w1", (2, 6), (10, 2, 10)),
            # 2 TS not severe with 4 (>3) hours of covering and
            # 0.2 (<0.25) proportion of coverage => 2 distinct TS
            ("wwmf", (70, 61), (20, 4, 20)),
            ("w1", (2, 6), (20, 4, 20)),
            # 2 TS not severe with 2 (<3) hours of covering and
            # 0.5 (>0.25) proportion of coverage => 2 distinct TS
            ("wwmf", (70, 61), (4, 2, 4)),
            ("w1", (2, 6), (4, 2, 4)),
            # 2 TS not severe with 4 (>3) hours of covering and
            # 0.4 (>0.25) proportion of coverage => same TS
            ("wwmf", (70, 61), (10, 4, 10)),
            ("w1", (2, 6), (10, 4, 10)),
            # 2 precipitation TS which 1 severe with 0.4 (>0.25) proportion of
            # intersection  => 2 distinct TS
            # Notice that if it was not severe it would consider as same TS
            ("wwmf", (70, 98), (10, 4, 10)),
            # 2 precipitation TS which 1 severe with 0.78 (>0.75) proportion of
            # intersection  => same TS
            ("wwmf", (70, 98), (1, 7, 1)),
        ],
    )
    def test_2_ts_same_families(self, units, codes, durations, assert_equals_result):
        # This test handles 2 TS  with valid_time which duration is given.
        # The first and second period lasts duration[0] and the third one duration[1]
        d0 = datetime(2023, 3, 1)
        valid_time = [
            d0,
            d0 + timedelta(hours=durations[0]),
            d0 + timedelta(hours=durations[0] + durations[1]),
            d0 + timedelta(hours=durations[0] + durations[1] + durations[2]),
        ]

        lon, lat = [40], [35, 36]
        codes = [
            [[0], [0]],
            [[codes[0]], [codes[0]]],
            [[codes[0]], [codes[1]]],
            [[codes[1]], [codes[1]]],
        ]
        assert_equals_result(
            self._compute(
                codes=codes, lon=lon, lat=lat, units=units, valid_time=valid_time
            )
        )

    @pytest.mark.parametrize(
        "codes,durations",
        [
            # 3 visibility TS
            ((30, 32, 33), (1, 4)),
            ((30, 32, 33), (4, 1)),
            # 3 precipitation TS with 2 subfamily
            ((51, 52, 60), (1, 4)),
            ((51, 58, 70), (4, 1)),
            # 3 precipitation TS with 1 subfamily
            ((51, 52, 53), (1, 4)),
            ((61, 62, 63), (4, 1)),
            ((70, 71, 77), (1, 4)),
            # 3 precipitation TS with 2 precipitations + 1 visibility
            ((32, 71, 77), (1, 4)),
            ((32, 70, 61), (4, 1)),
            ((71, 32, 77), (1, 4)),
            # 3 precipitation TS with 2 visibilities + 1 precipitation
            ((32, 33, 77), (4, 1)),
            ((32, 30, 61), (1, 4)),
            ((32, 77, 33), (4, 1)),
            # Phenomenon which can't be grouped by pair (according to their temporality)
            ((51, 71, 52), (2, 2)),
        ],
    )
    def test_3_ts_temporalities(self, codes, durations, assert_equals_result):
        # This test handles 3 phenomenon with two of same temporality to ensure that
        # they will be well put together.
        valid_time = [
            datetime(2023, 3, 1, 0),
            datetime(2023, 3, 1, 3),
            datetime(2023, 3, 1, 3 + durations[0]),
            datetime(2023, 3, 1, 3 + durations[0] + durations[1]),
            datetime(2023, 3, 1, 3 + durations[0] + durations[1] + 3),
        ]

        lon, lat = [40], [35, 36]
        codes = [
            [[0], [0]],
            [[codes[0]], [codes[0]]],
            [[codes[0]], [codes[1]]],
            [[codes[1]], [codes[2]]],
            [[codes[2]], [codes[2]]],
        ]

        assert_equals_result(
            self._compute(codes=codes, lon=lon, lat=lat, valid_time=valid_time)
        )

    @pytest.mark.parametrize(
        "codes",
        [
            # >3 visibility TS
            ([[[31, 32], [33, 38]], [[0, 0], [0, 0]]]),
            ([[[31, 32], [33, 38]], [[31, 39], [0, 0]]]),
            # 3 visibility TS and 1 precipitation
            ([[[31, 32], [33, 60]], [[0, 0], [0, 0]]]),
            # 2 visibility TS and 2 precipitation
            ([[[31, 61], [33, 60]], [[0, 0], [0, 0]]]),
            # 1 visibility TS and 3 precipitation
            ([[[31, 62], [63, 60]], [[0, 0], [0, 0]]]),
            # >3 precipitation TS and no severe
            ([[[51, 61], [70, 71]], [[0, 0], [0, 0]]]),
            ([[[51, 61], [70, 71]], [[80, 0], [0, 0]]]),
            ([[[51, 61], [70, 71]], [[80, 91], [0, 0]]]),
            ([[[51, 61], [70, 71]], [[80, 90], [70, 0]]]),
            ([[[51, 61], [70, 71]], [[80, 90], [50, 60]]]),
            # >3 precipitation TS and at least 1 severe
            ([[[51, 61], [70, 71]], [[98, 0], [0, 0]]]),
            ([[[51, 61], [70, 71]], [[98, 99], [0, 0]]]),
            ([[[51, 61], [70, 84]], [[98, 71], [0, 85]]]),
            ([[[51, 52], [70, 85]], [[98, 0], [0, 0]]]),
            # several precipitation + visibility TS
            ([[[51, 32], [0, 0]], [[0, 0], [84, 92]]]),
            ([[[51, 32], [33, 71]], [[80, 0], [0, 0]]]),
            ([[[51, 32], [33, 71]], [[33, 91], [83, 92]]]),
            ([[[51, 32], [33, 71]], [[33, 91], [83, 38]]]),
            ([[[51, 32], [33, 71]], [[33, 91], [83, 98]]]),
            # If there is only 2 visibilities with 31 (Haze)
            # => the code and temporality of haze aren't included
            ([[[31, 32], [60, 61]], [[31, 0], [0, 0]]]),
            # If there is at least 3 visibilities with 31 (Haze)
            # => the temporality of haze isn't included
            ([[[31, 32], [33, 61]], [[31, 60], [0, 0]]]),
            ([[[31, 32], [33, 38]], [[31, 60], [61, 0]]]),
        ],
    )
    def test_more_than_3_ts_temporalities(self, codes, assert_equals_result):
        valid_time = [datetime(2023, 3, 1), datetime(2023, 3, 2), datetime(2023, 3, 3)]

        # to avoid that the phenomenon is over all the period
        codes.append([[0, 0], [0, 0]])
        assert_equals_result(self._compute(codes=codes, valid_time=valid_time))

    @pytest.mark.parametrize(
        "code_j3,code_j4", [(50, 51), (60, 62), (90, 93), (58, 0), (63, 0), (92, 0)]
    )
    def test_handle_straddling_j3j4(self, code_j3, code_j4, assert_equals_result):
        # Handling of replacement code for straddling situation J3/J4 is tested
        valid_time = [datetime(2023, 3, 1), datetime(2023, 3, 10)]

        assert_equals_result(
            self._compute(
                lon=[40],
                lat=[30],
                codes=[[[code_j3]], [[code_j4]]],
                valid_time=valid_time,
            )
        )

    @pytest.mark.parametrize(
        "codes,has_risk",
        [
            # Fog with not enough density
            ([[[32, 0]], [[0, 32]], [[0, 32]]], None),  # no fog
            ([[[32, 0]], [[0, 32]], [[0, 32]]], False),  # no fog
            ([[[32, 0]], [[0, 32]], [[0, 32]]], True),  # locally fog
            # Without fog with temporality in synthesis
            ([[[32, 32]], [[32, 32]], [[0, 0]]], None),  # no fog
            ([[[32, 32]], [[32, 32]], [[0, 0]]], False),  # no fog
            ([[[32, 32]], [[32, 32]], [[0, 0]]], True),  # temporally
            # With fog in synthesis
            ([[[32, 32]], [[32, 32]], [[32, 32]]], None),  # fog
            ([[[32, 32]], [[32, 32]], [[32, 32]]], True),  # fog
            ([[[32, 32]], [[32, 32]], [[32, 32]]], False),  # fog
            ([[[32, 33]], [[32, 33]], [[33, 32]]], False),  # locally
            ([[[39, 33]], [[39, 33]], [[33, 39]]], False),  # locally
        ],
    )
    def test_fog_risk(self, codes, has_risk, assert_equals_result):
        # Handling of fog risk is tested - see #38534
        valid_time = [datetime(2023, 3, 1, i) for i in range(3)]

        assert_equals_result(
            self._compute(
                lon=[30, 31],
                lat=[40],
                codes=codes,
                valid_time=valid_time,
                requiredDT=0.6,
                requiredDHmax=0.6,
                interface=SynthesisCompositeInterfaceFactory(
                    has_risk=lambda x, y, z: has_risk
                ),
            )
        )

    @pytest.mark.parametrize(
        "code,lpn,has_snow_risk,has_lpn_field",
        [
            # Lpn not indicated
            (60, 4025, True, True),  # with snow risk
            (0, 4025, False, True),  # without snow points
            (60, 4025, False, False),  # without lpn field
            # Lpn indicated > alt min
            (60, 800, False, True),
            # Lpn indicated < alt min
            (60, 1200, False, True),
        ],
    )
    def test_process_lpn(
        self, code, lpn, has_snow_risk, has_lpn_field, assert_equals_result
    ):
        np.random.seed(0)
        assert_equals_result(
            self._compute(
                lon=[30, 31],
                lat=[40],
                codes=[[[code, 0]]] * 2,
                valid_time=[datetime(2023, 3, 1), datetime(2023, 3, 2)],
                interface=SynthesisCompositeInterfaceFactory(
                    has_risk=lambda x, y, z: has_snow_risk,
                    has_field=lambda x, y, z: has_lpn_field,
                ),
                lpn=[[[lpn, lpn]]] * 2,
                altitude=[[np.inf, 1000]],  # np.inf to avoid LPN correction
            )
        )
