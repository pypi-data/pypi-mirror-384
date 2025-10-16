from copy import deepcopy

import pytest
import xarray as xr

from mfire.text.synthesis.temperature import TemperatureSummary
from tests.composite.factories import SynthesisModuleFactory
from tests.text.synthesis.factories import (
    TemperatureBuilderFactory,
    TemperatureReducerFactory,
)
from tests.text.utils import generate_valid_time

# ==============================
# Testing a Text SYNTHESIS
# ==============================


class TestTemperatureSummary:
    temperature_one_date = [[[[5, 6]]]]
    one_mask = [[[1, 1]]]

    # First test case : only one date and one descriptive zone
    one_bracket_summary = {
        "high": {
            "location": "Zd1",
            "location_type": "",
            "min": 5,
            "max": 6,
            "overall": "de",
        }
    }
    test_1 = ([[[5, 6], [5, 6]]], [[[1, 1], [1, 1]]], ["Zd1"], one_bracket_summary)

    two_brackets_summary = {
        "high": {
            "location": "Zd1",
            "location_type": "",
            "min": 5,
            "max": 6,
            "overall": "de",
        },
        "low": {
            "location": "Zd2",
            "location_type": "",
            "min": 1,
            "max": 2,
            "overall": "de",
        },
    }
    test_two_brackets = (
        [[[5, 6, 5], [1, 2, 1]]],
        [[[1, 1, 1], [0, 0, 0]], [[0, 0, 0], [1, 1, 1]]],
        ["Zd1", "Zd2"],
        two_brackets_summary,
    )

    # Testing that extreme values are correctly ignored (38, in this case)
    # we assume a valid threshold at 5% of the points as
    # defined by TemperatureSummary.REQUIRED_DENSITY
    test_non_representative_bracket = (
        [
            [
                [
                    [4, 4, 5, 5, 6, 38],
                    [1, 1, 2, 2, 3, 3],
                    [2, 2, 2, 3, 3, 3],
                    [-2, -2, -1, -1, 0, 0],
                ]
            ]
        ],
        [
            [
                [1, 1, 1, 1, 1, 1],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
            ],
            [
                [0, 0, 0, 0, 0, 0],
                [1, 1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1, 1],
                [0, 0, 0, 0, 0, 0],
            ],
            [
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [1, 1, 1, 1, 1, 1],
            ],
        ],
        ["Nord", "Centre", "Sud"],
        generate_valid_time(periods=1),
        two_brackets_summary,
    )

    @pytest.mark.parametrize(
        "temperatures,masks,areaNames,expected_result", [test_1, test_two_brackets]
    )
    def test_summary(
        self, temperatures: list, masks: list, areaNames: list, expected_result
    ):
        # bogus coords based on the temperature size
        lat = list(range(len(temperatures[0])))
        lon = list(range(len(temperatures[0][0])))

        areaTypes = ["" for _ in areaNames]

        masks_da = xr.DataArray(
            masks,
            dims=["id", "latitude", "longitude"],
            coords={
                "id": [f"{1 + i}" for i in range(len(masks))],
                "latitude": lat,
                "longitude": lon,
                "areaType": (["id"], areaTypes),
                "areaName": (["id"], areaNames),
            },
        )

        t_da = xr.DataArray(
            temperatures,
            dims=["id", "latitude", "longitude"],
            coords={"id": ["Tempe"], "latitude": lat, "longitude": lon},
        )

        t_summary = TemperatureSummary(TemperatureReducerFactory(), t_da, masks_da)
        summary = t_summary.generate_reduction()

        assert summary == expected_result

    @pytest.mark.parametrize(
        "text,expected",
        [
            (
                "Températures minimales : -3 °C. Températures maximales : 5 °C.",
                "Températures minimales : -3 °C. Températures maximales : 5 °C.",
            ),
            (
                "Températures minimales : -3 à 5 °C. Températures maximales : 11 à "
                "13 °C.",
                "Températures minimales : -3 à 5 °C. Températures maximales : 11 à "
                "13 °C.",
            ),
            (
                "Températures minimales : -3 à -3 °C sur le sud et 0 à 0 °C dans le "
                "nord.",
                "Températures minimales : -3 °C sur le sud et 0 °C dans le nord.",
            ),
            ("Températures maximales : 5 à 5 °C", "Températures maximales : 5 °C"),
            (" Strasbourg à 5 °C", " Strasbourg à 5 °C"),
        ],
    )
    def test_post_process(self, text, expected):
        # Makes sure the regex correctly catches the two values of an interval
        # (be they positive or negative)
        t = TemperatureBuilderFactory(geo_id="geo_id", text=text)
        t.post_process()

    minimal_summary = {"general": {"tempe": {"unit": "°C", "mini": {}, "maxi": {}}}}

    two_neg_summary = {
        "high": {
            "location": "dans le Nord",
            "location_type": "",
            "min": -3,
            "max": -3,
            "overall": "globalement de ",
        },
        "low": {
            "location": "dans le Sud",
            "location_type": "",
            "min": -9,
            "max": -7,
            "overall": "globalement de ",
        },
    }

    two_pos_summary = {
        "high": {
            "location": "dans le Nord",
            "location_type": "",
            "min": 6,
            "max": 7,
            "overall": "globalement de ",
        },
        "low": {
            "location": "dans le Sud",
            "location_type": "",
            "min": 2,
            "max": 2,
            "overall": "globalement de ",
        },
    }

    summary_one_value_intervals = deepcopy(minimal_summary)
    summary_one_value_intervals["general"]["tempe"]["mini"] = two_neg_summary
    summary_one_value_intervals["general"]["tempe"]["maxi"] = two_pos_summary
    expected_output_one_value_intervals = (
        "Températures minimales : "
        "globalement de -3 °C dans le Nord, au plus bas -9 à -7 °C dans le Sud. "
        "Températures maximales : "
        "globalement de 2 °C dans le Sud, jusqu'à 6 à 7 °C dans le Nord."
    )

    @pytest.mark.parametrize(
        "summary,expected_sentence",
        [(summary_one_value_intervals, expected_output_one_value_intervals)],
    )
    def test_single_value_interval(self, summary, expected_sentence):
        # makes sure both negative and positive interval are properly managed
        t_builder = TemperatureBuilderFactory(reduction_factory=summary)
        assert t_builder.compute() == expected_sentence

    def test_compute_without_condition(self):
        builder = TemperatureBuilderFactory(
            parent=SynthesisModuleFactory(check_condition_factory=lambda _: False)
        )
        assert builder.compute() is None
