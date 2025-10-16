"""Unit tests of wind direction classes."""

import copy
from typing import Optional
from unittest.mock import patch

import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.text.synthesis.wind_reducers.wind.case3.wind_direction import (
    Pcd,
    PcdFinder,
    WindDirection,
    WindDirection120,
    set_and_check_class_nbr,
    set_and_check_class_size,
)
from mfire.utils.date import Datetime
from tests.text.utils import generate_valid_time, generate_valid_time_v2

from .mixins import Data1x2, Data2x5


class WindDirection180(WindDirection):
    pass


class TestWindDirection:
    @pytest.mark.parametrize(
        "start, angle, end_exp",
        [
            (10.0, 0.0, 10.0),
            (10.0, None, 10.0),
            (370.0, None, 10.0),
            (10.0, 20.0, 30.0),
            (350.0, 20.0, 10.0),
            (0.0, 179.9, 179.9),
            (350.0, 179.9, 169.9),
        ],
    )
    def test_creation_ok(self, start: float, angle: Optional[float], end_exp: float):
        wd: WindDirection

        if angle is None:
            wd = WindDirection(start)
        else:
            wd = WindDirection(start, angle)

        assert wd is not None
        np.testing.assert_allclose(wd.end, end_exp)

    @pytest.mark.parametrize("start, angle", [(0.0, 180.0), (350.0, 180.0)])
    def test_creation_nok(self, start: float, angle: Optional[float]):
        assert WindDirection.try_to_create(start, angle) is None

    @pytest.mark.parametrize(
        "wd1_args, wd2_args, wd_args_exp",
        [
            # Origin not in both dirs
            ((10.0, 20.0), (40.0, 20.0), (10.0, 50.0)),
            ((10.0, 20.0), (170.0, 19.9), (10.0, 179.9)),
            ((10.0, 10.0), (208.0, 2.0), (208.0, 172.0)),
            # Origin only in the 1st dir
            ((350.0, 20.0), (210.0, 10.0), (210.0, 160.0)),
            ((350.0, 20.0), (90.0, 20.0), (350.0, 120.0)),
            # Origin only in the 2nd dir
            ((210.0, 10.0), (350.0, 20.0), (210.0, 160.0)),
            # Origin in the 2 dirs without inclusion
            ((340.0, 30.0), (350.0, 40.0), (340.0, 50.0)),
            # Origin in the 2 dirs and dir 2 is included in the dir 1
            ((340.0, 40.0), (350.0, 20.0), (340.0, 40.0)),
            ((340.0, 40.0), (350.0, 10.0), (340.0, 40.0)),
            # Play around 0 = 360° (mod 360)
            ((0.0, 20.0), (30.0, 10.0), (0.0, 40.0)),
            ((0.0, 20.0), (350.0, 0.0), (350.0, 30.0)),
            # dir include in the other
            ((10.0, 50.0), (10.0, 20.0), (10.0, 50.0)),
            ((10.0, 50.0), (20.0, 20.0), (10.0, 50.0)),
            ((340.0, 50.0), (350.0, 10.0), (340.0, 50.0)),
            ((340.0, 50.0), (0.0, 20.0), (340.0, 50.0)),
            ((340.0, 50.0), (10.0, 20.0), (340.0, 50.0)),
            # not disjointed directions
            ((10.0, 40.0), (30.0, 40.0), (10.0, 60.0)),
            ((340.0, 15.0), (350.0, 40.0), (340.0, 50.0)),
        ],
    )
    def test_sum_ok(self, wd1_args, wd2_args, wd_args_exp):
        # Test the sum of 2 dirs. It tests the sum associativity.
        wd1: WindDirection = WindDirection(*wd1_args)
        wd2: WindDirection = WindDirection(*wd2_args)
        wd_exp = WindDirection(*wd_args_exp)

        for wd in [wd1 + wd2, wd2 + wd1]:
            assert wd.compare(wd_exp)
            assert wd == wd_exp

    @pytest.mark.parametrize(
        "wd1_args, wd2_args",
        [
            ((10.0, 20.0), (170.0, 20.0)),
            ((350.0, 20.0), (170.0, 20.0)),
            ((350.0, 20.0), (170.0, 20.0)),
            ((350.0, 20.0), (170.0, 10.0)),
        ],
    )
    def test_sum_nok(self, wd1_args, wd2_args):
        a1: WindDirection = WindDirection(*wd1_args)
        a2: WindDirection = WindDirection(*wd2_args)
        assert a1 + a2 is None
        assert a2 + a1 is None

    @pytest.mark.parametrize(
        "args, code, text",
        [
            ((45.0, 0.0), 1, "Nord-Est"),
            ((90.0, 0.0), 2, "Est"),
            ((135.0, 0.0), 3, "Sud-Est"),
            ((180.0, 0.0), 4, "Sud"),
            ((225.0, 0.0), 5, "Sud-Ouest"),
            ((270.0, 0.0), 6, "Ouest"),
            ((315.0, 0.0), 7, "Nord-Ouest"),
            ((0.0, 0.0), 0, "Nord"),
            ((360.0, 0.0), 0, "Nord"),
            ((355.0, 4.0), 0, "Nord"),
            ((355.0, 5.0), 0, "Nord"),
            ((355.0, 6.0), 0, "Nord"),
            ((66.9, 1), 1, "Nord-Est"),  # Middle = 66.4
            ((67.0, 1), 1, "Nord-Est"),  # Middle = 66.5
            ((67.1, 1), 2, "Est"),  # Middle = 66.6
        ],
    )
    def test_code(self, args, code, text):
        d = WindDirection(*args)
        assert d.code == code
        assert d.as_text == text

    def test_normalize(self):
        wd: WindDirection = WindDirection(80.0, 20.0)

        def check_normalization(d_to_check):
            assert d_to_check.start == d_to_check.end == 90.0
            assert d_to_check.angle == 0.0

        # Normalize not inplace
        d_normalized: WindDirection = wd.normalize(inplace=False)
        check_normalization(d_normalized)
        assert wd.start == 80.0
        assert wd.end == 100.0
        assert wd.angle == 20.0

        # Normalize inplace
        d_normalized = wd.normalize()
        check_normalization(d_normalized)
        check_normalization(wd)

    @pytest.mark.parametrize(
        "arg_1, arg_2",
        [
            ((45.0, 0.0), (46.0, 5)),
            ((350, 10), (355, 5)),
            ((45.0, 134.9), (90.0, 0.0)),
            ((45.0, 135.0), (90.0, 0.0)),
            ((45.0, 135.1), (135.0, 0.0)),
        ],
    )
    def test_equality(self, arg_1, arg_2):
        assert WindDirection(*arg_1) == WindDirection(*arg_2)

    @pytest.mark.parametrize(
        "arg_1, arg_2, res",
        [
            ((0.0, 0.0), (180.0, 0.0), True),
            ((350.0, 15.0), (179.0, 5.0), True),
            ((45.0, 0.0), (225.0, 0.0), True),
            ((80.0, 15.0), (271.0, 2.0), True),
            ((130.0, 15.0), (271.0, 2.0), False),
            ((130.0, 15.0), (130.0, 15.0), False),
            ((130.0, 15.0), (130.0, 5.0), False),
        ],
    )
    def test_is_opposite_to(self, arg_1, arg_2, res):
        d1 = WindDirection(*arg_1)
        d2 = WindDirection(*arg_2)
        assert d1.is_opposite_to(d2) == res
        assert d2.is_opposite_to(d1) == res

    def test_angle_max_180(self):
        assert WindDirection180.try_to_create(10, 179.0) is not None
        assert WindDirection180.try_to_create(10, 180.0) is None

        with pytest.raises(ValueError):
            WindDirection180(10, 180.0)

    def test_angle_max_120(self):
        assert WindDirection120.try_to_create(10, 120.0) is not None
        assert WindDirection120.try_to_create(10, 120.1) is None
        assert WindDirection120.try_to_create(10, 180.0) is None

        with pytest.raises(ValueError):
            WindDirection120(10, 120.1)


