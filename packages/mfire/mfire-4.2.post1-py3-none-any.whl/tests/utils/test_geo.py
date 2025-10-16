from mfire.settings.constants import LANGUAGES
from mfire.utils.geo import CompassRose8, CompassRose16


class TestCompassRose8:
    def test_azimut(self):
        assert round(CompassRose8.azimut((0, 0), (1, 1)), 2) == 45

    def test_from_azimut(self):
        assert CompassRose8.from_azimut(60) == CompassRose8.NE
        assert CompassRose8.from_azimut(359) == CompassRose8.N
        assert CompassRose8.from_azimut(540) == CompassRose8.S

    def test_opposite(self):
        assert CompassRose8.N.opposite == CompassRose8.S
        assert all(d.opposite == d + 180 for d in CompassRose8)

    def test_text_descriptions(self, assert_equals_result):
        assert_equals_result(
            {
                language: [
                    CompassRose8.N.description(language),
                    CompassRose8.N.text(language),
                    CompassRose8.N.short_description(language),
                ]
                for language in LANGUAGES
            }
        )

    def test_from_points(self):
        assert CompassRose8.from_points((0, 0), (1, 1)) == CompassRose8.NE
        assert CompassRose8.from_points((0, 0), (1, 2)) == CompassRose8.NE


class TestCompassRose16:
    def test_from_azimut(self):
        assert CompassRose16.from_azimut(60) == CompassRose16.ENE
        assert CompassRose16.from_azimut(359) == CompassRose16.N

    def test_opposite(self):
        assert CompassRose16.N.opposite == CompassRose16.S
        assert all(d.opposite == d + 180 for d in CompassRose16)

    def test_text_descriptions(self, assert_equals_result):
        assert_equals_result(
            {
                language: [
                    CompassRose16.N.description(language),
                    CompassRose16.N.text(language),
                    CompassRose16.N.short_description(language),
                ]
                for language in LANGUAGES
            }
        )

    def test_from_points(self):
        assert CompassRose16.from_points((0, 0), (1, 2)) == CompassRose16.NNE
