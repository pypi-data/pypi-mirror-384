from datetime import datetime
from unittest.mock import patch

import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.text.synthesis.wind_reducers.exceptions import WindSynthesisError
from mfire.text.synthesis.wind_reducers.wind import WindSummaryBuilder
from mfire.text.synthesis.wind_reducers.wind.case3 import (
    BlockSummaryBuilder,
    Case3SummaryBuilder,
    TwoBlocksSummaryBuilder,
)
from mfire.text.synthesis.wind_reducers.wind.wind_intensity import Pci
from mfire.utils.date import Datetime
from tests.composite.factories import BaseCompositeFactory
from tests.text.utils import generate_valid_time, generate_valid_time_v2

from .factories import (
    CompositeFactory1x1,
    CompositeFactory2x2,
    CompositeFactory2x2Type1,
    CompositeFactory5x2,
    CompositeFactory6x2,
    CompositeFactory6x4,
    WindIntensityFactory,
)


class TestWindDataConversion:
    @pytest.mark.parametrize(
        "valid_time, wind_data, units_compo, units_data, data_exp, unit_exp",
        [
            # All parametrization produce examples with only type 1 terms: then the
            # data is not filtered
            (
                generate_valid_time(periods=2),
                [[[0.0, 1.0], [np.nan, 15.0]], [[4.0, np.nan], [16.0, 20.0]]],
                {"wind": "km/h"},
                {"wind": "km/h"},
                [[[0.0, 1.0], [np.nan, 15.0]], [[4.0, np.nan], [16.0, 20.0]]],
                "km/h",
            ),
            (
                generate_valid_time(periods=2),
                [[[0.0, 1.0], [0.0, 15.0]], [[4.0, 0.0], [16.0, 20.0]]],
                {"wind": "km/h"},
                {"wind": "km/h"},
                [[[0.0, 1.0], [0.0, 15.0]], [[4.0, 0.0], [16.0, 20.0]]],
                "km/h",
            ),
            (
                generate_valid_time(periods=2),
                [[[0.0, 1.0], [np.nan, 1.0]], [[1.0, 0.0], [1.0, 1.0]]],
                {"wind": "km/h"},
                {"wind": "m s**-1"},
                3.6 * np.array([[[0.0, 1.0], [np.nan, 1.0]], [[1.0, 0.0], [1.0, 1.0]]]),
                "km/h",
            ),
            (
                generate_valid_time(periods=2),
                [[[0.0, 1.0], [0.0, 1.0]], [[1.0, 0.0], [1.0, 1.0]]],
                {"wind": "km/h"},
                {"wind": "m s**-1"},
                3.6 * np.array([[[0.0, 1.0], [0.0, 1.0]], [[1.0, 0.0], [1.0, 1.0]]]),
                "km/h",
            ),
        ],
    )
    def test_wind_units_conversion(
        self, valid_time, wind_data, units_compo, units_data, data_exp, unit_exp
    ):
        # Test wind force initialization and conversion. Nan values are replaced by 0
        # and the wind force unit has to be km/h.
        composite = CompositeFactory2x2().get(
            valid_time=valid_time,
            data_wind=wind_data,
            units_compo=units_compo,
            units_data=units_data,
        )
        dataset = composite.weather_data()
        summary_builder = WindSummaryBuilder(parent=composite, dataset=dataset)

        # Check unit
        data_array: xr.DataArray = summary_builder.wind
        assert data_array.units == unit_exp

        # Check value after conversion
        np.testing.assert_allclose(data_array.values, data_exp)

    @pytest.mark.parametrize(
        "valid_time, data, units_compo, units_data, data_exp, unit_exp",
        [
            (
                generate_valid_time(periods=2),
                [[[0.1, 1.0], [np.nan, 20.0]], [[4.0, np.nan], [15.0, 18.0]]],
                {"direction": "deg"},
                {"direction": "deg"},
                [[[0.1, 1.0], [np.nan, 20.0]], [[4.0, np.nan], [15.0, 18.0]]],
                "deg",
            ),
            (
                generate_valid_time(periods=2),
                [[[0.1, 1.0], [0.0, 20.0]], [[4.0, np.nan], [15.0, 18.0]]],
                {"direction": "deg"},
                {"direction": "°"},
                [[[0.1, 1.0], [np.nan, 20.0]], [[4.0, np.nan], [15.0, 18.0]]],
                "deg",
            ),
        ],
    )
    def test_direction_units_conversion(
        self, valid_time, data, units_compo, units_data, data_exp, unit_exp
    ):
        # Test wind direction initialization and conversion. The wind direction unit has
        # to be km/h.
        composite = CompositeFactory2x2Type1().get(
            valid_time=valid_time,
            data_dir=data,
            units_compo=units_compo,
            units_data=units_data,
        )
        dataset = composite.weather_data()
        summary_builder = WindSummaryBuilder(parent=composite, dataset=dataset)

        # Check unit
        data_array: xr.DataArray = summary_builder.direction
        assert data_array.units == unit_exp

        # Check value after conversion
        np.testing.assert_allclose(data_array.values, data_exp)


