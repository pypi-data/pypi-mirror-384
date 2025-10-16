import pytest

from mfire.composite.period import PeriodsComposite
from mfire.utils.date import Datetime
from tests.composite.factories import PeriodCompositeFactory


class TestPeriod:
    def test_init_boundaries(self):
        period = PeriodCompositeFactory(start="2023-03-01", stop="2023-03-03")
        assert period.start == Datetime(2023, 3, 1)
        assert period.stop == Datetime(2023, 3, 3)

    def test_total_hours(self):
        assert (
            PeriodCompositeFactory(
                start=Datetime(2021, 1, 1, 5), stop=Datetime(2021, 1, 1, 8)
            ).total_hours
            == 3
        )


class TestPeriodCollection:
    def test_attributes(self):
        p1 = PeriodCompositeFactory(id="id1")
        p2 = PeriodCompositeFactory(id="id2")
        period_collection = PeriodsComposite(periods=[p1, p2])

        assert len(period_collection) == 2

        assert period_collection["id1"] == p1
        assert list(iter(period_collection)) == [p1, p2]

        with pytest.raises(KeyError, match="id3"):
            _ = period_collection["id3"]

        assert period_collection.get("id2") == p2
        assert period_collection.get("id3") is None