class TestPcd:
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
            Pcd(begin_time=begin_time, end_time=end_time, wd=WindDirection(10.0))

    @staticmethod
    def check_update_method(p1: Pcd, p2: Pcd, res_exp: bool, period_exp: Pcd):
        p1_copy = copy.deepcopy(p1)
        res = p1_copy.update(p2)
        assert res == res_exp
        assert p1_copy == period_exp


class TestPcd120(TestPcd):
    WIND_DIRECTION_120 = WindDirection120(10.0, 40.0)
    PCD_120 = Pcd(
        begin_time=Datetime(2023, 1, 1, 10, 0, 0),
        end_time=Datetime(2023, 1, 1, 11, 0, 0),
        wd=WIND_DIRECTION_120,
    )
    ANGLE_MAX: float = WindDirection120.ANGLE_MAX

    @pytest.mark.parametrize(
        "period, res_exp, period_exp",
        [
            # Updating angle with a result < ANGLE_MAX
            (
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 11, 0, 0),
                    end_time=Datetime(2023, 1, 1, 12, 0, 0),
                    wd=WindDirection120(20.0, ANGLE_MAX - 10.0 - 0.1),
                ),
                True,
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 10, 0, 0),
                    end_time=Datetime(2023, 1, 1, 12, 0, 0),
                    wd=WindDirection120(10.0, ANGLE_MAX - 0.1),
                ),
            ),
            # Updating angle with a result = ANGLE_MAX
            (
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 11, 0, 0),
                    end_time=Datetime(2023, 1, 1, 12, 0, 0),
                    wd=WindDirection120(20.0, ANGLE_MAX - 10.0),
                ),
                True,
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 10, 0, 0),
                    end_time=Datetime(2023, 1, 1, 12, 0, 0),
                    wd=WindDirection120(10.0, ANGLE_MAX),
                ),
            ),
            # Updating a period with an earlier period
            (
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 9, 0, 0),
                    end_time=Datetime(2023, 1, 1, 11, 0, 0),
                    wd=WindDirection120(20.0, ANGLE_MAX - 10.0),
                ),
                False,
                PCD_120,
            ),
            # Updating angle with a result > ANGLE_MAX
            (
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 9, 0, 0),
                    end_time=Datetime(2023, 1, 1, 11, 0, 0),
                    wd=WindDirection120(20.0, ANGLE_MAX - 10.0 + 0.1),
                ),
                False,
                PCD_120,
            ),
            # Updating angle with a result > ANGLE_MAX
            (
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 11, 0, 0),
                    end_time=Datetime(2023, 1, 1, 12, 0, 0),
                    wd=WindDirection120(20.0, ANGLE_MAX - 10.0 + 0.1),
                ),
                False,
                PCD_120,
            ),
            # The sum of angles is None
            (
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 11, 0, 0),
                    end_time=Datetime(2023, 1, 1, 12, 0, 0),
                    wd=WindDirection120(210.0),
                ),
                False,
                PCD_120,
            ),
            # The sum of angles is None
            (
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 11, 0, 0),
                    end_time=Datetime(2023, 1, 1, 12, 0, 0),
                    wd=WindDirection120(210.0, 20.0),
                ),
                False,
                PCD_120,
            ),
        ],
    )
    def test_update(self, period: Pcd, res_exp: bool, period_exp: Pcd):
        self.check_update_method(self.PCD_120, period, res_exp, period_exp)

    def test_addition_exception(self):
        period = Pcd(
            begin_time=Datetime(2023, 1, 1, 14, 0, 0),
            end_time=Datetime(2023, 1, 1, 15, 0, 0),
            wd=self.PCD_120.wd,
        )

        with pytest.raises(ValueError):
            _ = period + self.PCD_120

    @pytest.mark.parametrize(
        "period, res_exp",
        [
            (
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 12, 0, 0),
                    end_time=Datetime(2023, 1, 1, 13, 0, 0),
                    wd=WindDirection120(110.0, 20.0),
                ),
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 10, 0, 0),
                    end_time=Datetime(2023, 1, 1, 13, 0, 0),
                    wd=WindDirection120(10.0, 120.0),
                ),
            ),
            (
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 12, 0, 0),
                    end_time=Datetime(2023, 1, 1, 13, 0, 0),
                    wd=WindDirection120(110.0, 20.1),
                ),
                None,
            ),
        ],
    )
    def test_addition(self, period, res_exp):
        assert self.PCD_120 + period == res_exp

    def test_normalize(self):
        pcd = Pcd(
            begin_time=Datetime(2023, 1, 1, 10, 0, 0),
            end_time=Datetime(2023, 1, 1, 11, 0, 0),
            wd=WindDirection(80.0, 20.0),
        )

        def check_normalization(pcd_to_check):
            wd: WindDirection = pcd_to_check.wd
            assert wd.start == wd.end == 90.0
            assert wd.angle == 0.0

        pcd.normalize_wd()
        check_normalization(pcd)


