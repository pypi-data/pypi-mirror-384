"""Unit tests of wind intensity classes."""

import copy

import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.text.synthesis.wind_reducers.wind.wind_intensity import (
    Pci,
    PciFinder,
    WindIntensity,
)
from mfire.utils.date import Datetime
from tests.composite.factories import BaseCompositeFactory
from tests.text.utils import generate_valid_time, generate_valid_time_v2

from .factories import WindIntensityFactory
from .mixins import Data1x1


class TestWindIntensity:
    @pytest.mark.parametrize(
        "force", [25.0, 34.9, 35.0, 49.9, 50.0, 69.9, 70.0, 80.0, 90.0]
    )
    def test_creation(self, force, assert_equals_result):
        wi = WindIntensityFactory(force)

        result: dict = {
            "force": force,
            "wi_interval": str(wi.interval),
            "wi_as_text": wi.as_text(),
        }

        # Check text
        assert_equals_result(result)

    @pytest.mark.parametrize("force", [25.0, 34.9, 35.0, 49.9])
    def test_creation_with_attenuation(self, force, assert_equals_result):
        wi = WindIntensityFactory(force)

        result: dict = {
            "force": force,
            "wi_interval": str(wi.interval),
            "wi_as_text": {
                describer: wi.as_text(describer)
                for describer in ["attenuate_with_prefix", "attenuate_by_replacement"]
            },
        }

        # Check text
        assert_equals_result(result)

    @pytest.mark.parametrize("force", [0.0, 14.0, 24.9])
    def test_creation_exception(self, force):
        with pytest.raises(ValueError):
            WindIntensityFactory(force)

    @pytest.mark.parametrize("force", [50.0, 70.0, 100.9])
    def test_text_with_attenuation_exception(self, force):
        wi: WindIntensity = WindIntensityFactory(force)
        for context in ["attenuate_with_prefix", "attenuate_by_replacement"]:
            with pytest.raises(KeyError):
                _ = wi.as_text(context)

    @pytest.mark.parametrize(
        "f0, f1, expected",
        [
            (25, 35, True),
            (34.9, 35, True),
            (35, 25, True),
            (40, 60, True),
            (60, 39, True),
            (60, 75, True),
            (75, 60, True),
            (25, 50, False),
            (50, 25, False),
            (40, 75, False),
            (75, 40, False),
            (30, 70, False),
        ],
    )
    def test_is_juxtaposed_with(self, f0, f1, expected):
        wi_0 = WindIntensityFactory(f0)
        wi_1 = WindIntensityFactory(f1)
        assert wi_0.is_juxtaposed_with(wi_1) == expected

    @pytest.mark.parametrize(
        "force, expected",
        [
            (25, True),
            (34.9, True),
            (35.0, True),
            (49.999, True),
            (50, False),
            (70, False),
            (100, False),
        ],
    )
    def test_has_attenuable_interval(self, force, expected):
        wi = WindIntensityFactory(force)
        assert wi.has_attenuable_interval() == expected

    def test_speed_min(self):
        assert WindIntensityFactory(35).speed_min == 25.0
        assert WindIntensityFactory(70.0).speed_min == 25.0

    def test_comparison(self):
        assert WindIntensityFactory(25.0) == WindIntensityFactory(34.9)
        assert WindIntensityFactory(35.0) == WindIntensityFactory(49.9)
        assert WindIntensityFactory(50.0) == WindIntensityFactory(69.9)
        assert WindIntensityFactory(70.2) == WindIntensityFactory(90.8)

        assert WindIntensityFactory(30.0) <= WindIntensityFactory(35.0)
        assert WindIntensityFactory(30.0) <= WindIntensityFactory(40.0)
        assert WindIntensityFactory(60.0) >= WindIntensityFactory(40.0)
        assert WindIntensityFactory(60.0) >= WindIntensityFactory(54.0)

        assert WindIntensityFactory(30.0) < WindIntensityFactory(40.0)
        assert WindIntensityFactory(60.0) > WindIntensityFactory(49.0)
        assert WindIntensityFactory(80.0) > WindIntensityFactory(67.6)


