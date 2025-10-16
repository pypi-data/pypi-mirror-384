import pytest

from mfire.settings.constants import LANGUAGES
from mfire.utils.date import Datetime, Timedelta
from mfire.utils.period import Period, PeriodDescriber, Periods
from tests.utils.factories import PeriodDescriberFactory


class TestPeriod:
    _p1 = Period(begin_time=Datetime(2021, 1, 1), end_time=Datetime(2021, 1, 2))
    _p2 = Period(begin_time=Datetime(2021, 1, 3), end_time=Datetime(2021, 1, 4))
    _p3 = Period(begin_time=Datetime(2021, 1, 1, 23), end_time=Datetime(2021, 1, 2, 23))
    _p4 = Period(begin_time=Datetime(2021, 1, 1, 10), end_time=Datetime(2021, 1, 1, 12))
    _p5 = Period(begin_time=Datetime(2021, 1, 1, 11), end_time=Datetime(2021, 1, 1, 15))
    _p6 = Period(begin_time=Datetime(2021, 1, 1, 12), end_time=Datetime(2021, 1, 1, 16))

    _d1 = Datetime(2021, 1, 1, 20)
    _d2 = Datetime(2021, 1, 2, 12)
    _d3 = Datetime(2021, 1, 5, 9)
    _d4 = Datetime(2021, 2, 1, 9)
    _d5 = Datetime(2021, 1, 1, 18)

    def test_init(self):
        p1 = Period(begin_time=Datetime(2021, 4, 17), end_time=Datetime(2021, 4, 18))
        p2 = Period(begin_time="20210417", end_time="20210418")
        assert isinstance(p1, Period)
        assert isinstance(p2, Period)
        assert p1 == p2

        assert (
            str(self._p1) == "Period(begin_time=2021-01-01T00:00:00+00:00, "
            "end_time=2021-01-02T00:00:00+00:00)"
        )

    def test_init_end_time(self):
        assert Period(begin_time=self._d1).end_time == self._d1

    def test_eq(self):
        assert self._p1 == self._p1
        assert self._p1 != self._p2
        assert Period(begin_time=self._d1, language="fr") == Period(
            begin_time=self._d1, language="es"
        )

    def test_total_hours(self):
        assert (
            Period(
                begin_time=Datetime(2023, 3, 1, 2), end_time=Datetime(2023, 3, 1, 8)
            ).total_hours
            == 6
        )

    def test_days(self):
        assert (
            Period(begin_time=Datetime(2023, 3, 1), end_time=Datetime(2023, 3, 5)).days
            == 4
        )
        assert (
            Period(
                begin_time=Datetime(2023, 3, 1, 12), end_time=Datetime(2023, 3, 2, 22)
            ).days
            == 2
        )

    @pytest.mark.parametrize(
        "p1,p2,expected",
        [
            (
                _p1,
                _p2,
                Period(begin_time=Datetime("20210101"), end_time=Datetime("20210104")),
            ),
            (
                _p2,
                _p1,
                Period(begin_time=Datetime("20210101"), end_time=Datetime("20210104")),
            ),
            (
                _p1,
                _p3,
                Period(
                    begin_time=Datetime("20210101"), end_time=Datetime("202101022300")
                ),
            ),
            (
                _p2,
                _p3,
                Period(
                    begin_time=Datetime("202101012300"), end_time=Datetime("20210104")
                ),
            ),
        ],
    )
    def test_basic_union(self, p1, p2, expected):
        assert p1.basic_union(p2) == expected

    @pytest.mark.parametrize(
        "p1,p2,expected",
        [
            (_p1, _p2, Periods([_p1, _p2])),
            (_p2, _p1, Periods([_p1, _p2])),
            (
                _p4,
                _p5,
                Periods(
                    [
                        Period(
                            begin_time=Datetime(2021, 1, 1, 10),
                            end_time=Datetime(2021, 1, 1, 15),
                        )
                    ]
                ),
            ),
            (
                _p4,
                _p6,
                Periods(
                    [
                        Period(
                            begin_time=Datetime(2021, 1, 1, 10),
                            end_time=Datetime(2021, 1, 1, 16),
                        )
                    ]
                ),
            ),
        ],
    )
    def test_union(self, p1, p2, expected):
        assert p1.union(p2) == expected

    @pytest.mark.parametrize(
        "p1,p2,expected", [(_p1, _p2, False), (_p1, _p3, True), (_p2, _p3, True)]
    )
    def test_extends(self, p1, p2, expected):
        assert p1.extends(p2, language="fr") is expected

    @pytest.mark.parametrize(
        "p1,p2,expected", [(_p1, _p2, False), (_p1, _p3, True), (_p2, _p3, False)]
    )
    def test_intersects(self, p1, p2, expected):
        assert p1.intersects(p2) is expected

    @pytest.mark.parametrize(
        "p1,p2,expected",
        [
            (_p4, _p5, Timedelta(hours=1)),
            (_p4, _p2, Timedelta(hours=0)),
            (_p5, _p6, Timedelta(hours=3)),
        ],
    )
    def test_intersection(self, p1, p2, expected):
        assert p1.intersection(p2) == expected

    def test_describe(self, assert_equals_result):
        result = {}
        for language in LANGUAGES:
            result[language] = {}
            for begin_time, end_time in [
                (self._d5, self._d1),
                (self._d5, self._d2),
                (self._d5, self._d3),
                (self._d5, self._d4),
                (Datetime(2021, 1, 5, 12), Datetime(2021, 1, 5, 17)),
            ]:
                result[language][str((begin_time, end_time))] = Period(
                    begin_time=begin_time, end_time=end_time
                ).describe(
                    Datetime(2021, 1, 1, 12),
                    time_zone="Europe/Paris",
                    language=language,
                )
        assert_equals_result(result)

    def test_describe_after_midnight(self, assert_equals_result):
        # This test ensures that period after midnight are well described
        assert_equals_result(
            Period(
                begin_time=Datetime(2024, 7, 21), end_time=Datetime(2024, 7, 21, 22)
            ).describe(
                Datetime(2024, 7, 20, 23), time_zone="Europe/Paris", language="fr"
            )
        )