class TestPcd180(TestPcd):
    WIND_DIRECTION_180 = WindDirection180(10.0, 40.0)
    PCD_180 = Pcd(
        begin_time=Datetime(2023, 1, 1, 10, 0, 0),
        end_time=Datetime(2023, 1, 1, 11, 0, 0),
        wd=WIND_DIRECTION_180,
    )

    @pytest.mark.parametrize(
        "period, res_exp, period_exp",
        [
            # Updating angle with a result < 180.0
            (
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 11, 0, 0),
                    end_time=Datetime(2023, 1, 1, 12, 0, 0),
                    wd=WindDirection180(20.0, 180.0 - 10.0 - 0.1),
                ),
                True,
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 10, 0, 0),
                    end_time=Datetime(2023, 1, 1, 12, 0, 0),
                    wd=WindDirection180(10.0, 180.0 - 0.1),
                ),
            ),
            # Updating angle with a result = 180.0
            (
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 11, 0, 0),
                    end_time=Datetime(2023, 1, 1, 12, 0, 0),
                    wd=WindDirection180(20.0, 180.0 - 10.0),
                ),
                False,
                PCD_180,
            ),
            # Updating angle with a result > 180.0
            (
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 11, 0, 0),
                    end_time=Datetime(2023, 1, 1, 12, 0, 0),
                    wd=WindDirection180(20.0, 180.1 - 10.0),
                ),
                False,
                PCD_180,
            ),
        ],
    )
    def test_update(self, period: Pcd, res_exp: bool, period_exp: Pcd):
        self.check_update_method(self.PCD_180, period, res_exp, period_exp)

    @pytest.mark.parametrize(
        "period, res_exp",
        [
            (
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 12, 0, 0),
                    end_time=Datetime(2023, 1, 1, 13, 0, 0),
                    wd=WindDirection180(170.0, 19.9),
                ),
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 10, 0, 0),
                    end_time=Datetime(2023, 1, 1, 13, 0, 0),
                    wd=WindDirection180(10.0, 179.9),
                ),
            ),
            (
                Pcd(
                    begin_time=Datetime(2023, 1, 1, 12, 0, 0),
                    end_time=Datetime(2023, 1, 1, 13, 0, 0),
                    wd=WindDirection180(170.0, 20.0),
                ),
                None,
            ),
        ],
    )
    def test_addition(self, period, res_exp):
        assert self.PCD_180 + period == res_exp