class TestPci:
    WIND_INTENSITY = WindIntensityFactory(37.0)
    WIND_PCI = Pci(
        begin_time=Datetime(2023, 1, 1, 10, 0, 0),
        end_time=Datetime(2023, 1, 1, 11, 0, 0),
        wi=WIND_INTENSITY,
    )

    @pytest.mark.parametrize(
        "begin_time, end_time",
        [
            (Datetime(2023, 1, 1, 11, 0, 0), Datetime(2023, 1, 1, 10, 0, 0)),
            (Datetime(2023, 1, 1, 11, 0, 0), Datetime(2023, 1, 1, 11, 59, 59)),
            (Datetime(2023, 1, 1, 11, 0, 0), Datetime(2023, 1, 1, 11, 0, 0)),
        ],
    )
    def test_creation_exception(self, begin_time, end_time):
        with pytest.raises(ValueError):
            Pci(begin_time=begin_time, end_time=end_time, wi=self.WIND_INTENSITY)

    @pytest.mark.parametrize(
        "period, res_exp, period_exp",
        [
            (
                Pci(
                    begin_time=Datetime(2023, 1, 1, 11, 0, 0),
                    end_time=Datetime(2023, 1, 1, 12, 0, 0),
                    wi=WindIntensityFactory(35.0),
                ),
                True,
                Pci(
                    begin_time=Datetime(2023, 1, 1, 10, 0, 0),
                    end_time=Datetime(2023, 1, 1, 12, 0, 0),
                    wi=WIND_INTENSITY,
                ),
            ),
            (
                Pci(
                    begin_time=Datetime(2023, 1, 1, 11, 0, 0),
                    end_time=Datetime(2023, 1, 1, 12, 0, 0),
                    wi=WindIntensityFactory(49.9),
                ),
                True,
                Pci(
                    begin_time=Datetime(2023, 1, 1, 10, 0, 0),
                    end_time=Datetime(2023, 1, 1, 12, 0, 0),
                    wi=WIND_INTENSITY,
                ),
            ),
            (
                Pci(
                    begin_time=Datetime(2023, 1, 1, 9, 0, 0),
                    end_time=Datetime(2023, 1, 1, 10, 0, 0),
                    wi=WindIntensityFactory(36.1),
                ),
                False,
                WIND_PCI,
            ),
            (
                Pci(
                    begin_time=Datetime(2023, 1, 1, 8, 0, 0),
                    end_time=Datetime(2023, 1, 1, 9, 0, 0),
                    wi=WindIntensityFactory(50.0),
                ),
                False,
                WIND_PCI,
            ),
        ],
    )
    def test_update(self, period: Pci, res_exp: bool, period_exp: Pci):
        pci = copy.deepcopy(self.WIND_PCI)
        res = pci.update(period)
        assert res == res_exp
        assert pci == period_exp

    @pytest.mark.parametrize(
        "wi_p1, wi_p2, check_exp",
        [
            (
                Pci(
                    begin_time=Datetime(2023, 1, 1, 0, 0, 0),
                    end_time=Datetime(2023, 1, 1, 4, 0, 0),
                    wi=WindIntensityFactory(25.0),
                ),
                Pci(
                    begin_time=Datetime(2023, 1, 1, 6, 0, 0),
                    end_time=Datetime(2023, 1, 1, 10, 0, 0),
                    wi=WindIntensityFactory(25.0),
                ),
                True,
            ),
            (
                Pci(
                    begin_time=Datetime(2023, 1, 1, 0, 0, 0),
                    end_time=Datetime(2023, 1, 1, 4, 0, 0),
                    wi=WindIntensityFactory(50.0),
                ),
                Pci(
                    begin_time=Datetime(2023, 1, 1, 6, 0, 0),
                    end_time=Datetime(2023, 1, 1, 10, 0, 0),
                    wi=WindIntensityFactory(69.9),
                ),
                True,
            ),
            (
                Pci(
                    begin_time=Datetime(2023, 1, 1, 0, 0, 0),
                    end_time=Datetime(2023, 1, 1, 4, 0, 0),
                    wi=WindIntensityFactory(34.9),
                ),
                Pci(
                    begin_time=Datetime(2023, 1, 1, 6, 0, 0),
                    end_time=Datetime(2023, 1, 1, 10, 0, 0),
                    wi=WindIntensityFactory(51.0),
                ),
                False,
            ),
        ],
    )
    def test_has_same_intensity(self, wi_p1, wi_p2, check_exp):
        assert wi_p1.has_same_intensity_than(wi_p2) == check_exp