class TestWindSummaryInitialization:
    def test_points_nbr(self):
        valid_time = generate_valid_time(periods=1)

        composite = CompositeFactory5x2().get(
            valid_time=valid_time, data_wind=np.full((5, 2), 20.0)
        )
        dataset = composite.weather_data()
        summary_builder = WindSummaryBuilder(parent=composite, dataset=dataset)

        points_nbr_exp = 5 * 2
        assert summary_builder.dataset.attrs["points_nbr"] == points_nbr_exp

    @pytest.mark.parametrize(
        "term_data, lower_bound, count_exp, percent_exp",
        [
            (
                [[1.0, 2.0], [3.0, 3.0], [4.0, 5.0], [30.0, 31.0], [32.0, 33.0]],
                20.0,
                4,
                40.0,
            ),
            (
                [
                    [np.nan, np.nan],
                    [np.nan, np.nan],
                    [30.0, 31.0],
                    [32.0, 33.0],
                    [34.0, 35.0],
                ],
                20.0,
                6,
                100.0,
            ),
            (
                [
                    [np.nan, np.nan],
                    [np.nan, np.nan],
                    [1.0, 2.0],
                    [3.0, 33.0],
                    [34.0, 35.0],
                ],
                20.0,
                3,
                50.0,
            ),
            (np.full((5, 2), np.nan), 30.0, 0, 0.0),
            (np.full((5, 2), 0.0), 30.0, 0, 0.0),
        ],
    )
    def test_count_points(self, term_data, lower_bound, count_exp, percent_exp):
        valid_time = generate_valid_time(periods=1)

        composite = CompositeFactory5x2().get(
            valid_time=valid_time, data_wind=term_data
        )
        dataset = composite.weather_data()
        summary_builder = WindSummaryBuilder(parent=composite, dataset=dataset)

        data = summary_builder.wind.sel(valid_time=valid_time[0])
        count, percent = summary_builder.count_points(data, data >= lower_bound)

        assert count == count_exp
        assert percent == percent_exp

    @staticmethod
    @patch(
        "mfire.text.synthesis.wind_reducers.wind.WindSummaryBuilder."
        "WF_TYPE_SEPARATORS",
        [15.0, 30.0],
    )  # We mock the wind types separator to easily simulate the wind situations
    def _check_wind_summary_builder(
        composite_factory, valid_time, data_wf, data_wd, assert_equals_result
    ):
        # Test WindSummaryBuilder.

        # We mock the wind types separator to easily simulate the wind situations.

        # Test the most sensitive data from the initialization to the summary dictionary
        # generation:
        # - term types
        # - case
        # - dataset.attrs
        # - wind data
        # - direction data

        # Compute the composite
        composite = composite_factory.get(
            valid_time=valid_time, data_wind=data_wf, data_dir=data_wd
        )
        dataset = composite.weather_data()
        summary_builder = WindSummaryBuilder(parent=composite, dataset=dataset)

        # Generate summary
        reference_datetime: Datetime = Datetime(datetime.now())
        summary_builder.compute(reference_datetime)

        # Build result
        result: dict = {
            "input": {
                "valid_time": [str(v) for v in valid_time],
                "data_wf": data_wf,
                "data_wd": data_wd,
            },
            "wind_type": summary_builder.wind_type.values.tolist(),
            "dataset_attrs": summary_builder._get_sorted_dataset_attrs(),
            "data_wf": summary_builder.wind.values.tolist(),
            "data_wd": summary_builder.direction.values.tolist(),
        }

        assert_equals_result(result)

    @pytest.mark.parametrize(
        "valid_time, data_wf, data_wd",
        [
            # All point have no wind force
            # --> term of type 1
            (
                generate_valid_time(periods=1),  # valid_time
                np.full((5, 2), np.nan),  # data_wf
                np.full((5, 2), np.nan),  # data_wd
            ),
            # Each point has a wind force < 15 --> term of type 1
            (
                generate_valid_time(periods=1),
                [[1.0, 2.0], [4.0, 5.0], [6.0, 7.0], [np.nan, np.nan], [8.0, 14.9]],
                [
                    [10.0, 11.0],
                    [12.0, 13.0],
                    [14.0, 15.0],
                    [np.nan, np.nan],
                    [18.0, 19.0],
                ],
            ),
            # The wind force are in [1, 15] --> type 2
            (
                generate_valid_time(periods=1),
                [[1.0, 2.0], [4.0, 5.0], [6.0, 7.0], [np.nan, np.nan], [8.0, 15.0]],
                [
                    [10.0, 11.0],
                    [12.0, 13.0],
                    [14.0, 15.0],
                    [np.nan, np.nan],
                    [18.0, 19.0],
                ],
            ),
            # A point has a wind force >= 35 and the threshold is 13.3
            # 1/10 points (10. %) with a wind force >= 35 --> possibly a type 3
            # 1/10 points (10. %) with a wind force >= threshold --> type 3
            (
                generate_valid_time(periods=1),
                [[1.0, 2.0], [4.0, 5.0], [6.0, 7.0], [8.0, 9.0], [8.0, 35.0]],
                [
                    [10.0, 11.0],
                    [12.0, 13.0],
                    [14.0, 15.0],
                    [np.nan, np.nan],
                    [18.0, 19.0],
                ],
            ),
            # All points have a wind force equal to 25.0  --> type 2
            (generate_valid_time(periods=1), [[25.0, 25.0]] * 5, [[10.0, 11.0]] * 5),
            # All points have a wind force  >= 35  --> type 3
            (generate_valid_time(periods=1), [[35.0, 40.0]] * 5, [[10.0, 11.0]] * 5),
        ],
    )
    def test_wind_summary_builder_5x2(
        self, valid_time, data_wf, data_wd, assert_equals_result
    ):
        # Test the WindSummaryBuilder with terms of 5x2 size.
        self._check_wind_summary_builder(
            CompositeFactory5x2, valid_time, data_wf, data_wd, assert_equals_result
        )

    @pytest.mark.parametrize(
        "valid_time, data_wf, data_wd",
        [
            # A point has a wind force equal to 35.0 and the threshold is 8.0
            # 1/11 points (9.1 %) with a wind force >= 35 --> possibly a type 3
            # 1/12 points (9.1 %) with a wind force >= threshold --> type 2
            (
                generate_valid_time(periods=1),
                [
                    [1.0, 1.0],
                    [np.nan, 1.0],
                    [1.0, 1.0],
                    [1.0, 1.0],
                    [1.0, 1.0],
                    [1.0, 35.0],
                ],
                [
                    [10.0, 11.0],
                    [np.nan, 13.0],
                    [14.0, 15.0],
                    [16.0, 17.0],
                    [18.0, 19.0],
                    [20.0, 21.0],
                ],
            ),
            # A point has a wind force equal to 35.0 and the threshold is 25.2
            # 2/10 points (20.0 %) with a wind force >= 35 --> possibly a type 3
            # 2/10 points (20.0 %) with a wind force >= threshold --> type 3
            (
                generate_valid_time(periods=1),
                [
                    [1.0, 2.0],
                    [np.nan, 3.0],
                    [np.nan, 5.0],
                    [6.0, 7.0],
                    [8.0, 9.0],
                    [36.0, 35.0],
                ],
                [
                    [10.0, 11.0],
                    [np.nan, 13.0],
                    [np.nan, 15.0],
                    [16.0, 17.0],
                    [18.0, 19.0],
                    [20.0, 21.0],
                ],
            ),
            # Threshold = 13.0
            # - term 0: all points < 15 --> type 1
            # - term 1: 4/12 (33.3 %) points with wind >= 15 --> type 2
            # - term 2: 2/12 (16.7 %) points with wind force >= 35 --> possibly a type 3
            # 4/12 points (33.3 %) with a wind force >= threshold --> type 3
            (
                generate_valid_time(periods=3),
                [
                    [
                        [1.0, 2.0],
                        [3.0, 3.0],
                        [4.0, 5.0],
                        [6.0, 7.0],
                        [8.0, 9.0],
                        [10.0, 11.0],
                    ],
                    [
                        [1.0, 2.0],
                        [3.0, 3.0],
                        [4.0, 5.0],
                        [6.0, 7.0],
                        [16.0, 17.0],
                        [18.0, 19.0],
                    ],
                    [
                        [1.0, 2.0],
                        [3.0, 3.0],
                        [4.0, 5.0],
                        [6.0, 7.0],
                        [16.0, 17.0],
                        [35.0, 35.0],
                    ],
                ],
                [
                    [
                        [1.0, 2.0],
                        [3.0, 3.0],
                        [4.0, 5.0],
                        [6.0, 7.0],
                        [16.0, 17.0],
                        [18.0, 19.0],
                    ],
                    [
                        [10.0, 11.0],
                        [12.0, 13.0],
                        [14.0, 15.0],
                        [16.0, 17.0],
                        [18.0, 19.0],
                        [20.0, 21.0],
                    ],
                    [
                        [22.0, 23.0],
                        [24.0, 25.0],
                        [26.0, 27.0],
                        [28.0, 29.0],
                        [30.0, 31.0],
                        [32.0, 33.0],
                    ],
                ],
            ),
            # Threshold = 8.3
            # - term 0: all points < 15 --> type 1
            # - term 1: 4/12 (33.3 %) points with wind >= 15 --> type 2
            # - term 2: 1/12 (8.3 %) points with wind force >= 35 --> possibly a type 3
            # 1/12 points (8.3 %) with a wind force >= threshold --> type 2
            (
                generate_valid_time(periods=3),
                [
                    [
                        [1.0, 2.0],
                        [3.0, 3.0],
                        [4.0, 5.0],
                        [6.0, 7.0],
                        [8.0, 9.0],
                        [10.0, 11.0],
                    ],
                    [
                        [1.0, 2.0],
                        [3.0, 3.0],
                        [4.0, 5.0],
                        [6.0, 7.0],
                        [16.0, 17.0],
                        [18.0, 19.0],
                    ],
                    [
                        [1.0, 1.0],
                        [1.0, 1.0],
                        [1.0, 1.0],
                        [1.0, 1.0],
                        [1.0, 5.0],
                        [np.nan, 35.0],
                    ],
                ],
                [
                    [
                        [1.0, 2.0],
                        [3.0, 3.0],
                        [4.0, 5.0],
                        [6.0, 7.0],
                        [16.0, 17.0],
                        [18.0, 19.0],
                    ],
                    [
                        [10.0, 11.0],
                        [12.0, 13.0],
                        [14.0, 15.0],
                        [16.0, 17.0],
                        [18.0, 19.0],
                        [20.0, 21.0],
                    ],
                    [
                        [22.0, 23.0],
                        [24.0, 25.0],
                        [26.0, 27.0],
                        [28.0, 29.0],
                        [30.0, 31.0],
                        [32.0, 33.0],
                    ],
                ],
            ),
        ],
    )
    def test_wind_summary_builder_6x2(
        self, valid_time, data_wf, data_wd, assert_equals_result
    ):
        # Test the WindSummaryBuilder with terms of 5x2 size.
        self._check_wind_summary_builder(
            CompositeFactory6x2, valid_time, data_wf, data_wd, assert_equals_result
        )

    @pytest.mark.parametrize(
        "valid_time, data_wf, data_wd",
        [
            # Threshold = 0
            # There is point >= 15 --> --> possibly a type 2
            # 1/24 points (4.1 %) with a wind force >= 15 --> type 1
            (
                generate_valid_time(periods=1),
                [
                    [1.0, 1.0, 1.0, 1.0],
                    [1.0, 1.0, 1.0, 1.0],
                    [1.0, 1.0, 1.0, 1.0],
                    [1.0, 1.0, 1.0, 1.0],
                    [1.0, 1.0, 1.0, 1.0],
                    [1.0, 1.0, 1.0, 20.0],
                ],
                [
                    [1.0, 2.0, 3.0, 3.0],
                    [5.0, 6.0, 7.0, 8.0],
                    [9.0, 10.0, 11.0, 12.0],
                    [13.0, 14.0, 15.0, 16.0],
                    [17.0, 18.0, 19.0, 20.0],
                    [21.0, 22.0, 23.0, 24.0],
                ],
            ),
            # Threshold = 0
            # There is point >= 35 --> --> possibly a type 3
            # - 1/24 points (4.1 %) with a wind force >= 35 --> not a type 3
            # - 1/24 points (4.1 %) with a wind force >= 15 --> not a type 2
            # so this is a term of type 1
            (
                generate_valid_time(periods=1),
                [
                    [1.0, 1.0, 1.0, 1.0],
                    [1.0, 1.0, 1.0, 1.0],
                    [1.0, 1.0, 1.0, 1.0],
                    [1.0, 1.0, 1.0, 1.0],
                    [1.0, 1.0, 1.0, 1.0],
                    [1.0, 1.0, 1.0, 35.0],
                ],
                [
                    [1.0, 2.0, 3.0, 3.0],
                    [5.0, 6.0, 7.0, 8.0],
                    [9.0, 10.0, 11.0, 12.0],
                    [13.0, 14.0, 15.0, 16.0],
                    [17.0, 18.0, 19.0, 20.0],
                    [21.0, 22.0, 23.0, 24.0],
                ],
            ),
            # Threshold = 7.1
            # There is point >= 35 --> --> possibly a type 3
            # - 1/24 points (4.1 %) with a wind force >= 35 --> not a type 3
            # - 2/24 points (8.3 %) with a wind force >= 15 --> type 2
            (
                generate_valid_time(periods=1),
                [
                    [1.0, 1.0, 1.0, 1.0],
                    [1.0, 1.0, 1.0, 1.0],
                    [1.0, 1.0, 1.0, 1.0],
                    [1.0, 1.0, 1.0, 1.0],
                    [1.0, 1.0, 1.0, 1.0],
                    [1.0, 1.0, 20.0, 35.0],
                ],
                [
                    [1.0, 2.0, 3.0, 3.0],
                    [5.0, 6.0, 7.0, 8.0],
                    [9.0, 10.0, 11.0, 12.0],
                    [13.0, 14.0, 15.0, 16.0],
                    [17.0, 18.0, 19.0, 20.0],
                    [21.0, 22.0, 23.0, 24.0],
                ],
            ),
        ],
    )
    def test_wind_summary_builder_6x4(
        self, valid_time, data_wf, data_wd, assert_equals_result
    ):
        # Test the WindSummaryBuilder with terms of 5x2 size.
        self._check_wind_summary_builder(
            CompositeFactory6x4, valid_time, data_wf, data_wd, assert_equals_result
        )