class TestPeriods:
    def test_properties(self):
        periods = Periods(
            [
                Period(
                    begin_time=Datetime(2021, 1, 1, 5), end_time=Datetime(2021, 1, 1, 8)
                ),
                Period(
                    begin_time=Datetime(2021, 1, 1, 12),
                    end_time=Datetime(2021, 1, 1, 15),
                ),
            ]
        )
        assert periods.begin_time == Datetime(2021, 1, 1, 5)
        assert periods.end_time == Datetime(2021, 1, 1, 15)

    @pytest.mark.parametrize(
        "a,b,expected",
        [
            (
                [
                    Period(
                        begin_time=Datetime(2021, 1, 1, 5),
                        end_time=Datetime(2021, 1, 1, 8),
                    )
                ],
                [],
                [
                    Period(
                        begin_time=Datetime(2021, 1, 1, 5),
                        end_time=Datetime(2021, 1, 1, 8),
                    )
                ],
            ),
            (
                [],
                [
                    Period(
                        begin_time=Datetime(2021, 1, 1, 5),
                        end_time=Datetime(2021, 1, 1, 8),
                    )
                ],
                [
                    Period(
                        begin_time=Datetime(2021, 1, 1, 5),
                        end_time=Datetime(2021, 1, 1, 8),
                    )
                ],
            ),
            (
                [
                    Period(
                        begin_time=Datetime(2021, 1, 1, 5),
                        end_time=Datetime(2021, 1, 1, 8),
                    ),
                    Period(
                        begin_time=Datetime(2021, 1, 1, 12),
                        end_time=Datetime(2021, 1, 1, 15),
                    ),
                ],
                [
                    Period(
                        begin_time=Datetime(2021, 1, 1, 6),
                        end_time=Datetime(2021, 1, 1, 9),
                    ),
                    Period(
                        begin_time=Datetime(2021, 1, 1, 10),
                        end_time=Datetime(2021, 1, 1, 11),
                    ),
                    Period(
                        begin_time=Datetime(2021, 1, 1, 14),
                        end_time=Datetime(2021, 1, 1, 19),
                    ),
                ],
                [
                    Period(
                        begin_time=Datetime(2021, 1, 1, 5),
                        end_time=Datetime(2021, 1, 1, 9),
                    ),
                    Period(
                        begin_time=Datetime(2021, 1, 1, 10),
                        end_time=Datetime(2021, 1, 1, 11),
                    ),
                    Period(
                        begin_time=Datetime(2021, 1, 1, 12),
                        end_time=Datetime(2021, 1, 1, 19),
                    ),
                ],
            ),
        ],
    )
    def test_add(self, a, b, expected):
        assert Periods(a) + Periods(b) == Periods(expected)

        p = Periods(a)
        p += Periods(b)
        assert p == Periods(expected)

    @pytest.mark.parametrize(
        "dates,expected",
        [
            # Union of two datetimes without covering
            (
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 6),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 8),
                        end_time=Datetime(2023, 3, 4, 12),
                    ),
                ],
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 6),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 8),
                        end_time=Datetime(2023, 3, 4, 12),
                    ),
                ],
            ),
            # Union of two datetimes with covering
            (
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 10),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 8),
                        end_time=Datetime(2023, 3, 4, 12),
                    ),
                ],
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 12),
                    )
                ],
            ),
            # Union of two datetimes unsorted
            (
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 8),
                        end_time=Datetime(2023, 3, 4, 12),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 10),
                    ),
                ],
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 12),
                    )
                ],
            ),
            # Repetition of two datetimes
            (
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 10),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 10),
                    ),
                ],
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 10),
                    )
                ],
            ),
            # Continuity of two/three datetimes
            (
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 10),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 10),
                        end_time=Datetime(2023, 3, 4, 12),
                    ),
                ],
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 12),
                    )
                ],
            ),
            (
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 10),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 10),
                        end_time=Datetime(2023, 3, 4, 12),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 11),
                        end_time=Datetime(2023, 3, 4, 15),
                    ),
                ],
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 15),
                    )
                ],
            ),
        ],
    )
    def test_reduce_without_n(self, dates, expected):
        periods = Periods(dates)
        assert periods.reduce() == Periods(expected)

    @pytest.mark.parametrize(
        "dates,expected",
        [
            # Reduce the two first
            (
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 10),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 11),
                        end_time=Datetime(2023, 3, 4, 13),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 19),
                        end_time=Datetime(2023, 3, 4, 20),
                    ),
                ],
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 13),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 19),
                        end_time=Datetime(2023, 3, 4, 20),
                    ),
                ],
            ),
            # Reduce the two last
            (
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 10),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 15),
                        end_time=Datetime(2023, 3, 4, 18),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 19),
                        end_time=Datetime(2023, 3, 4, 20),
                    ),
                ],
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 10),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 15),
                        end_time=Datetime(2023, 3, 4, 20),
                    ),
                ],
            ),
            # Reduce the third first
            (
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 8),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 11),
                        end_time=Datetime(2023, 3, 4, 13),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 14),
                        end_time=Datetime(2023, 3, 4, 15),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 22),
                        end_time=Datetime(2023, 3, 4, 23),
                    ),
                ],
                [
                    Period(
                        begin_time=Datetime(2023, 3, 4, 4),
                        end_time=Datetime(2023, 3, 4, 15),
                    ),
                    Period(
                        begin_time=Datetime(2023, 3, 4, 22),
                        end_time=Datetime(2023, 3, 4, 23),
                    ),
                ],
            ),
        ],
    )
    def test_reduce_with_n(self, dates, expected):
        periods = Periods(dates)
        assert periods.reduce(n=2) == Periods(expected)

    @pytest.mark.parametrize(
        "periods,expected",
        [
            (
                [
                    Period(
                        begin_time=Datetime(2021, 1, 1, 5),
                        end_time=Datetime(2021, 1, 1, 8),
                    ),
                    Period(
                        begin_time=Datetime(2021, 1, 1, 11),
                        end_time=Datetime(2021, 1, 1, 15),
                    ),
                ],
                7,
            ),
            (
                [
                    Period(
                        begin_time=Datetime(2021, 1, 1, 5),
                        end_time=Datetime(2021, 1, 2, 8),
                    ),
                    Period(
                        begin_time=Datetime(2021, 1, 2, 11),
                        end_time=Datetime(2021, 1, 2, 15),
                    ),
                ],
                31,
            ),
        ],
    )
    def test_total_hours(self, periods, expected):
        assert Periods(periods).total_hours == expected

    @pytest.mark.parametrize(
        "periods,expected",
        [
            ([], 0),
            (
                [
                    Period(
                        begin_time=Datetime(2021, 1, 1, 5),
                        end_time=Datetime(2021, 1, 1, 8),
                    ),
                    Period(
                        begin_time=Datetime(2021, 1, 1, 11),
                        end_time=Datetime(2021, 1, 1, 15),
                    ),
                ],
                1,
            ),
            (
                [
                    Period(
                        begin_time=Datetime(2021, 1, 1, 5),
                        end_time=Datetime(2021, 1, 2, 8),
                    ),
                    Period(
                        begin_time=Datetime(2021, 1, 2, 11),
                        end_time=Datetime(2021, 1, 2, 15),
                    ),
                ],
                2,
            ),
        ],
    )
    def test_total_days(self, periods, expected):
        assert Periods(periods).total_days == expected

    def test_all_intersections(self):
        p1 = Periods(
            [
                Period(
                    begin_time=Datetime(2023, 3, 1, 5),
                    end_time=Datetime(2023, 3, 1, 10),
                ),
                Period(
                    begin_time=Datetime(2023, 3, 1, 16),
                    end_time=Datetime(2023, 3, 1, 19),
                ),
            ]
        )
        p2 = Periods(
            [
                Period(
                    begin_time=Datetime(2023, 3, 1, 8),
                    end_time=Datetime(2023, 3, 1, 12),
                ),
                Period(
                    begin_time=Datetime(2023, 3, 1, 15),
                    end_time=Datetime(2023, 3, 1, 20),
                ),
            ]
        )

        assert list(p1.all_intersections(p2)) == [
            Timedelta(hours=2),
            Timedelta(hours=3),
        ]

    def test_intersects(self):
        p1 = Periods(
            [
                Period(
                    begin_time=Datetime(2023, 3, 1, 5),
                    end_time=Datetime(2023, 3, 1, 10),
                ),
                Period(
                    begin_time=Datetime(2023, 3, 1, 16),
                    end_time=Datetime(2023, 3, 1, 19),
                ),
            ]
        )
        p2 = Periods(
            [
                Period(
                    begin_time=Datetime(2023, 3, 1, 2), end_time=Datetime(2023, 3, 1, 4)
                ),
                Period(
                    begin_time=Datetime(2023, 3, 1, 9),
                    end_time=Datetime(2023, 3, 1, 11),
                ),
            ]
        )
        assert p1.intersects(p2)
        assert p2.intersects(p1)

        p3 = Periods(
            [
                Period(
                    begin_time=Datetime(2023, 3, 1, 2), end_time=Datetime(2023, 3, 1, 4)
                )
            ]
        )
        assert not p1.intersects(p3)

    def test_hours_of_intersection(self):
        p1 = Periods(
            [
                Period(
                    begin_time=Datetime(2023, 3, 1, 5),
                    end_time=Datetime(2023, 3, 1, 10),
                ),
                Period(
                    begin_time=Datetime(2023, 3, 1, 16),
                    end_time=Datetime(2023, 3, 1, 19),
                ),
            ]
        )
        p2 = Periods(
            [
                Period(
                    begin_time=Datetime(2023, 3, 1, 8),
                    end_time=Datetime(2023, 3, 1, 12),
                ),
                Period(
                    begin_time=Datetime(2023, 3, 1, 15),
                    end_time=Datetime(2023, 3, 1, 20),
                ),
            ]
        )

        assert p1.hours_of_intersection(p2) == 5

    def test_hours_of_union(self):
        p1 = Periods(
            [
                Period(
                    begin_time=Datetime(2023, 3, 1, 5),
                    end_time=Datetime(2023, 3, 1, 10),
                ),
                Period(
                    begin_time=Datetime(2023, 3, 1, 16),
                    end_time=Datetime(2023, 3, 1, 19),
                ),
            ]
        )
        p2 = Periods(
            [
                Period(
                    begin_time=Datetime(2023, 3, 1, 8),
                    end_time=Datetime(2023, 3, 1, 12),
                ),
                Period(
                    begin_time=Datetime(2023, 3, 1, 15),
                    end_time=Datetime(2023, 3, 1, 20),
                ),
            ]
        )

        assert p1.hours_of_union(p2) == 12