class TestPciFinder(Data1x1):
    @pytest.mark.parametrize(
        "data, valid_time, periods_exp",
        [
            (
                [30.0],
                generate_valid_time(periods=1),
                [
                    Pci(
                        begin_time=Datetime(2023, 1, 1, 23, 0, 0),
                        end_time=Datetime(2023, 1, 2, 0, 0, 0),
                        wi=WindIntensityFactory(25.0),
                    )
                ],
            ),
            (
                [25.0, 32.0],
                generate_valid_time(periods=2),
                [
                    Pci(
                        begin_time=Datetime(2023, 1, 1, 23, 0, 0),
                        end_time=Datetime(2023, 1, 2, 1, 0, 0),
                        wi=WindIntensityFactory(25.0),
                    )
                ],
            ),
            (
                [25.0, 35.0, 50.0],
                generate_valid_time(periods=3),
                [
                    Pci(
                        begin_time=Datetime(2023, 1, 1, 23, 0, 0),
                        end_time=Datetime(2023, 1, 2, 0, 0, 0),
                        wi=WindIntensityFactory(25.0),
                    ),
                    Pci(
                        begin_time=Datetime(2023, 1, 2, 0, 0, 0),
                        end_time=Datetime(2023, 1, 2, 1, 0, 0),
                        wi=WindIntensityFactory(35.0),
                    ),
                    Pci(
                        begin_time=Datetime(2023, 1, 2, 1, 0, 0),
                        end_time=Datetime(2023, 1, 2, 2, 0, 0),
                        wi=WindIntensityFactory(50.0),
                    ),
                ],
            ),
            (
                [25.0, 27.6, 36.5, 42.0, 47],
                generate_valid_time(periods=5),
                [
                    Pci(
                        begin_time=Datetime(2023, 1, 1, 23, 0, 0),
                        end_time=Datetime(2023, 1, 2, 1, 0, 0),
                        wi=WindIntensityFactory(25.0),
                    ),
                    Pci(
                        begin_time=Datetime(2023, 1, 2, 1, 0, 0),
                        end_time=Datetime(2023, 1, 2, 4, 0, 0),
                        wi=WindIntensityFactory(35.0),
                    ),
                ],
            ),
            (
                [25.0, 32.6, 43.0],
                generate_valid_time_v2("2023-01-02", (2, "H"), (1, "3H")),
                [
                    Pci(
                        begin_time=Datetime(2023, 1, 1, 23, 0, 0),
                        end_time=Datetime(2023, 1, 2, 1, 0, 0),
                        wi=WindIntensityFactory(25.0),
                    ),
                    Pci(
                        begin_time=Datetime(2023, 1, 2, 1, 0, 0),
                        end_time=Datetime(2023, 1, 2, 4, 0, 0),
                        wi=WindIntensityFactory(35.0),
                    ),
                ],
            ),
            (
                [75.0] * 5,
                generate_valid_time_v2("2023-01-02", (2, "H"), (3, "3H")),
                [
                    Pci(
                        begin_time=Datetime(2023, 1, 1, 23, 0, 0),
                        end_time=Datetime(2023, 1, 2, 10, 0, 0),
                        wi=WindIntensityFactory(70.0),
                    )
                ],
            ),
        ],
    )
    def test_period_finder(self, data, valid_time: list | np.ndarray, periods_exp):
        dataset: xr.Dataset = self._create_dataset(valid_time, data_wind=np.array(data))

        wind_q95: list[float] = []
        for vt in dataset.valid_time:
            dataset_cur: xr.Dataset = dataset.sel(valid_time=vt)
            wind_q95.append(
                round(WindIntensity.data_array_to_value(dataset_cur.wind), 2)
            )

        # Add the `wind_q95` variable
        dataset["wind_q95"] = xr.DataArray(
            data=wind_q95, coords=[dataset.valid_time], dims=["valid_time"]
        )

        period_finder = PciFinder.from_dataset(dataset, parent=BaseCompositeFactory())
        periods = period_finder.run()
        assert periods == periods_exp