class TestGenerateSummaryCase1:
    class CompositeFactory(CompositeFactory2x2):
        LON = [30, 31]
        LAT = [40, 41]

    def test(self):
        valid_time = generate_valid_time(periods=1)

        composite = self.CompositeFactory().get(
            valid_time=valid_time, data_wind=np.full((2, 2), 9.0)
        )
        dataset = composite.weather_data()
        summary_builder = WindSummaryBuilder(parent=composite, dataset=dataset)
        reference_datetime: Datetime = Datetime(datetime.now())
        summary = summary_builder.compute(reference_datetime)

        summary_exp = {"wind": {"case": "1"}}
        assert summary == summary_exp


TEST_CASE3_PARAMS: list = [
    (
        # Input Fingerprint: 111222222233333333333333
        # The last group is the only one type 3 group and then has the wind force
        # max [25, 35[.
        # WindBlock with 1 PCI, 1 PCD
        generate_valid_time(periods=24),
        [5] * 3 + [15] * 7 + [25] * 10 + [30] * 4,
        [90] * 24,
    ),
    (
        # Input Fingerprint: 333333332233333333333333
        # The type 2 group hase size 2 between 2 type 3 groups
        # => we will get only one merged WindBlock
        # 1 WindBlock with 1 PCI, no PCD
        generate_valid_time(periods=24),
        [25] * 8 + [15] * 2 + [26] * 14,
        [np.nan] * 24,
    ),
    (
        # Input Fingerprint: 333222222233333333333333
        # 2 type 3 groups:
        # - 1st is < 4h => not kept
        # - the last which is >= 4 and has the wind force max
        # 1 WindBlocks: 1 PCI, no PCD
        generate_valid_time(periods=24),
        [25] * 3 + [15] * 7 + [26] * 14,
        [np.nan] * 24,
    ),
    (
        # Input Fingerprint: 322222222222222222222222
        # Only the 1st term has the type 3
        # 1 WindBlock: 1 PCI, no PCD (because
        # dir period of 1h < 3h)
        generate_valid_time(periods=4),
        [25] * 1 + [15] * 3,
        [10] * 4,
    ),
    (
        # Input Fingerprint: 332222222222222222222222
        # Only one type 3 group with the 1srt 2 terms.
        # 1 WindBlock: 1 PCI, no PCD (because dir period of 2h < 3h)
        generate_valid_time(periods=4),
        [25] * 2 + [15] * 2,
        [10] * 4,
    ),
    (
        # Input Fingerprint: 333222222222222222222222
        # Only one type 3 group with the first 3 terms.
        # 1 WindBlock: 1 PCI, 1 PCD
        generate_valid_time(periods=4),
        [25] * 3 + [15] * 1,
        [10] * 4,
    ),
    (
        # Input Fingerprint: 222222223223223223223223
        # Type 3 terms are separated by 2-terms groups. The Last has the type 3.
        # 1 WindBlock: 1 PCI, 1 PCD
        generate_valid_time(periods=24),
        [15] * 8 + [25, 15, 15] * 5 + [25],
        [90] * 24,
    ),
    (
        # Input Fingerprint: 222222223223223223223222
        # Type 3 terms are separated by 2-terms groups. The Last has the type 2.
        # 1 WindBlock: 1 PCI, 1 PCD
        generate_valid_time(periods=24),
        [15] * 8 + [25, 15, 17] * 5 + [15],
        [180] * 24,
    ),
    (
        # Input Fingerprint: 22222222222222222222223
        # Only the last term has the type 3
        # 1 WindBlock: 1 PCI, no PCD (because dir period of 1h < 3h)
        generate_valid_time(periods=4),
        [17] * 3 + [25],
        [10] * 4,
    ),
    (
        # Input Fingerprint: 333322222233333333333333
        # 2 type 3 groups (1st and last), wind force max is in the last
        # 2 WindBlocks
        generate_valid_time(periods=24),
        [25] * 4 + [17] * 6 + [26] * 14,
        [np.nan] * 24,
    ),
    (
        # Input Fingerprint: 333222222233333333333333
        # 2 type 3 groups (1st and last), wind force max is in the 1st
        # 2 WindBlocks
        generate_valid_time(periods=24),
        [30] * 3 + [16] * 7 + [25] * 14,
        [np.nan] * 24,
    ),
    (
        # Input Fingerprint: 333222222233333333333333
        # 2 type 3 groups (1st and last), wind force max in all type 3 group
        # 2 WindBlocks
        generate_valid_time(periods=24),
        [26] * 3 + [15] * 7 + [26] * 14,
        [np.nan] * 24,
    ),
    (
        # Input Fingerprint: 22222222223222222222222
        # Max wind force is on the only one type 3 term
        # 1 WindBlocks: 1 PCI, 0 PCD
        generate_valid_time(periods=5),
        [16] * 1 + [26] * 1 + [16] * 3,
        [150] * 5,
    ),
    (
        # Input Fingerprint: 333322222233333322223333
        # Max wind force is in the first type 3 group
        # There are 3 WindBlocks => the 2 last are the closest and will be
        # merged. So there will stay only 2 WindBlocks.
        generate_valid_time(periods=24),
        [27] * 4 + [15] * 6 + [26] * 6 + [16] * 4 + [26] * 4,
        [np.nan] * 24,
    ),
    (
        # Input Fingerprint: 333322222233333322223333
        # Max wind force is in all type 3 group
        # There are 3 WindBlocks => the 2 last are the closest and will be
        # merged. So there will stay only 2 WindBlocks.
        generate_valid_time(periods=24),
        [26] * 4 + [15] * 6 + [26] * 6 + [16] * 4 + [26] * 4,
        [np.nan] * 24,
    ),
    (
        # Input Fingerprint: 222222222333222222222223
        # 2 type 3 groups, wind force max is in 1st type 3 group, the last is so
        # short
        # 1 WindBlock: PCI, no PCD
        generate_valid_time(periods=24),
        [15] * 9 + [26] * 3 + [16] * 10 + [25] * 2,
        [360] * 24,
    ),
    (
        # Input Fingerprint: 333333333333333333333333
        # All terms are of type 3
        # Same WindDirection in the 1st and the last PCD
        # 1 WindBlock: 1 PCI, 2 PCD
        generate_valid_time(periods=24),
        [26] * 24,
        [0.1] * 4 + [150] * 12 + [0.1] * 8,
    ),
    (
        # Input Fingerprint: 333333333333333333333333
        # All terms are of type 3
        # The 1st and the last direction are opposite => no PCD
        # 1 WindBlock: 1 PCI, 0 PCD
        generate_valid_time(periods=24),
        [25] * 24,
        [180] * 4 + [np.nan] * 12 + [0.1] * 8,
    ),
    (
        # Input Fingerprint: 322222222333222222222222
        # Only short type 3 groups, wind force max 31 is in 2nd so is kept
        # 1 WindBlock: 1 PCI, no PCD
        generate_valid_time(periods=24),
        [25] * 2 + [15] * 7 + [26] * 3 + [15] * 12,
        [50] * 24,
    ),
    (
        # Input Fingerprint: 322222222333222222222222
        # Only short type 3 groups, wind force max 60 is in 2nd so is kept
        # 1 WindBlock: 1 PCI, no PCD
        generate_valid_time(periods=24),
        [25] * 2 + [15] * 7 + [45] * 5 + [20] * 10,
        [np.nan] * 24,
    ),
    (
        # Input Fingerprint: 22233222
        # 3-hours terms => 1 type group of 6 hours
        # 1 WindBlock: 1 PCI, 2 PCD
        generate_valid_time(periods=8, freq="3h"),
        [15] * 3 + [25] * 2 + [16] * 3,
        [np.nan] * 3 + [0.1] * 1 + [150] * 1 + [np.nan] * 3,
    ),
    (
        # Input Fingerprint: 222222222222222333333
        # 1 type 3 group at the end
        # 1 WindBlock: 1 PCI, 1 PCD
        generate_valid_time_v2("2023-01-02", (16, "h"), (5, "3h")),
        [15] * 15 + [25] * 6,
        [0.1] * 21,
    ),
    (
        # Input Fingerprint: 333322222222222222222322
        # 2 type 3 groups, wind force max in the 1st, the 2nd is so short
        # 1 WindBlock: 1 PCI, 1 PCD
        generate_valid_time(periods=24),
        [26] * 4 + [15] * 17 + [25] * 1 + [16] * 2,
        [0.1] * 24,
    ),
    (
        # Input Fingerprint: 333322222222222222223222
        # 2 type 3 groups, wind force max in the 2nd: all kept
        # 2 WindBlock
        generate_valid_time(periods=24),
        [25] * 4 + [15] * 16 + [26] * 1 + [15] * 3,
        [0.1] * 24,
    ),
    (
        # Input Fingerprint: 2323233332323222
        # 1 WindBlock
        generate_valid_time(periods=16),
        [15] + [25, 15] * 2 + [29] * 4 + [15, 25] * 2 + [15] * 3,
        [0.1] * 16,
    ),
    (
        # Input Fingerprint: only one term of type 3
        # 1 WindBlock
        generate_valid_time(periods=1),
        [45],
        [0.1],
    ),
    (
        # Input Fingerprint: 333222222222333333333222222222333333
        # The 2 first WindBlocks should be merged
        # 2 Windblocks: 3 changing and unordered WindIntensity
        generate_valid_time(periods=36),
        [75] * 3 + [15] * 9 + [65] * 9 + [15] * 9 + [75] * 6,
        [np.nan] * 36,
    ),
    (
        # Input Fingerprint: 333111111111333333333111111111333333
        # Same result as previous test: the 2 first WindBlocks should be merged
        # 2 Windblocks: 3 changing and unordered WindIntensity
        generate_valid_time(periods=36),
        [75] * 3 + [1] * 9 + [65] * 9 + [1] * 9 + [75] * 6,
        [np.nan] * 36,
    ),
    (
        # Input Fingerprint: 333222222233333333333333
        # 2 type 3 blocks: 1st so short, wind force max in the last
        # 1 Windblock: 1 PCI, no PCD
        generate_valid_time(periods=24),
        [25] * 3 + [20] * 7 + [34] * 14,
        [np.nan] * 24,
    ),
    (
        # Input Fingerprint: 333222222233333333333333
        # 2 type 3 blocks: wind force max in the 1st, 2nd enough long then kept
        # 2 Windblocks
        generate_valid_time(periods=24),
        [29] * 3 + [20] * 7 + [26] * 14,
        [5] * 24,
    ),
    (
        # Input Fingerprint: 333322222233333322223333
        # There are 3 WindBlocks => the 2 last are the closest and will be
        # merged. So there will stay only 2 WindBlocks.
        generate_valid_time(periods=24),
        [26] * 4 + [20] * 6 + [26] * 6 + [20] * 4 + [34.9] * 4,
        [90] * 12 + [180] * 12,
    ),
    (
        # Input Fingerprint: 222222222333222222222223
        # Max wind force is in 1st type 3 group (last type 3 terms no kept)
        # 1 WindBlock: 1 PCI, no PCD
        generate_valid_time(periods=24),
        [20] * 9 + [34] * 3 + [20] * 10 + [25] * 2,
        [0.1] * 24,
    ),
    (
        # Input Fingerprint: 322222222333222222222222
        # Max wind force is in the 2 WindBlocks
        # 2 WindBlocks
        generate_valid_time(periods=24),
        [26] * 2 + [20] * 7 + [26] * 3 + [20] * 12,
        [np.nan] * 24,
    ),
    (
        # Input Fingerprint: 333322222222222222222322
        # Max wind force is in the 1st WindBlock
        # 1 WindBlock: 1 PCI, 1 PCD
        generate_valid_time(periods=24),
        [34] * 4 + [20] * 17 + [25] * 1 + [20] * 2,
        [0.1] * 24,
    ),
    (
        # Input Fingerprint: 333333333333333333333333
        # More than 3 wi but they are ordered from the min to the max
        # 1 WindBlock:
        # - 3 PCI with [25, 35[, [35, 50[ and [70, ...[ wi
        # => only [25, 35[ and [70, ...[ wi are kept
        # - 1 PCD
        # case: case 3_1B_2_1
        generate_valid_time(periods=24),
        [25] * 20 + [35] * 2 + [70] * 2,
        [360] * 24,
    ),
    (
        # Input Fingerprint: 333333333333333333333333
        # More than 3 wi but they are ordered from the max to the min
        # 1 WindBlock:
        # - 3 PCI with [70, ...[, [50, 70[ and [25, 35[ wi
        # => only [70, ...[ and [25, 35[ wi are kept
        # - same wind direction for the 2 blocks => 1 PCD
        # case: case 3_1B_2_1
        generate_valid_time(periods=24),
        [70] * 2 + [50] * 2 + [25] * 20,
        [360] * 24,
    ),
    (
        # Input Fingerprint: 333333333322223333333333
        # More than 3 wi but they are ordered from the min to the max
        # 2 WindBlocks
        # - B1: 1 PCI with [25, 35[ wi
        # - B2: 2 PCI with [35, 50[ and [70, ...[ wi
        # - same wind direction for the 2 blocks
        # => only [25, 35[ and [70, ...[ wi are kept
        # - same wind direction for the 2 blocks => 1 PCD
        # case: case 3_2B_2_1_1_1
        generate_valid_time(periods=24),
        [25] * 16 + [np.nan] * 4 + [35] * 2 + [70] * 2,
        [360] * 24,
    ),
    (
        # Input Fingerprint: 333333333322223333333333
        # More than 3 wi but they are ordered from the max to the min
        # 2 WindBlocks
        # - B1: 1 PCI with [70, ...[ and [35, 50[ wi
        # - B2: 2 PCI with [25, 35[ wi
        # - same wind direction for the 2 blocks => 1 PCD
        # => only [70, ...[ and [25, 35[ wi are kept
        # case: case 3_2B_2_1_1_1
        generate_valid_time(periods=24),
        [70] * 2 + [35] * 2 + [np.nan] * 4 + [25] * 16,
        [360] * 24,
    ),
    (
        # Input Fingerprint: 333333333333333333333333
        # More than 2 unordered wi with 1 WindBlock:
        # 3 PCI with [35, 50[, [25, 35[ and [70, ...[ wi
        # => only min = [25, 35[ and max [70, ...[ wi are kept
        # case: case 3_1B_>2_1
        generate_valid_time(periods=24),
        [35] * 2 + [25] * 20 + [70] * 2,
        [360] * 24,
    ),
    (
        # Input Fingerprint: 333333333322223333333333
        # More than 2 unordered wi with 2 WindBlocks
        # - B1: 1 PCI with [35, 50[ and [70, ...[ wi
        # - B2: 2 PCI with [25, 35[ wi
        # - same wind direction for the 2 blocks => 1 PCD
        # => only min = [25, 35[ and max [70, ...[ wi are kept
        # case: case 3_2B_>2_2_1_1
        generate_valid_time(periods=24),
        [35] * 2 + [70] * 2 + [np.nan] * 4 + [25] * 16,
        [360] * 4 + [np.nan] * 4 + [90] * 16,
    ),
    (
        # Input Fingerprint: 333333333333333333333333
        # 1 PCI
        # 2 opposite directions => no PCD
        # case: 3_1B_1_0
        generate_valid_time(periods=12),
        [45] * 12,
        [360] * 6 + [180] * 6,
    ),
    (
        # Input Fingerprint: 333333333333333333333333
        # 2 PCI
        # 2 opposite directions => no PCD
        # case: 3_1B_2_0
        generate_valid_time(periods=12),
        [35] * 9 + [50] * 3,
        [360] * 6 + [180] * 6,
    ),
    (
        # Input Fingerprint: 333333333333333333333333
        # 3 unordered PCI
        # 2 opposite directions => no PCD
        # case: 3_1B_>2_0
        generate_valid_time(periods=24),
        [35] * 2 + [25] * 20 + [70] * 2,
        [360] * 12 + [180] * 12,
    ),
    (
        # Input Fingerprint: 333333333333333333333333
        # 1 PCI
        # The 1st and last directions are opposite => no PCD
        # case: 3_1B_1_0
        generate_valid_time(periods=12),
        [35] * 12,
        [360] * 4 + [90] * 4 + [180] * 4,
    ),
    (
        # Input Fingerprint: 333333333333333333333333
        # 2 PCI
        # 2 opposite directions => no PCD
        # case: 3_1B_2_0
        generate_valid_time(periods=12),
        [35] * 9 + [50] * 3,
        [360] * 4 + [90] * 4 + [180] * 4,
    ),
    (
        # Input Fingerprint: 333333333333333333333333
        # 3 unordered PCI
        # 2 opposite directions => no PCD
        # case: 3_1B_>2_0
        generate_valid_time(periods=24),
        [35] * 2 + [25] * 20 + [70] * 2,
        [360] * 8 + [90] * 8 + [180] * 8,
    ),
    (
        # Input Fingerprint: 333333333322223333333333
        # 1 PCI
        # 2 opposite directions => no PCD
        # case: case 3_2B_1_0_0_0
        generate_valid_time(periods=24),
        [35] * 10 + [np.nan] * 4 + [35] * 10,
        [360] * 10 + [np.nan] * 4 + [180] * 10,
    ),
    (
        # Input Fingerprint: 333333333322223333333333
        # 2 PCI
        # 2 opposite directions => no PCD
        # case: case 3_2B_2_0_0_0
        generate_valid_time(periods=24),
        [45] * 10 + [np.nan] * 4 + [65] * 10,
        [360] * 10 + [np.nan] * 4 + [180] * 10,
    ),
    (
        # Input Fingerprint: 333333333322223333333333
        # 3 unordered PCI
        # 2 opposite directions => no PCD
        # case: case 3_2B_>2_0_0_0
        generate_valid_time(periods=24),
        [55] * 1 + [30] * 15 + [np.nan] * 4 + [35] * 4,
        [360] * 16 + [np.nan] * 4 + [180] * 4,
    ),
    (
        # Input Fingerprint: 333333333322223333333333
        # 1 PCI
        # 2 dir periods: the 1st and last directions are equals
        # => 1 PCD
        # case: case 3_2B_1_1_1_1
        generate_valid_time(periods=24),
        [35] * 10 + [np.nan] * 4 + [40] * 10,
        [360] * 10 + [np.nan] * 4 + [360] * 10,
    ),
    (
        # Input Fingerprint: 333333333322223333333333
        # 2 PCI
        # 2 dir periods: the 1st and last directions are equals
        # => 1 PCD
        # case: case 3_2B_2_1_1_1
        generate_valid_time(periods=24),
        [45] * 10 + [np.nan] * 4 + [50] * 10,
        [360] * 10 + [np.nan] * 4 + [360] * 10,
    ),
    (
        # Input Fingerprint: 333333333322223333333333
        # 3 unordered PCI
        # 2 dir periods: the 1st and last directions are equals
        # => 1 PCD
        # case: case 3_2B_>2_1_1_1
        generate_valid_time(periods=24),
        [49] * 9 + [70] * 1 + [np.nan] * 4 + [50] * 10,
        [360] * 10 + [np.nan] * 4 + [360] * 10,
    ),
    (
        # Input Fingerprint: 333333333322223333333333
        # 2 PCI
        # 3 dir periods: the 1st and last directions are equals
        # => no PCD
        # case: case 3_2B_2_1_1_1
        generate_valid_time(periods=24),
        [45] * 10 + [np.nan] * 4 + [50] * 10,
        [360] * 5 + [90] * 5 + [np.nan] * 4 + [360] * 10,
    ),
    (
        # Input Fingerprint: 333333333322223333333333
        # 3 unordered PCI
        # 3 dir periods: the 1st and last directions are equals
        # => no PCD
        # case: case 3_2B_>2_1_1_1
        generate_valid_time(periods=24),
        [45] * 9 + [70] * 1 + [np.nan] * 4 + [50] * 10,
        [360] * 5 + [90] * 5 + [np.nan] * 4 + [360] * 10,
    ),
    (
        # Input Fingerprint: 222233333333333333333333
        # 1 PCI
        # The period starting from the 1st long enough PCD and finishing by the last
        # long enough PCD is 45 % of the monitoring period
        # => < 50 % => no PCD
        # case: case 3_1B_1_0
        generate_valid_time(periods=24),
        [20] * 4 + [45] * 20,
        [np.nan] * 8 + [90] * 4 + [np.nan] + [180] * 4 + [np.nan] * 7,
    ),
    (
        # Input Fingerprint: 222233333333333333333333
        # 1 PCI
        # The period starting from the 1st long enough PCD and finishing by the last
        # long enough PCD is 50 % of the block period
        # => 2 PCD
        # case: case 3_1B_1_2
        generate_valid_time(periods=24),
        [20] * 4 + [45] * 20,
        [np.nan] * 8 + [90] * 4 + [np.nan] * 2 + [180] * 4 + [np.nan] * 6,
    ),
    (
        # Input Fingerprint: 222233333333333322223333
        # 2 WindBlocks
        # In the 1st block: the PCD is 41.6 % of the block period
        # => no PCD for the 1st block
        # 1 PCD fot the 2nd block
        # case: case 3_2B_2_1_0_1
        generate_valid_time(periods=24),
        [20] * 4 + [49] * 12 + [20] * 4 + [80] * 4,
        [np.nan] * 4 + [np.nan] + [180] * 5 + [np.nan] * 6 + [45] * 8,
    ),
    (
        # Input Fingerprint: 222233333333333322223333
        # 2 WindBlocks
        # In the 1st block: the period starting from the 1st long enough PCD and
        # finishing by the last long enough PCD is 50 % of the block period
        # => 2 PCD for the 1st block
        # 1 PCD fot the 2nd block
        # case: case 3_2B_2_3_2_1
        generate_valid_time(periods=24),
        [20] * 4 + [45] * 12 + [20] * 4 + [80] * 4,
        [np.nan] * 4 + [180] * 3 + [90] * 3 + [np.nan] * 6 + [45] * 8,
    ),
    (
        # Input Fingerprint: 333333333322223333333333
        # - B1: 1 PCI with [30, 50[ intensity, 1 PCD with (90, 80) angle
        # - B2: 1 PCI with [65, 75[ intensity, 1 PCD with (320, 80) angle
        # - 2 PCI with [30, 50[ and [65, 75[ intensities
        # - 2 PCD with (50, 80) and (320, 80) angles
        # PCI and PCD change at the same time
        # case: 3_2B_2_2_1_1_simultaneous_change
        generate_valid_time(periods=24),
        [25] * 10 + [20] * 4 + [50] * 10,
        [90] * 10 + [np.nan] * 4 + [360] * 10,
    ),
    (
        # Input Fingerprint: 333333333322223333333333
        # - B1: 1 PCI with [30, 50[ intensity, 1 PCD with (90, 80) angle
        # - B2: 1 PCI with [65, 75[ intensity, 1 PCD with (320, 80) angle
        # - 2 PCI with [30, 50[ and [65, 75[ intensities
        # - 2 PCD with (50, 80) and (320, 80) angles
        # PCI and PCD don't change at the same time
        # case: 3_2B_2_2_1_1
        generate_valid_time(periods=24),
        [25] * 10 + [20] * 4 + [55] * 10,
        [90] * 10 + [np.nan] * 8 + [360] * 6,
    ),
]

