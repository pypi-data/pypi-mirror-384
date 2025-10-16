import numpy as np
import pytest

from mfire.localisation.altitude import AltitudeInterval, Segment
from mfire.settings.constants import LANGUAGES


class TestSegment:
    def test_init(self):
        assert Segment(2, 3) == (2, 3)
        assert Segment(np.nan, 5) == (-np.inf, +np.inf)
        assert Segment(5, np.nan) == (-np.inf, +np.inf)


class TestAltitudeInterval:
    def test_union(self):
        assert AltitudeInterval.union(
            [AltitudeInterval([1, 3], [4, 6]), AltitudeInterval([2, 5], 9)]
        ) == AltitudeInterval([1.0, 6.0], [9.0])
        assert AltitudeInterval([1, 3], [4, 6]) | AltitudeInterval(
            [2, 5], 9
        ) == AltitudeInterval([1.0, 6.0], [9.0])

    def test_hull(self):
        assert AltitudeInterval.hull(
            (AltitudeInterval([1, 3]), AltitudeInterval([10, 15]))
        ) == AltitudeInterval([1.0, 15.0])
        assert AltitudeInterval.hull([AltitudeInterval((1, 2))]) == AltitudeInterval(
            [1.0, 2.0]
        )

    def test_operators(self):
        assert -AltitudeInterval((-3, 5)) == AltitudeInterval((3, -5))

        assert AltitudeInterval((-5, 5)) in AltitudeInterval((-10, 10))
        assert AltitudeInterval((-5, 15)) not in AltitudeInterval((-10, 10))

        assert str(AltitudeInterval((-3, 5))) == "AltitudeInterval([-3, 5])"

    def test_inversion(self):
        assert ~AltitudeInterval([-np.inf, 0]) == AltitudeInterval([0, np.inf])
        assert ~AltitudeInterval([0, 100]) == AltitudeInterval(
            [-np.inf, 0], [100, np.inf]
        )
        assert ~AltitudeInterval([0]) == AltitudeInterval([-np.inf, np.inf])
        assert ~AltitudeInterval(
            [-np.inf, 0], [100, 200], [300], [400, np.inf]
        ) == AltitudeInterval([0, 100], [200, 400])

    def test_difference(self):
        assert AltitudeInterval([0, 1000]).difference(
            [500, np.inf]
        ) == AltitudeInterval([0, 500])

    def test_symmetric_difference(self):
        assert AltitudeInterval([0, 1000]).symmetric_difference(
            [500, np.inf]
        ) == AltitudeInterval([0, 500], [1000, np.inf])

    def test_is_sub_interval(self):
        my_interval = AltitudeInterval([0, 1000])
        assert my_interval.is_sub_interval((0, 2000)) is True
        assert my_interval.is_sub_interval((500, 2000)) is False

    def test_is_super_interval(self):
        my_interval = AltitudeInterval((0, 1000))
        assert my_interval.is_super_interval((0, 500)) is True
        assert my_interval.is_super_interval((-100, 500)) is False

    def test_name_segment(self, assert_equals_result):
        # Basic case
        assert (
            AltitudeInterval.name_segment((0, 1000), "fr", alt_min=0, alt_max=800) == ""
        )
        assert AltitudeInterval.name_segment((1000, 1000), "fr", alt_min=1000) == ""
        assert AltitudeInterval.name_segment((1500, 1000), "fr") == ""

        assert_equals_result(
            {
                language: {
                    str(segment): AltitudeInterval.name_segment(
                        segment, language=language, alt_min=50, alt_max=300
                    )
                    for segment in [
                        (-np.inf, 100),
                        (100, np.inf),
                        (100, 200),
                        (100, 100),
                        (20, 100),
                        (100, 400),
                    ]
                }
                for language in LANGUAGES
            }
        )

    def test_name(self, assert_equals_result):
        empty = AltitudeInterval()
        assert empty.name("fr") == ""

        inter = AltitudeInterval((-np.inf, 100), (200, 300), (400), (500, 1000))
        assert_equals_result(
            {
                language: {
                    "no alt_min,no_alt_max": inter.name(language),
                    "alt_max=1000": inter.name(language, alt_max=1000),
                    "alt_min=500": inter.name(language, alt_min=500),
                    "alt_min=400,alt_max=800": inter.name(
                        language, alt_min=400, alt_max=800
                    ),
                }
                for language in LANGUAGES
            }
        )

    @pytest.mark.parametrize(
        "language,area_name,expected",
        [
            ("fr", "à Toulouse", "à Toulouse"),
            ("fr", "entre 1000 m et 1500 m", "entre 1000 m et 1500 m"),
            ("fr", "entre 1000 m et 2500 m", "au-dessus de 1000 m"),
            ("fr", "entre 250 m et 1700 m", "en dessous de 1700 m"),
            ("en", "at Toulouse", "at Toulouse"),
            ("en", "between 1000 m and 1500 m", "between 1000 m and 1500 m"),
            ("en", "between 1000 m and 2500 m", "over 1000 m"),
            ("en", "between 250 m and 1700 m", "under 1700 m"),
            ("es", "en Toulouse", "en Toulouse"),
            ("es", "entre 1000 m y 1500 m", "entre 1000 m y 1500 m"),
            ("es", "entre 1000 m y 2500 m", "por encima 1000 m"),
            ("es", "entre 250 m y 1700 m", "por debajo 1700 m"),
        ],
    )
    def test_rename(self, language, area_name, expected):
        assert (
            AltitudeInterval.rename(area_name, language, alt_min=500, alt_max=2000)
            == expected
        )

    @pytest.mark.parametrize(
        "language,string,expected",
        [
            ("fr", "à Toulouse", AltitudeInterval()),
            ("fr", "au-dessus de 800 m", AltitudeInterval([800.0, np.inf])),
            (
                "fr",
                "entre 1000 m et 2000 m",
                AltitudeInterval(AltitudeInterval([1000.0, 2000.0])),
            ),
            ("fr", "à 200 m", AltitudeInterval([200.0, 200.0])),
            ("fr", "en dessous de 450 m", AltitudeInterval([-np.inf, 450])),
            (
                "fr",
                "en dessous de 100 m, entre 800 m et 900 m et au-dessus de 1000 m",
                AltitudeInterval([-np.inf, 100], [800, 900], [1000, np.inf]),
            ),
            ("en", "at Toulouse", AltitudeInterval()),
            ("en", "over 800 m", AltitudeInterval([800.0, np.inf])),
            (
                "en",
                "between 1000 m and 2000 m",
                AltitudeInterval(AltitudeInterval([1000.0, 2000.0])),
            ),
            ("en", "at 200 m", AltitudeInterval([200.0, 200.0])),
            ("en", "under 450 m", AltitudeInterval([-np.inf, 450])),
            (
                "en",
                "under 100 m, between 800 m and 900 m and over 1000 m",
                AltitudeInterval([-np.inf, 100], [800, 900], [1000, np.inf]),
            ),
            ("es", "en Toulouse", AltitudeInterval()),
            ("es", "por encima 800 m", AltitudeInterval([800.0, np.inf])),
            (
                "es",
                "entre 1000 m y 2000 m",
                AltitudeInterval(AltitudeInterval([1000.0, 2000.0])),
            ),
            ("es", "a 200 m", AltitudeInterval([200.0, 200.0])),
            ("es", "por debajo 450 m", AltitudeInterval([-np.inf, 450])),
            (
                "es",
                "por debajo 100 m, entre 800 m y 900 m and por encima 1000 m",
                AltitudeInterval([-np.inf, 100], [800, 900], [1000, np.inf]),
            ),
        ],
    )
    def test_from_name(self, language, string, expected):
        assert AltitudeInterval.from_name(string, language) == expected
