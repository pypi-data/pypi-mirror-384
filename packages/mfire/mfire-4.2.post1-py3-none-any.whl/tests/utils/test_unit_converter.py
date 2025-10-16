import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.utils.calc import all_close
from mfire.utils.unit_converter import (
    find_input_units,
    find_output_units,
    from_beaufort_to_description,
    from_beaufort_to_kt,
    from_dbz_to_kg_per_m2_per_second,
    from_decimal_to_sexagesimal_degree,
    from_decimal_to_sexagesimal_latitude,
    from_decimal_to_sexagesimal_longitude,
    from_degree_to_direction,
    from_kg_per_m2_per_second_to_dbz,
    from_knots_to_beaufort,
    from_knots_to_description,
    from_kt_to_beaufort,
    from_w1_to_wwmf,
    from_wwmf_to_w1,
    pint_converter,
    unit_conversion,
)
from tests.functions_test import assert_identically_close


class TestUnitConverterFunctions:
    @pytest.mark.parametrize(
        "val, expected",
        [
            (0, ("+", 0, 0, 0)),
            (45.5, ("+", 45, 30, 0)),
            (-90.75, ("-", 90, 45, 0)),
            (180.25, ("+", 180, 15, 0)),
        ],
    )
    def test_from_decimal_to_sexagesimal_degree(self, val, expected):
        result = from_decimal_to_sexagesimal_degree(val)
        assert result == expected

    @pytest.mark.parametrize(
        "val, expected",
        [
            (0, "00°00'00\" Nord"),
            (45.5, "45°30'00\" Nord"),
            (-90.75, "90°45'00\" Sud"),
            (180.25, "180°15'00\" Nord"),
        ],
    )
    def test_from_decimal_to_sexagesimal_latitude(self, val, expected):
        result = from_decimal_to_sexagesimal_latitude(val)
        assert result == expected

    @pytest.mark.parametrize(
        "val, expected",
        [
            (0, "00°00'00\" Est"),
            (45.5, "45°30'00\" Est"),
            (-90.75, "90°45'00\" Ouest"),
            (180.25, "180°15'00\" Est"),
        ],
    )
    def test_from_decimal_to_sexagesimal_longitude(self, val, expected):
        result = from_decimal_to_sexagesimal_longitude(val)
        assert result == expected

    @pytest.mark.parametrize(
        "val, expected",
        [
            (0, "Nord"),
            (22.5, "NNE"),
            (45, "NE"),
            (67.5, "ENE"),
            (90, "Est"),
            (112.5, "ESE"),
            (135, "SE"),
            (157.5, "SSE"),
            (180, "Sud"),
            (202.5, "SSO"),
            (225, "SO"),
            (247.5, "OSO"),
            (270, "Ouest"),
            (292.5, "ONO"),
            (315, "NO"),
            (337.5, "NNO"),
            (360, "Nord"),
        ],
    )
    def test_from_degree_to_direction(self, val, expected):
        result = from_degree_to_direction(val)
        assert result == expected

    @pytest.mark.parametrize(
        "val,expected",
        [
            (0, 0),
            (3, 1),
            (6, 2),
            (9, 3),
            (13, 4),
            (18, 5),
            (24, 6),
            (30, 7),
            (37, 8),
            (45, 9),
            (53, 10),
            (61, 11),
            (70, 12),
            (np.array([5, 10, 15, 20]), np.array([2, 3, 4, 5])),
        ],
    )
    def test_from_knots_to_beaufort(self, val, expected):
        result = from_knots_to_beaufort(val)
        assert np.array_equal(result, expected)

    @pytest.mark.parametrize(
        "val,expected",
        [
            (0, "Calme"),
            (1, "Très légère brise"),
            (2, "Légère brise"),
            (3, "Petite brise"),
            (4, "Jolie brise"),
            (5, "Bonne brise"),
            (6, "Vent frais"),
            (7, "Grand vent frais"),
            (8, "Coup de vent"),
            (9, "Fort coup de vent"),
            (10, "Tempête"),
            (11, "Violente tempête"),
            (12, "Ouragan"),
            (13, "Inconnu"),
            (-1, "Inconnu"),
            (np.array([0, 1]), ["Calme", "Très légère brise"]),
            (np.array([7, -1, 10]), ["Grand vent frais", "Inconnu", "Tempête"]),
        ],
    )
    def test_from_beaufort_to_description(self, val, expected):
        result = from_beaufort_to_description(val)
        assert np.array_equal(result, expected)

    @pytest.mark.parametrize(
        "val,expected",
        [
            (0, "Calme"),
            (3, "Très légère brise"),
            (6, "Légère brise"),
            (9, "Petite brise"),
            (13, "Jolie brise"),
            (18, "Bonne brise"),
            (24, "Vent frais"),
            (30, "Grand vent frais"),
            (37, "Coup de vent"),
            (45, "Fort coup de vent"),
            (53, "Tempête"),
            (61, "Violente tempête"),
            (70, "Ouragan"),
        ],
    )
    def test_from_knots_to_description(self, val, expected):
        assert from_knots_to_description(val) == expected

    @pytest.mark.parametrize(
        "kt,expected",
        [
            (0, 0),
            (0.25, 0.25),
            (1, 0.66666),
            (2, 1.0),
            (5, 2.0),
            (8.75, 3.0625),
            (13, 3.916666),
            (19, 5.0),
            (25, 6.083333),
            (30, 6.916666),
            (35, 7.714285),
            (44.5, 9.071428),
            (51, 9.9375),
            (60, 11.0625),
            (70, None),
        ],
    )
    def test_from_kt_to_beaufort(self, kt, expected):
        result = from_kt_to_beaufort(kt)
        assert all_close(result, expected)

    @pytest.mark.parametrize(
        "beaufort, expected",
        [
            (0, 0),
            (0.5, 0.5),
            (1.25, 2.75),
            (2.5, 6.5),
            (3.5, 10.5),
            (4.5, 16.5),
            (5.45, 21.25),
            (6.5, 27.5),
            (7.5, 33.5),
            (8.5, 40.5),
            (9.75, 49.5),
            (10.5, 55.5),
            (11.5, 63.5),
            (12, None),
        ],
    )
    def test_from_beaufort_to_kt(self, beaufort, expected):
        result = from_beaufort_to_kt(beaufort)
        assert result == expected

    def test_from_kg_per_m2_per_second_to_dbz(self):
        x = np.array([1.0, 2.0, 3.0, -1, 0])
        expected = np.array([127.91114, 132.72762, 135.54508, 0.0, 0.0])
        result = from_kg_per_m2_per_second_to_dbz(x)
        np.testing.assert_almost_equal(result, expected)

    def test_from_dbz_to_kg_per_m2_per_second(self):
        x = np.array([100.0, 120.0, 150.0])
        expected = np.array([1.80116605e-02, 3.20297650e-01, 2.40189353e01])
        result = from_dbz_to_kg_per_m2_per_second(x)
        np.testing.assert_almost_equal(result, expected)

    @pytest.mark.parametrize(
        "w1,expected",
        [
            (8, 59),
            (np.nan, np.nan),
            (100, -1),
            ([16, 24], [62, 91]),
            ([2, 32, np.nan], [32, 92, np.nan]),
            (
                xr.DataArray([2, 32, np.nan]),
                xr.DataArray([32, 92, np.nan], attrs={"units": "wwmf"}),
            ),
            (xr.DataArray([4, 22]), xr.DataArray([38, 80], attrs={"units": "wwmf"})),
        ],
    )
    def test_from_w1_to_wwmf(self, w1, expected):
        result = from_w1_to_wwmf(w1)
        assert_identically_close(result, expected)

    @pytest.mark.parametrize(
        "wwmf,expected",
        [
            (-1, []),
            (98, [29]),
            (61, [13]),
            ([98, 99], [25, 29]),
            ([40, 53, 61, 99], [9, 11, 13, 25]),
        ],
    )
    def test_from_wwmf_to_w1(self, wwmf, expected):
        result = from_wwmf_to_w1(wwmf)
        assert result == expected

    def test_pint_converter(self):
        assert all_close(pint_converter(10.0, "m", "ft"), 32.8084)
        assert all_close(pint_converter(50.0, "%", ""), 0.5)
        assert all_close(pint_converter(0.5, "", "%"), 50.0)
        assert all_close(
            pint_converter(xr.DataArray([0.2, 0.8]), "", "%"),
            xr.DataArray([20.0, 80.0]),
        )

    @pytest.mark.parametrize(
        "input_val,input_units,output_units,expected",
        [
            (1.0, "km/h", "B", (0.54, "kt")),
            (xr.DataArray([1.0, 2.0]), "km/h", "B", (xr.DataArray([0.54, 1.08]), "kt")),
            (1.0, "truc", "B", (None, None)),
        ],
    )
    def test_find_input_units(self, input_val, input_units, output_units, expected):
        result = find_input_units(input_val, input_units, output_units)
        assert pytest.approx(result[0], abs=1e-2) == expected[0]
        assert result[1] == expected[1]

    @pytest.mark.parametrize(
        "input_val,input_units,output_units,expected",
        [
            (1.0, "B", "km/h", (0.5399568034557235, "kt")),
            (
                xr.DataArray([1.0, 2.0]),
                "B",
                "km/h",
                (xr.DataArray([0.5399568, 1.07991361]), "kt"),
            ),
            (1.0, "B", "truc", (None, None)),
        ],
    )
    def test_find_output_units(self, input_val, input_units, output_units, expected):
        result = find_output_units(input_val, input_units, output_units)
        assert pytest.approx(result[0], abs=1e-2) == expected[0]
        assert result[1] == expected[1]

    @pytest.mark.parametrize(
        "input_value,output_units,context,expected",
        [
            ((1.0, "m"), "cm", None, 100.0),
            ((1.0, "kg/m^2"), "g/m^2", None, 1000.0),
            ((1.0, "cm"), "cm", None, 1.0),
            ((100.0, "km/h"), "B", None, np.int64(10)),
            ((10.0, "B"), "km/h", None, 10.0),
            (
                xr.DataArray([100.0, 200.0], attrs={"units": "cm"}),
                "m",
                None,
                xr.DataArray([1.0, 2.0], attrs={"units": "m"}),
            ),
            # (
            #    xr.DataArray([100.0, 200.0], attrs={"units": "km/h"}),
            #    "B",
            #    None,
            #    xr.DataArray([10.0, 12.0], attrs={"units": "B"}),
            # ),
            (
                xr.DataArray([10.0, 20.0], attrs={"units": "B"}),
                "km/h",
                None,
                xr.DataArray([10.0, 20.0], attrs={"units": "km/h"}),
            ),
            (
                xr.DataArray([4, 10, 20, 24], attrs={"units": "w1"}),
                "wwmf",
                None,
                xr.DataArray([38, 52, 77, 91], attrs={"units": "wwmf"}),
            ),
            # Context
            (
                xr.DataArray([1.0], attrs={"units": "mm"}, name="PRECIP24__SOL"),
                "kg m**-2 s**-1",
                None,
                xr.DataArray(
                    [1.0], attrs={"units": "kg m**-2 s**-1"}, name="PRECIP24__SOL"
                ),
            ),
            (
                xr.DataArray(
                    [10.0], attrs={"units": "kg m**-2 s**-1"}, name="NEIPOT12__SOL"
                ),
                "mm",
                None,
                xr.DataArray([100.0], attrs={"units": "mm"}, name="NEIPOT12__SOL"),
            ),
            ((1.0, "mm"), "kg m**-2 s**-1", "precipitation", 1.0),
            ((10.0, "kg m**-2 s**-1"), "mm", "snow", 100.0),
        ],
    )
    def test_unit_conversion(self, input_value, output_units, context, expected):
        result = unit_conversion(input_value, output_units, context=context)
        assert_identically_close(result, expected)

    def test_unit_conversion_fails(self):
        with pytest.raises(ValueError):
            _ = unit_conversion((1.0, "truc1"), "truc2")

        with pytest.raises(ValueError):
            _ = unit_conversion(xr.DataArray([1.0], attrs={"units": "truc1"}), "truc2")

        # No context
        with pytest.raises(ValueError):
            _ = unit_conversion(
                xr.DataArray([1.0], attrs={"units": "mm"}), "kg m**-2 s**-1"
            )
        with pytest.raises(ValueError):
            _ = unit_conversion((1.0, "mm"), "kg m**-2 s**-1")
        with pytest.raises(ValueError):
            _ = unit_conversion((1.0, "mm"), "kg m**-2 s**-1", context="random")