TEST_CASE3_WI_ATTENUATION_1_BLOCK: list = [
    (
        # 1 PCI, its wi is not attenuable -> no attenuation
        generate_valid_time(periods=6),
        [50] * 1 + [15] * 5,
    ),
    (
        # 1 PCI, its wi represents 16.6 % < 20% of all terms
        # -> attenuate with prefix `modéré à assez fort`
        generate_valid_time(periods=6),
        [30] * 1 + [15] * 5,
    ),
    (
        # 1 PCI, its wi represents 16.6 % < 20% of all terms
        # -> attenuate with prefix `assez fort à fort`
        generate_valid_time(periods=6),
        [40] * 1 + [15] * 5,
    ),
    (
        # 1 PCI, its wi represents 33 % of all terms -> no attenuation
        generate_valid_time(periods=6),
        [30] * 2 + [15] * 4,
    ),
    (
        # 1 PCI, its wi represents 33 % of all terms -> no attenuation
        generate_valid_time(periods=6),
        [40] * 2 + [15] * 4,
    ),
    (
        # 2 PCI with reinforcement and no juxtaposed wi, where only the lowest is
        # attenuable and covers less than 20 % of terms -> no attenuation
        generate_valid_time(periods=6),
        [30] * 1 + [50] * 2 + [15] * 3,
    ),
    (
        # 2 PCI with weakening and no juxtaposed wi, where only the lowest is
        # attenuable and covers less than 20 % of terms -> no attenuation
        generate_valid_time(periods=6),
        [50] * 2 + [30] * 1 + [15] * 3,
    ),
    (
        # 2 PCI with reinforcement and juxtaposed wi, the lowest represents 16.6 % of
        # all terms -> attenuate with prefix `modéré à assez fort`
        generate_valid_time(periods=6),
        [30] * 1 + [40] * 2 + [15] * 3,
    ),
    (
        # 2 PCI with reinforcement and juxtaposed wi, the lowest represents 33 % of all
        # terms -> no attenuation
        generate_valid_time(periods=6),
        [30] * 2 + [40] * 2 + [15] * 2,
    ),
    (
        # 2 PCI with weakening and juxtaposed wi, the lowest represents 16.6 % of all
        # terms -> attenuate with prefix `modéré à assez fort`
        generate_valid_time(periods=6),
        [40] * 2 + [30] * 1 + [15] * 3,
    ),
    (
        # 2 PCI with weakening, the lowest represents 33 % of all terms
        # -> no attenuation
        generate_valid_time(periods=6),
        [40] * 2 + [30] * 2 + [15] * 2,
    ),
    (
        # 3 PCI with reinforcement 3 wi
        # -> no attenuation
        generate_valid_time(periods=6),
        [30] * 2 + [40] * 2 + [50] * 2,
    ),
    (
        # Initially 3 PCI with weakening 3 wi
        # -> no attenuation
        generate_valid_time(periods=6),
        [50] * 2 + [40] * 2 + [30] * 2,
    ),
    (
        # 3 PCI where min wi and max wi are juxtaposed: the lowest represents 16.6 % of
        # all terms -> attenuation by replacement: 'assez fort` replaced by `modéré`
        generate_valid_time(periods=12),
        [30] * 1 + [40] * 10 + [30] * 1,
    ),
    (
        # 3 PCI where min wi and max wi are juxtaposed:  the lowest represents 16.6 % of
        # all terms -> attenuation by replacement: 'assez fort` replaced by `modéré`
        generate_valid_time(periods=12),
        [40] * 5 + [30] * 2 + [40] * 5,
    ),
    (
        # 3 PCI where min wi and max wi are juxtaposed: the lowest represents 33 % of
        # all terms -> no attenuation
        generate_valid_time(periods=6),
        [30] * 2 + [40] * 2 + [30] * 2,
    ),
    (
        # 3 PCI where min wi and max wi are juxtaposed: the lowest represents 33 % of
        # all terms -> no attenuation
        generate_valid_time(periods=6),
        [40] * 2 + [30] * 2 + [40] * 2,
    ),
    (
        # 3 PCI where max wi not attenuable -> no attenuation
        generate_valid_time(periods=6),
        [30] * 2 + [50] * 2 + [40] * 2,
    ),
]

