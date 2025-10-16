from mfire.production.period import CDPPeriod
from mfire.utils.date import Datetime
from tests.composite.factories import PeriodCompositeFactory
from tests.production.factories import CDPPeriodFactory


class TestCDPPeriod:
    def test_init_dates(self):
        cdp_period = CDPPeriodFactory(
            DateDebutPeriode="2023-05-01", DateFinPeriode="20230504T000000"
        )
        assert cdp_period.DateDebutPeriode == Datetime(2023, 5, 1)
        assert cdp_period.DateFinPeriode == Datetime(2023, 5, 4)

    def test_from_composite(self):
        cdp_period = CDPPeriod.from_composite(PeriodCompositeFactory())
        assert cdp_period.PeriodId == "period_id"
        assert cdp_period.PeriodName == "period_name"
        assert cdp_period.DateDebutPeriode == Datetime(2023, 3, 1)
        assert cdp_period.DateFinPeriode == Datetime(2023, 3, 5)

        cdp_period = CDPPeriod.from_composite(PeriodCompositeFactory(name=None))
        assert cdp_period.PeriodId == "period_id"
        assert (
            cdp_period.PeriodName
            == "Du 2023-03-01T00:00:00+00:00 au 2023-03-05T00:00:00+00:00"
        )
        assert cdp_period.DateDebutPeriode == Datetime(2023, 3, 1)
        assert cdp_period.DateFinPeriode == Datetime(2023, 3, 5)