class TestPeriodDescriber:
    pdesc = PeriodDescriberFactory(
        cover_period=Period(
            begin_time=Datetime(2021, 1, 1), end_time=Datetime(2021, 1, 2)
        ),
        request_time=Datetime(2021, 1, 1),
    )
    p1 = Period(begin_time=Datetime(2021, 1, 1, 18), end_time=Datetime(2021, 1, 2, 7))
    p2 = Period(begin_time=Datetime(2021, 1, 2, 8), end_time=Datetime(2021, 1, 2, 16))
    p3 = Period(begin_time=Datetime(2021, 1, 2, 17), end_time=Datetime(2021, 1, 3, 8))

    def test_eq(self):
        assert self.pdesc == self.pdesc
        assert self.pdesc != PeriodDescriberFactory(
            cover_period=Period(begin_time=Datetime(2021, 1, 2)),
            request_time=Datetime(2021, 1, 1, 12),
        )
        assert self.pdesc != PeriodDescriberFactory(
            cover_period=Period(
                begin_time=Datetime(2021, 1, 1), end_time=Datetime(2021, 1, 2)
            ),
            request_time=Datetime(2021, 1, 2),
        )

    def test_describe(self):
        assert isinstance(self.pdesc, PeriodDescriber)
        assert (
            self.pdesc.describe(self.p1)
            == "de ce vendredi soir jusqu’à samedi en début de matinée"
        )
        assert (
            self.pdesc.describe(Periods([self.p1, self.p2]))
            == "de ce vendredi soir jusqu’à samedi après-midi"
        )
        assert (
            self.pdesc.describe(Periods([self.p1, self.p3]))
            == "de ce vendredi soir jusqu’à samedi en début de matinée puis de samedi "
            "après-midi jusqu’à dimanche en début de matinée"
        )

        assert self.pdesc.describe(self.pdesc.cover_period) == "sur toute la période"
        assert (
            self.pdesc.describe(
                Periods(
                    [
                        Period(
                            begin_time=Datetime(2020, 1, 1, 0),
                            end_time=Datetime(2021, 1, 1, 2),
                        )
                    ]
                )
            )
            == "en début de période"
        )
        assert (
            self.pdesc.describe(
                Periods(
                    [
                        Period(
                            begin_time=Datetime(2021, 1, 1, 22),
                            end_time=Datetime(2021, 1, 10),
                        )
                    ]
                )
            )
            == "en fin de période"
        )

        assert (
            self.pdesc.describe(
                Periods(
                    [
                        Period(
                            begin_time=Datetime(2021, 1, 1),
                            end_time=Datetime(2021, 1, 1, 10),
                        ),
                        Period(
                            begin_time=Datetime(2021, 1, 1, 16),
                            end_time=Datetime(2021, 1, 2),
                        ),
                    ]
                )
            )
            == "jusqu'à ce matin puis à nouveau à partir de cet après-midi"
        )

        assert (
            self.pdesc.describe(
                Periods(
                    [
                        Period(
                            begin_time=Datetime(2021, 1, 1),
                            end_time=Datetime(2021, 1, 1, 2),
                        ),
                        Period(
                            begin_time=Datetime(2021, 1, 1, 16),
                            end_time=Datetime(2021, 1, 1, 22),
                        ),
                    ]
                )
            )
            == "en début de période puis à nouveau à partir de cet après-midi"
        )

        assert (
            self.pdesc.describe(
                Periods(
                    [
                        Period(
                            begin_time=Datetime(2021, 1, 1),
                            end_time=Datetime(2021, 1, 1, 10),
                        ),
                        Period(
                            begin_time=Datetime(2021, 1, 1, 22),
                            end_time=Datetime(2021, 1, 23),
                        ),
                    ]
                )
            )
            == "jusqu'à ce matin puis à nouveau en fin de période"
        )

        assert (
            self.pdesc.describe(
                Periods(
                    [
                        Period(
                            begin_time=Datetime(2021, 1, 1),
                            end_time=Datetime(2021, 1, 1, 2),
                        ),
                        Period(
                            begin_time=Datetime(2021, 1, 1, 22),
                            end_time=Datetime(2021, 1, 1, 23),
                        ),
                    ]
                )
            )
            == "en début de période puis à nouveau en fin de période"
        )
        # Test of period repetition
        pdesc = PeriodDescriberFactory(
            cover_period=Period(
                begin_time=Datetime(2021, 1, 1), end_time=Datetime(2021, 1, 4)
            ),
            request_time=Datetime(2021, 1, 1),
        )

        assert (
            pdesc.describe(
                Periods(
                    [
                        Period(
                            begin_time=Datetime(2021, 1, 1, 9),
                            end_time=Datetime(2021, 1, 1, 10),
                        ),
                        Period(
                            begin_time=Datetime(2021, 1, 2, 10),
                            end_time=Datetime(2021, 1, 2, 11),
                        ),
                        Period(
                            begin_time=Datetime(2021, 1, 3, 10),
                            end_time=Datetime(2021, 1, 3, 11),
                        ),
                    ]
                )
            )
            == "les matins"
        )

        assert (
            pdesc.describe(
                Periods(
                    [
                        Period(
                            begin_time=Datetime(2021, 1, 1, 9),
                            end_time=Datetime(2021, 1, 1, 10),
                        ),
                        Period(
                            begin_time=Datetime(2021, 1, 3, 10),
                            end_time=Datetime(2021, 1, 3, 11),
                        ),
                    ]
                )
            )
            == "ce vendredi en fin de matinée puis dimanche matin"
        )

    def test_reduce(self):
        assert not self.pdesc.reduce(Periods())
        assert self.pdesc.reduce(Periods([self.p1, self.p2, self.p3])) == Periods(
            [Period(begin_time=self.p1.begin_time, end_time=self.p3.end_time)]
        )