class TestPcdFinder2x5(Data2x5):
    """Test PcdFinder with 2x5 data."""

    SIZE_MAX = PcdFinder.WIND_DIRECTION_CLASS.ANGLE_MAX
    WIND_DIRECTION_CLASS = PcdFinder.WIND_DIRECTION_CLASS
    CLASS_SIZE = PcdFinder.CLASS_SIZE

    @pytest.mark.parametrize(
        "data, c_max_exp",
        [
            # Case where there are 2 c_max but the sum of those has an angle > 120°
            (
                [
                    [
                        [0.1, 20.0, 39.0, 141.0, 160.0],
                        [178.0, 291.0, 310.0, 329.0, np.nan],
                    ]
                ],
                None,
            )
        ],
    )
    def test_get_term_period(self, data, c_max_exp):
        # Get the term period of a dataset with which contains only one term.
        previous_time = generate_valid_time(start="2023-01-01 23:00:00", periods=1)
        valid_time = generate_valid_time(periods=1)

        dataset: xr.Dataset = self._create_dataset(
            valid_time, data_direction=np.array(data)
        )

        term_period = PcdFinder._get_term_period(dataset.sel(valid_time=valid_time[0]))

        if c_max_exp is None:
            assert term_period is None
        else:
            term_period_exp = Pcd(
                begin_time=Datetime(previous_time[0]),
                end_time=Datetime(valid_time[0]),
                wd=self.WIND_DIRECTION_CLASS(*c_max_exp),
            )
            assert term_period == term_period_exp
            assert term_period.wd.compare(term_period_exp.wd)

    @pytest.mark.parametrize(
        "data, c_max_exp",
        [
            # 50 % of points are in the class C_0 = [0, CLASS_SIZE] => C_max = C_0
            # => term period found: WindDirection(0, CLASS_SIZE)
            (
                [
                    [
                        [0.0, 0.0, 0.0, 0.0, CLASS_SIZE],
                        [np.nan, np.nan, np.nan, np.nan, np.nan],
                    ]
                ],
                (0, CLASS_SIZE),
            ),
            # 50 % of points are in the class C_0 = [0, CLASS_SIZE] => C_max = C_0
            # => term period found: WindDirection(0, CLASS_SIZE)
            (
                [
                    [
                        [360.0, 0.0, 0.0, 0.0, CLASS_SIZE],
                        [np.nan, np.nan, np.nan, np.nan, np.nan],
                    ]
                ],
                (0, CLASS_SIZE),
            ),
            # 50 % of points are in the class C_0 = [360 - CLASS_SIZE, 0] which is then
            # C_max => term period found: WindDirection(360 - CLASS_SIZE, CLASS_SIZE)
            (
                [
                    [
                        [360.0, 360.0, 360.0, 360.0 - CLASS_SIZE, 360.0 - CLASS_SIZE],
                        [np.nan, np.nan, np.nan, np.nan, np.nan],
                    ]
                ],
                (360.0 - CLASS_SIZE, CLASS_SIZE),
            ),
            # only 40 % of points are in the class C_0 = [360 - CLASS_SIZE, 0]
            # => term period found: None
            (
                [
                    [
                        [360.0, 360.0, 360.0, 360.0 - CLASS_SIZE, np.nan],
                        [np.nan, np.nan, np.nan, np.nan, np.nan],
                    ]
                ],
                None,
            ),
            # 40 % of points are in the class C_0 = [0, CLASS_SIZE]
            # => term period found: None
            (
                [
                    [
                        [0.0, 0.0, 0.0, CLASS_SIZE, np.nan],
                        [np.nan, np.nan, np.nan, np.nan, np.nan],
                    ]
                ],
                None,
            ),
            # 60 % of points are in the class C_0 = [0, CLASS_SIZE] => C_max = C_0
            # => term period found: WindDirection(0, CLASS_SIZE)
            (
                [
                    [
                        [0.0, 0.0, 0.0, 0.0, CLASS_SIZE],
                        [np.nan, 70.0, 70.0, np.nan, 70.0],
                    ]
                ],
                (0, CLASS_SIZE),
            ),
            # not enough points in C_0 and C_6
            # => term period found: None
            (
                [[[0.0, 0.0, 0.0, 0.0, np.nan], [np.nan, 70.0, 70.0, np.nan, 70.0]]],
                None,
            ),
            # 50 % of points are in the class [350, CLASS_SIZE - 10] which is then C_max
            (
                [
                    [
                        [350.0, 360.0, CLASS_SIZE - 10, CLASS_SIZE - 10, 0.0],
                        [np.nan, 70.0, 70.0, np.nan, np.nan],
                    ]
                ],
                (360 - 10, CLASS_SIZE),
            ),
            # Only 40 % of points are in the class C_35 = [350, CLASS_SIZE - 10]
            # > term period found: None
            (
                [
                    [
                        [350.0, 360.0, CLASS_SIZE - 10, CLASS_SIZE - 10, np.nan],
                        [np.nan, 70.0, 70.0, np.nan, np.nan],
                    ]
                ],
                None,
            ),
            # 3 C_max classes contains the same number of points: (350, 40), (0, 40)
            # and (10, 40) => (350, 60) has an angle of 60 which is <= 120
            # => term period found: WindDirection(350, 60)
            ([[[10.0] * 3 + [30.0] * 2, [np.nan] * 5]], (350, 60)),
            # Case where there are 2 c_max:
            # counters_list: [(40.0, 5), (50.0, 6), (60.0, 6), (70.0, 5)]
            # c_max_list: [(50.0, 6), (60.0, 6)]
            # => term period found: WindDirection(50, 50)
            (
                [
                    [
                        [50.0, 60.0, 70.0, 80.0, 90.0],
                        [100.0, 50.0, 100.0, np.nan, np.nan],
                    ]
                ],
                (50, 50),
            ),
        ],
    )
    @patch(
        "mfire.text.synthesis.wind_reducers.wind.case3.wind_direction."
        "PcdFinder.CLASS_PERCENT_MIN",
        50.0,
    )
    def test_get_term_period_percent_min_50(self, data, c_max_exp):
        # Get the term period of a dataset with which contains only one term.

        # PcdFinder.CLASS_PERCENT_MIN is mocked to 50 instead of the normal
        # value 20.
        self.test_get_term_period(data, c_max_exp)


