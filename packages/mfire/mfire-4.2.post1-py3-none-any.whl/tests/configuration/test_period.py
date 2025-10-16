import pytest
from pydantic import ValidationError

from mfire.configuration.period import (
    PeriodCollection,
    PeriodMultiple,
    PeriodSingle,
    PeriodSingleBase,
)
from mfire.utils.date import Datetime
from tests.configuration.factories import PeriodMultipleFactory, PeriodSingleFactory


class TestPeriodSingleBase:
    def test_init_production_time_until(self):
        assert (
            PeriodSingleBase(
                start=6, stop=10, productionTime_until=None
            ).production_time_until
            == 24
        )
        assert (
            PeriodSingleBase(
                start=6, stop=10, productionTime_until=0
            ).production_time_until
            == 0
        )
        assert (
            PeriodSingleBase(
                start=6, stop=10, productionTime_until=24
            ).production_time_until
            == 24
        )
        assert (
            PeriodSingleBase(
                start=6, stop=10, productionTime_until=11
            ).production_time_until
            == 11
        )
        with pytest.raises(ValidationError):
            _ = PeriodSingleBase(
                start=6, stop=10, productionTime_until=3.2
            ).production_time_until
        with pytest.raises(ValidationError):
            _ = PeriodSingleBase(
                start=6, stop=10, productionTime_until=28
            ).production_time_until

    @pytest.mark.parametrize(
        "values",
        [
            {"start": 6, "stop": 10},
            {"deltaStart": 6, "stop": 10},
            {"start": 6, "deltaStop": 10},
            {"absoluStart": "20230301", "absoluStop": "20230302"},
        ],
    )
    def test_init_start_stop(self, values, assert_equals_result):
        assert_equals_result(PeriodSingleBase(**values))

    def test_init_start_stop_fails(self):
        with pytest.raises(ValueError, match="Exactly one 'start' key expected"):
            PeriodSingleBase(start=6, deltaStart=5)
        with pytest.raises(ValueError, match="Exactly one 'start' key expected"):
            PeriodSingleBase()
        with pytest.raises(ValueError, match="Exactly one 'stop' key expected"):
            PeriodSingleBase(start=6, absoluStop=Datetime(2023, 3, 1), stop=5)

    def test_bound(self):
        element = PeriodSingleBase(deltaStart=1, stop=20, productionTime_until=16)
        prod_dt = Datetime(2021, 1, 1, 15)

        # Si production_time est avant pT_until, on devrait produire pour la même
        # journée
        assert element.bound(prod_dt, "start") == Datetime(2021, 1, 1, 16)
        assert element.bound(prod_dt, "stop") == Datetime(2021, 1, 1, 20)

        prod_dt = Datetime(2021, 1, 1, 16)
        # Si production_time == pT_until, on devrait produit pour le lendemain
        assert element.bound(prod_dt, "start") == Datetime(2021, 1, 1, 17)
        assert element.bound(prod_dt, "stop") == Datetime(2021, 1, 2, 20)

        # Si le production_time > pT_until, on devrait produire jusqu'au lendemain
        prod_dt = Datetime(2021, 1, 1, 17)
        assert element.bound(prod_dt, "start") == Datetime(2021, 1, 1, 18)
        assert element.bound(prod_dt, "stop") == Datetime(2021, 1, 2, 20)

        element = PeriodSingleBase(
            start=6, absoluStop=Datetime(2021, 1, 3, 12), productionTime_until=16
        )
        assert element.bound(prod_dt, "start") == Datetime(2021, 1, 2, 6)
        assert element.bound(prod_dt, "stop") == Datetime(2021, 1, 3, 12)

    def test_start_stop(self):
        element = PeriodSingleBase(deltaStart=1, stop=20, productionTime_until=16)
        assert element.start_stop(Datetime(2021, 1, 1, 16)) == (
            Datetime(2021, 1, 1, 17),
            Datetime(2021, 1, 2, 20),
        )

        prod_dt = Datetime(2021, 1, 1, 17)
        assert element.start_stop(prod_dt) == (
            Datetime(2021, 1, 1, 18),
            Datetime(2021, 1, 2, 20),
        )

        element = PeriodSingleBase(
            start=6, absoluStop=Datetime(2021, 1, 3, 12), productionTime_until=16
        )
        assert element.start_stop(prod_dt) == (
            Datetime(2021, 1, 2, 6),
            Datetime(2021, 1, 3, 12),
        )

        element = PeriodSingleBase(deltaStart=-1, stop=10, productionTime_until=16)
        assert element.start_stop(Datetime(2021, 1, 1, 16)) == (
            Datetime(2021, 1, 1, 15),
            Datetime(2021, 1, 2, 10),
        )