TEST_CASE3_WI_ATTENUATION_2_BLOCKS: list = [
    (
        # 1 PCI, its wi is not attenuable -> no attenuation
        generate_valid_time(periods=24),
        [50] * 5 + [15] * 14 + [50] * 5,
    ),
    (
        # 1 PCI, its wi represents 16.6 % < 20% of all terms
        # -> attenuation with prefix `modéré à assez fort`
        generate_valid_time(periods=24),
        [30] * 2 + [15] * 20 + [30] * 2,
    ),
    (
        # 1 PCI, its wi represents 16.6 % < 20% of all terms
        # -> attenuate with prefix `assez fort à fort`
        generate_valid_time(periods=24),
        [40] * 2 + [15] * 20 + [40] * 2,
    ),
    (
        # 2 PCI with reinforcement and no juxtaposed wi, where only the lowest is
        # attenuable -> no attenuation
        generate_valid_time(periods=24),
        [30] * 5 + [15] * 14 + [50] * 5,
    ),
    (
        # 2 PCI with weakening and no juxtaposed wi, where only the lowest is
        # attenuable -> no attenuation
        generate_valid_time(periods=24),
        [50] * 5 + [15] * 14 + [30] * 5,
    ),
    (
        # 2 PCI with reinforcement, the lowest represents 4/24 terms ie 16.6 % of all
        # terms -> attenuate with prefix `modéré à assez fort`
        generate_valid_time(periods=24),
        [30] * 4 + [15] * 14 + [40] * 6,
    ),
    (
        # 2 PCI with reinforcement, the lowest represents 5/24 = 20.8 % of all terms
        # -> no attenuation
        generate_valid_time(periods=24),
        [30] * 5 + [15] * 13 + [40] * 6,
    ),
    (
        # 2 PCI with weakening, the lowest represents 4/24 terms ie 16.6 % of all
        # terms -> attenuate with prefix `modéré à assez fort`
        generate_valid_time(periods=24),
        [40] * 8 + [15] * 12 + [30] * 4,
    ),
    (
        # 2 PCI with weakening, the lowest represents 5/24 = 20.8 % of all terms
        # -> no attenuation
        generate_valid_time(periods=24),
        [40] * 6 + [15] * 13 + [30] * 5,
    ),
    (
        # 3 PCI with reinforcement 3 wi
        # -> no attenuation
        generate_valid_time(periods=24),
        [30] * 6 + [40] * 6 + [15] * 6 + [50] * 6,
    ),
    (
        # 3 PCI with weakening 3 wi
        # -> no attenuation
        generate_valid_time(periods=24),
        [50] * 6 + [40] * 6 + [15] * 6 + [30] * 6,
    ),
    (
        # 3 PCI where min wi and max wi are juxtaposed: the lowest represents 20.8 % of
        # all terms -> no attenuation
        generate_valid_time(periods=24),
        [30] * 3 + [40] * 7 + [15] * 10 + [30] * 4,
    ),
    (
        # 3 PCI where min wi and max wi are juxtaposed: the lowest represents 20.8 % of
        # all terms -> no attenuation
        generate_valid_time(periods=24),
        [40] * 6 + [15] * 6 + [30] * 5 + [40] * 7,
    ),
]