class TestPcdFinderAttributes:
    """Test class attributes class_size and class_nb initialization."""

    def test_classes_size(self):
        with pytest.raises(ValueError):
            set_and_check_class_size(30.1)

    def test_classes_nbr(self):
        with pytest.raises(ValueError):
            set_and_check_class_nbr(30.1)

        assert set_and_check_class_nbr(10.0) == 36.0


class TestPcdFinder1x2(Data1x2):
    """Test PcdFinder with 1x2 data."""

    SIZE_MAX = PcdFinder.WIND_DIRECTION_CLASS.ANGLE_MAX
    WIND_DIRECTION_CLASS = PcdFinder.WIND_DIRECTION_CLASS
    CLASS_SIZE = PcdFinder.CLASS_SIZE

    @pytest.mark.parametrize(
        "data, valid_time",
        [
            # No direction for all terms => no PCD found
            (
                [[[np.nan, np.nan]], [[np.nan, np.nan]], [[np.nan, np.nan]]],
                generate_valid_time(periods=3),
            ),
            # All 3 terms have the same c_max => 1 PCD
            (
                [[[0.0, CLASS_SIZE]], [[0.0, CLASS_SIZE]], [[360.0, CLASS_SIZE]]],
                generate_valid_time(periods=3),
            ),
            # => 60 % of monitoring period are covered by a 3-hours PCD
            # => 1 PCD
            (
                [
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[0.0, CLASS_SIZE]],
                ],
                generate_valid_time(periods=5),
            ),
            # The sum of the c_max has the (0, 120) angle
            # => 1 PCD with c_max direction
            (
                [
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [
                        [
                            WIND_DIRECTION_CLASS.ANGLE_MAX - CLASS_SIZE,
                            WIND_DIRECTION_CLASS.ANGLE_MAX,
                        ]
                    ],
                ],
                generate_valid_time(periods=3),
            ),
            # The sum of the c_max has the (350, 110) angle
            # => 1 PCD with c_max direction
            (
                [
                    [[350.0, CLASS_SIZE - 10.0]],
                    [[0.0, CLASS_SIZE]],
                    [
                        [
                            WIND_DIRECTION_CLASS.ANGLE_MAX - CLASS_SIZE - 10.0,
                            WIND_DIRECTION_CLASS.ANGLE_MAX - 10.0,
                        ]
                    ],
                ],
                generate_valid_time(periods=3),
            ),
            # The sum of the c_max has the (0, 130) angle with is > 120
            # => no PCD
            (
                [
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [
                        [
                            WIND_DIRECTION_CLASS.ANGLE_MAX - CLASS_SIZE + 10.0,
                            WIND_DIRECTION_CLASS.ANGLE_MAX + 10.0,
                        ]
                    ],
                ],
                generate_valid_time(periods=3),
            ),
            # One 1-hours PCD < 3h
            # => no PCD
            ([[[0.0, CLASS_SIZE]]], generate_valid_time(periods=1)),
            # One 2-hours PCD < 3h
            # => no PCD
            (
                [[[0.0, CLASS_SIZE]], [[0.0, CLASS_SIZE]]],
                generate_valid_time(periods=2),
            ),
            # One 1-hour PCD < 3h
            # => no Pcd
            (
                [
                    [[0.0, CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                ],
                generate_valid_time(periods=4),
            ),
            # One 2-hours PCD < 3h
            # => no Pcd
            (
                [
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                ],
                generate_valid_time(periods=4),
            ),
            # 50 % of the monitoring period are covered by a 3-hours PCD
            # => 1 PCD
            (
                [
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                ],
                generate_valid_time(periods=6),
            ),
            # 50 % of the monitoring period are covered by a 4-hours PCD
            # => 1 PCD
            (
                [
                    [[np.nan, np.nan]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                ],
                generate_valid_time(periods=8),
            ),
            # The period starting from the 1st long enough PCD and finishing by the last
            # long enough PCD is 50 % of the monitoring period
            # => 2 PCD
            (
                [
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                ],
                generate_valid_time(periods=14),
            ),
            # 75 % of the monitoring period are covered by a 3-hours PCD
            # => 1 PCD
            (
                [
                    [[np.nan, np.nan]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                ],
                generate_valid_time(periods=4),
            ),
            # 75% of the monitoring period are covered by a 3-hours PCD
            # => 1 PCD
            (
                [
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[np.nan, np.nan]],
                ],
                generate_valid_time(periods=4),
            ),
            # All PCD are < 3h
            # => no Pcd
            (
                [
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[0.0, CLASS_SIZE]],
                ],
                generate_valid_time(periods=4),
            ),
            # first 3 terms -> 1 PCD with (0, 40) angle
            # last 3 terms -> 1 PCD with (90, 130) angle
            # 100 % of the monitoring period are covered by a long enough PCD
            # => 2 Pcd
            (
                [
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                ],
                generate_valid_time(periods=8),
            ),
            # first 3 terms -> 1 period with (0, 40) angle
            # last 3 terms -> 1 period with (0, 40) angle
            # 100 % of the monitoring period are covered by a long enough PCD
            # => the 2 PCD has the same direction
            # => they are merged to 1 PCD
            # => 1 PCD
            (
                [
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                ],
                generate_valid_time(periods=8),
            ),
            # first 3 terms -> 1 period with (0, 40) angle
            # last 3 terms -> 1 period with (180, 40) angle
            # 100 % of the monitoring period are covered by a long enough PCD
            # But the 1st and the last PCD are periods are opposite
            # => no Pcd
            (
                [
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[180.0, 180.0 + CLASS_SIZE]],
                    [[180.0, 180.0 + CLASS_SIZE]],
                    [[180.0, 180.0 + CLASS_SIZE]],
                ],
                generate_valid_time(periods=8),
            ),
            # first 3 terms -> 1 period with (0, 40) angle
            # last 3 terms -> 1 period with (180, 40) angle
            # 100 % of the monitoring period are covered by a long enough PCD
            # But the 1st and the last PCD are periods are opposite
            # => no Pcd
            (
                [
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[180.0, 180.0 + CLASS_SIZE]],
                    [[180.0, 180.0 + CLASS_SIZE]],
                    [[180.0, 180.0 + CLASS_SIZE]],
                ],
                generate_valid_time(periods=6),
            ),
            # 66.7 % of the monitoring period are covered by a 3-hours PCD
            # => 1 Pcd
            (
                [
                    [[0.0, CLASS_SIZE]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                ],
                generate_valid_time(periods=4),
            ),
            # 66.7 % of the monitoring period are covered by a 3-hours PCD
            # => 1 Pcd
            (
                [
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                ],
                generate_valid_time(periods=4),
            ),
            # 1 PCD 4-hours PCD with (0, 40) angle
            # 1 3-hours PCD with (180, 40) angle
            # => 2 Pcd
            (
                [
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[100.0, 100.0 + CLASS_SIZE]],
                ],
                generate_valid_time_v2("2023-01-02", (2, "2H"), (1, "3H")),
            ),
            # 1 PCD 4-hours PCD with (0, 40) angle
            # => 1 Pcd
            (
                [[[0.0, CLASS_SIZE]], [[0.0, CLASS_SIZE]]],
                generate_valid_time(periods=2, freq="2H"),
            ),
            # The period starting from the 1st long enough PCD and finishing by the last
            # long enough PCD is 46 % of the monitoring period
            # => 0 PCD
            (
                [
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                ],
                generate_valid_time(periods=15),
            ),
            # The period starting from the 1st long enough PCD and finishing by the last
            # long enough PCD is 50 % of the monitoring period
            # => 2 PCD
            (
                [
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                ],
                generate_valid_time(periods=20),
            ),
            # Case with 3 long enough PDC
            # => 2 PCD (he 1rst and the last)
            (
                [
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[0.0, CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[90.0, 90.0 + CLASS_SIZE]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[np.nan, np.nan]],
                    [[40.0, 40.0 + CLASS_SIZE]],
                    [[40.0, 40.0 + CLASS_SIZE]],
                    [[40.0, 40.0 + CLASS_SIZE]],
                ],
                generate_valid_time(periods=20),
            ),
        ],
    )
    def test_period_finder(
        self, data: list, valid_time: list | np.ndarray, assert_equals_result
    ):
        dataset: xr.Dataset = self._create_dataset(
            valid_time, data_direction=np.array(data)
        )

        with patch(
            "mfire.text.synthesis.wind_reducers.wind.case3.wind_direction."
            "PcdFinder.CLASS_PERCENT_MIN",
            100.0,
        ):
            period_finder = PcdFinder(dataset)
            pcd = period_finder.run()

        result: dict = {
            "input": {"valid_time": [str(v) for v in valid_time], "data_wd": data},
            "pcd": [str(p) for p in pcd],
        }

        # Check text
        assert_equals_result(result)

    def test_equals_1st_and_last_pcd(self):
        dataset: xr.Dataset = self._create_dataset(generate_valid_time(periods=12))

        period_finder = PcdFinder(dataset)
        period_finder._term_periods = [
            Pcd(
                begin_time=Datetime(2024, 2, 1, 23),
                end_time=Datetime(2024, 2, 2, 5),
                wd=self.WIND_DIRECTION_CLASS(160.0, 120.0),
            ),
            None,
            None,
            None,
            Pcd(
                begin_time=Datetime(2024, 2, 2, 8),
                end_time=Datetime(2024, 2, 2, 11),
                wd=self.WIND_DIRECTION_CLASS(200.0, 90.0),
            ),
        ]

        period_finder.run()

        assert period_finder._pcd == [
            Pcd(
                begin_time=Datetime(2024, 2, 1, 23),
                end_time=Datetime(2024, 2, 2, 11),
                wd=self.WIND_DIRECTION_CLASS(225.0),
            )
        ]