class TestPeriodSingle:
    @pytest.mark.parametrize(
        "production_datetime",
        [Datetime(2021, 1, 1, 15), Datetime(2021, 1, 1, 16), Datetime(2021, 1, 1, 17)],
    )
    def test_processed_period(self, production_datetime, assert_equals_result):
        period = PeriodSingleFactory(deltaStart=1, stop=32, productionTime_until=16)
        assert_equals_result(period.processed_period(production_datetime))


class TestPeriodMultiple:
    @pytest.mark.parametrize(
        "production_datetime",
        [
            # production is before productionTime_until (6),
            # the period should use the first periodElement and be on the same day
            Datetime(2021, 1, 1, 5),
            # production == productionTime_until (6),
            # the period should use the second periodElement
            Datetime(2021, 1, 1, 6),
            # production is after productionTime_until (6) but before (12),
            # the period should use the second periodElement
            Datetime(2021, 1, 1, 7),
            # production == productionTime_until (12), the Period should switch from the
            # second to the third periodElement
            Datetime(2021, 1, 1, 12),
            # production is after productionTime_until(13), the Period should use the
            # third periodElement
            Datetime(2021, 1, 1, 13),
            # production == productionTime_until, we've gone full circle and use the
            # first periodElement again but with values for the next day
            Datetime(2021, 1, 1, 18),
            # production is still after productionTime_until(18) and before (6),
            # we still use the first periodElement
            Datetime(2021, 1, 1, 19),
        ],
    )
    def test_processed_period(self, production_datetime, assert_equals_result):
        period = PeriodMultipleFactory(
            periodElements=[
                PeriodSingleFactory(start=6, stop=18, productionTime_until=6),
                PeriodSingleFactory(deltaStart=1, deltaStop=12, productionTime_until=6),
                PeriodSingleFactory(
                    absoluStart="2021-01-01T18:00:00",
                    absoluStop="20210102T060000",
                    productionTime_until=18,
                ),
            ]
        )
        assert_equals_result(period.processed_period(production_datetime))


class TestPeriodCollection:
    factory: PeriodCollection = PeriodCollection(
        periods=[
            PeriodSingle(id="period1", deltaStart=1, stop=32, productionTime_until=16),
            PeriodMultiple(
                id="period2",
                periodElements=[
                    PeriodSingleBase(start=6, stop=18, productionTime_until=6),
                    PeriodSingleBase(
                        deltaStart=1, deltaStop=12, productionTime_until=12
                    ),
                    PeriodSingleBase(
                        absoluStart="2021-01-01T18:00:00",
                        absoluStop="2021-01-02T06:00:00",
                        productionTime_until=18,
                    ),
                ],
            ),
        ]
    )

    def test_init(self):
        assert isinstance(self.factory.periods[0], PeriodSingle)
        assert isinstance(self.factory.periods[1], PeriodMultiple)

        assert self.factory["period1"] == self.factory.periods[0]
        with pytest.raises(KeyError):
            _ = self.factory["toto"]

    def test_processed_periods(self, assert_equals_result):
        assert_equals_result(self.factory.processed_periods(Datetime(2021, 1, 1, 6)))