class TestGenerateSummaryCase3:
    @staticmethod
    def _create_summary_builder_from_composite(composite) -> WindSummaryBuilder:
        # Create a WindSummaryBuilder from a composite.
        dataset = composite.weather_data()
        summary_builder: WindSummaryBuilder = WindSummaryBuilder(
            parent=composite, dataset=dataset
        )
        return summary_builder

    @staticmethod
    def _run_case3_from_summary_builder(
        summary_builder: WindSummaryBuilder,
    ) -> Case3SummaryBuilder:
        # Run Case3SummaryBuilder from the dataset of a summary builder.
        reference_datetime: Datetime = Datetime(datetime.now())
        case3_summary_builder: Case3SummaryBuilder = Case3SummaryBuilder(
            parent=BaseCompositeFactory()
        )
        case3_summary_builder.run(summary_builder.dataset, reference_datetime)
        return case3_summary_builder

    def build_and_check_wind_blocks(self, composite):
        # Build and check WindBlocks from composite.
        summary_builder: WindSummaryBuilder
        summary_builder = self._create_summary_builder_from_composite(composite)
        case3_summary_builder: Case3SummaryBuilder
        case3_summary_builder = self._run_case3_from_summary_builder(summary_builder)
        block_summary_builder: BlockSummaryBuilder
        block_summary_builder = case3_summary_builder.block_summary_builder

        expected: dict = {
            "wind_blocks": [
                str(b) for b in case3_summary_builder.blocks_builder.blocks
            ],
            "pci": [str(p) for p in block_summary_builder.pci],
            "pcd": [str(p) for p in block_summary_builder.pcd],
            "counters": case3_summary_builder.block_summary_builder.counters,
            "summary": case3_summary_builder.summary,
        }

        if isinstance(block_summary_builder, TwoBlocksSummaryBuilder):
            expected.update(
                {
                    "pcd_g0": [str(p) for p in block_summary_builder.pcd_g0],
                    "pcd_g1": [str(p) for p in block_summary_builder.pcd_g1],
                }
            )

        return expected

    def test_pci_sorted_key(self, assert_equals_result):
        pci: list[Pci] = [
            Pci(
                begin_time=Datetime(2023, 2, 2, 3, 0, 0),
                end_time=Datetime(2023, 2, 2, 6, 0, 0),
                wi=WindIntensityFactory(70),
            ),
            Pci(
                begin_time=Datetime(2023, 2, 2, 9, 0, 0),
                end_time=Datetime(2023, 2, 2, 12, 0, 0),
                wi=WindIntensityFactory(35),
            ),
            Pci(
                begin_time=Datetime(2023, 2, 2, 6, 0, 0),
                end_time=Datetime(2023, 2, 2, 9, 0, 0),
                wi=WindIntensityFactory(25),
            ),
            Pci(
                begin_time=Datetime(2023, 2, 2, 3, 0, 0),
                end_time=Datetime(2023, 2, 2, 6, 0, 0),
                wi=WindIntensityFactory(35),
            ),
        ]

        pci.sort(key=BlockSummaryBuilder.pci_sorted_key)

        assert_equals_result([str(p) for p in pci])

    @pytest.mark.parametrize("valid_time, data_wf, data_wd", TEST_CASE3_PARAMS)
    def test_block_builder_grid_1x1(
        self, valid_time, data_wf, data_wd, assert_equals_result
    ):
        # Test resulting WindBlocks built from 1x1 grid data.
        composite = CompositeFactory1x1.get_composite_when_term_data_is_one_number(
            valid_time=valid_time, data_wind=data_wf, data_dir=data_wd
        )

        result: dict = {
            "input": {
                "valid_time": [str(v) for v in valid_time],
                "data_wf": data_wf,
                "data_wd": data_wd,
            }
        }

        with patch(
            "mfire.text.synthesis.wind_reducers.wind.WindSummaryBuilder."
            "WF_PERCENTILE_NUM",
            50,
        ):
            result.update(self.build_and_check_wind_blocks(composite))

        assert_equals_result(result)

    @patch(
        "mfire.text.synthesis.wind_reducers.wind.WindSummaryBuilder."
        "WF_TYPE3_CONFIRMATION_PERCENT",
        5,
    )
    @pytest.mark.parametrize(
        "valid_time, data_wf, data_wd",
        [
            (
                # Input Fingerprint: 23
                # 3h step between terms
                # Q95 max for each term: 24.9 and 25
                # => Q95 max is 25 (and not 65 which is the wind force max but not the
                # Q95 max)
                # Wind direction of each term: (320, 80) and (110, 80)
                # => 1 WindBlock containing the 2nd term
                generate_valid_time_v2("2023-01-02", (2, "3h")),
                [
                    [
                        [14.9, 24.9, 24.9, 24.9],
                        [24.9, 24.9, 24.9, 24.9],
                        [24.9, 24.9, 24.9, 24.9],
                        [24.9, 24.9, 24.9, 24.9],
                        [24.9, 24.9, 24.9, 24.9],
                        [24.9, 24.9, 24.9, 65.0],
                    ],
                    [
                        [24.9, 25.0, 25.0, 25.0],
                        [25.0, 25.0, 25.0, 25.0],
                        [25.0, 25.0, 25.0, 25.0],
                        [25.0, 25.0, 25.0, 25.0],
                        [25.0, 25.0, 25.0, 25.0],
                        [25.0, 25.0, 25.0, 21.0],
                    ],
                ],
                [np.full((6, 4), 0.1), np.full((6, 4), 150.0)],
            ),
            (
                # Input Fingerprint: 323
                # monitoring period: 8h
                # Q95 max for each term: 25.0, 16.0 and 41.85
                # => the Q95 max is 41.85 (and not 50. which are in the 2nd term)
                # => only the last term are kept
                # Wind direction of each term: (320, 80), (110, 80) and (110, 80)
                # => 1 WindBlock containing the 2nd type3-term
                generate_valid_time_v2("2023-01-02", (1, "2h"), (1, "3h"), (1, "4h")),
                [
                    [
                        [25.0, 25.0, 25.0, 25.0],
                        [25.0, 25.0, 25.0, 25.0],
                        [25.0, 25.0, 25.0, 25.0],
                        [25.0, 25.0, 25.0, 25.0],
                        [25.0, 25.0, 25.0, 25.0],
                        [25.0, 25.0, 25.0, 60.0],
                    ],  # Q95 = 25.0
                    [
                        [16.0, 16.0, 16.0, 16.0],
                        [16.0, 16.0, 16.0, 16.0],
                        [16.0, 16.0, 16.0, 16.0],
                        [16.0, 16.0, 16.0, 16.0],
                        [16.0, 16.0, 16.0, 16.0],
                        [16.0, 16.0, 16.0, 65.0],
                    ],  # Q95 = 16.0
                    [
                        [35.0, 35.0, 35.0, 35.0],
                        [35.0, 35.0, 35.0, 35.0],
                        [35.0, 35.0, 35.0, 35.0],
                        [35.0, 35.0, 35.0, 35.0],
                        [35.0, 35.0, 35.0, 35.0],
                        [40.0, 41.0, 42.0, 43.0],
                    ],  # Q95 = 41.85
                ],
                [np.full((6, 4), 0.1), np.full((6, 4), 150.0), np.full((6, 4), 150.0)],
            ),
            (
                # Input Fingerprint: 33 => Case 3
                # The 1st term has the type 3, but with a Q95 equal to 23.73 which
                # is < 30 => it is replaced by 30 when the WindIntensity is computed
                # in BlocksBuilder._compute_periods
                generate_valid_time_v2("2023-01-02", (2, "3h")),
                [
                    [
                        [25.1, 25.1, 16.0, 16.0],
                        [16.0, 16.0, 16.0, 16.0],
                        [16.0, 16.0, 16.0, 16.0],
                        [16.0, 16.0, 16.0, 16.0],
                        [16.0, 16.0, 16.0, 16.0],
                        [16.0, 16.0, 16.0, 16.0],
                    ],
                    [
                        [25.1, 25.1, 25.1, 25.1],
                        [0.1, 0.1, 0.1, 0.1],
                        [0.1, 0.1, 0.1, 0.1],
                        [0.1, 0.1, 0.1, 0.1],
                        [0.1, 0.1, 0.1, 0.1],
                        [0.1, 0.1, 0.1, 0.1],
                    ],
                ],
                [np.full((6, 4), 0.1), np.full((6, 4), 150.0)],
            ),
        ],
    )
    def test_block_builder_grid_6x2(
        self, valid_time, data_wf, data_wd, assert_equals_result
    ):
        # Test resulting WindBlocks built from 6x2 grid data.
        composite = CompositeFactory6x4.get(
            valid_time=valid_time, data_wind=data_wf, data_dir=data_wd
        )

        result: dict = {
            "input": {
                "valid_time": [str(v) for v in valid_time],
                "data_wf": data_wf,
                "data_wd": data_wd,
            }
        }

        result.update(self.build_and_check_wind_blocks(composite))

        assert_equals_result(result)

    @pytest.mark.parametrize(
        "valid_time, data_wf",
        [
            (
                generate_valid_time("2023-01-02", 3),
                [
                    [
                        [1.0, 1.0, 1.0, 1.0],
                        [1.0, 1.0, 1.0, 1.0],
                        [1.0, 1.0, 1.0, 1.0],
                        [1.0, 1.0, 1.0, 1.0],
                        [1.0, 1.0, 1.0, 1.0],
                        [1.0, 1.0, 1.0, 65.0],
                    ],
                    [
                        [1.0, 1.0, 1.0, 1.0],
                        [1.0, 1.0, 1.0, 1.0],
                        [1.0, 1.0, 1.0, 1.0],
                        [1.0, 1.0, 1.0, 1.0],
                        [1.0, 1.0, 1.0, 1.0],
                        [1.0, 30.0, 35.0, 60.0],
                    ],  # Q95 of filtered data is 57.5
                    [
                        [1.0, 1.0, 1.0, 1.0],
                        [1.0, 1.0, 1.0, 1.0],
                        [1.0, 1.0, 1.0, 1.0],
                        [1.0, 1.0, 1.0, 1.0],
                        [1.0, 1.0, 1.0, 1.0],
                        [1.0, 30.0, 35.0, 37.0],
                    ],  # Q95 of filtered data is 36.8
                ],
            )
        ],
    )
    def test_block_builder_q95_max_6x4(self, valid_time, data_wf):
        # Test resulting WindBlocks built from 6x2 grid data.
        composite = CompositeFactory6x4.get(valid_time=valid_time, data_wind=data_wf)

        summary_builder: WindSummaryBuilder
        summary_builder = self._create_summary_builder_from_composite(composite)
        self._run_case3_from_summary_builder(summary_builder)

        # Test wind_q95 values
        dataset: xr.Dataset = summary_builder.dataset
        np.array_equal(
            dataset.wind_q95.values, np.array([np.nan, 57.5, 36.8]), equal_nan=True
        )

        # Test the value of the wind_q95_max's attribute
        assert dataset.attrs["wind_q95_max"] == 57.5

    def check_block_builder_with_attenuation_grid_1x1(
        self, valid_time, data_wf, block_cnt, assert_equals_result
    ):
        # Test resulting WindBlocks built from 1x1 grid data.
        composite = CompositeFactory1x1.get_composite_when_term_data_is_one_number(
            valid_time=valid_time, data_wind=data_wf
        )

        summary_builder: WindSummaryBuilder

        with patch(
            "mfire.text.synthesis.wind_reducers.wind.WindSummaryBuilder."
            "WF_PERCENTILE_NUM",
            50,
        ):
            summary_builder = self._create_summary_builder_from_composite(composite)
            case3_summary_builder: Case3SummaryBuilder
            case3_summary_builder = self._run_case3_from_summary_builder(
                summary_builder
            )
        block_summary_builder: BlockSummaryBuilder
        block_summary_builder = case3_summary_builder.block_summary_builder

        # Check block number
        assert len(case3_summary_builder.blocks_builder.blocks) == block_cnt

        result: dict = {
            "input": {"valid_time": [str(v) for v in valid_time], "data_wf": data_wf},
            "output": {
                "pci": [str(p) for p in block_summary_builder.pci],
                "pcd": [str(p) for p in block_summary_builder.pcd],
                "counters": case3_summary_builder.block_summary_builder.counters,
                "wi_describers": block_summary_builder._wind_intensities_describer(
                    summary_builder.dataset
                ),
                "summary": case3_summary_builder.summary,
            },
        }

        assert_equals_result(result)

    @pytest.mark.parametrize("valid_time, data_wf", TEST_CASE3_WI_ATTENUATION_1_BLOCK)
    def test_block_builder_with_attenuation_1_block(
        self, valid_time, data_wf, assert_equals_result
    ):
        # Test resulting WindBlocks built from 1x1 grid data.
        self.check_block_builder_with_attenuation_grid_1x1(
            valid_time, data_wf, 1, assert_equals_result
        )

    @pytest.mark.parametrize("valid_time, data_wf", TEST_CASE3_WI_ATTENUATION_2_BLOCKS)
    def test_block_builder_with_attenuation_2_blocks(
        self, valid_time, data_wf, assert_equals_result
    ):
        # Test resulting WindBlocks built from 1x1 grid datA.
        self.check_block_builder_with_attenuation_grid_1x1(
            valid_time, data_wf, 2, assert_equals_result
        )

    @pytest.mark.parametrize(
        "valid_time, data_wf, data_wd",
        [
            (
                # Input Fingerprint: 111111222222222222222222 => no type 3 terms
                generate_valid_time(periods=24),
                [10.0] * 6 + [15.0] * 18,
                [np.nan] * 24,
            )
        ],
    )
    def test_summary_builder_error(self, valid_time, data_wf, data_wd):
        reference_datetime: Datetime = Datetime(datetime.now())
        composite = CompositeFactory1x1.get_composite_when_term_data_is_one_number(
            valid_time=valid_time, data_wind=data_wf, data_dir=data_wd
        )
        summary_builder = self._create_summary_builder_from_composite(composite)

        case3_summary_builder: Case3SummaryBuilder = Case3SummaryBuilder(
            parent=BaseCompositeFactory()
        )

        with pytest.raises(WindSynthesisError):
            case3_summary_builder.run(summary_builder.dataset, reference_datetime)


class TestGenerateSummaryError:
    class CompositeFactory(CompositeFactory2x2):
        LON = [30, 31]
        LAT = [40, 41]

    def get_summary(self, wind_summary_builder_class) -> dict:
        valid_time = generate_valid_time(periods=1)

        composite = self.CompositeFactory().get(
            valid_time=valid_time, data_wind=np.full((2, 2), 15.0)
        )
        dataset = composite.weather_data()
        summary_builder = wind_summary_builder_class(parent=composite, dataset=dataset)
        reference_datetime: Datetime = Datetime(datetime.now())
        summary = summary_builder.compute(reference_datetime)

        return summary

    def test_summary_error(self):
        for error in WindSummaryBuilder.CACHED_EXCEPTIONS:

            class BadWindSummaryBuilder(WindSummaryBuilder):
                def _generate_summary(self, reference_datetime: Datetime) -> None:
                    raise error

            with pytest.raises(error):
                self.get_summary(BadWindSummaryBuilder)
