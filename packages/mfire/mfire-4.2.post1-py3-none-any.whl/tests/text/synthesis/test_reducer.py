import xarray as xr

from mfire.utils.date import Datetime
from tests.composite.factories import (
    FieldCompositeFactory,
    GeoCompositeFactory,
    SynthesisComponentCompositeFactory,
    SynthesisCompositeInterfaceFactory,
    SynthesisModuleFactory,
)
from tests.functions_test import assert_identically_close
from tests.text.synthesis.factories import SynthesisReducerFactory
from tests.utils.factories import PeriodDescriberFactory


class TestSynthesisReducer:
    def test_period_describer(self):
        period_describer = PeriodDescriberFactory()
        reducer = SynthesisReducerFactory(
            parent=SynthesisModuleFactory(
                parent=SynthesisComponentCompositeFactory(
                    period_describer_factory=period_describer
                )
            )
        )
        assert reducer.period_describer == period_describer

    def test_has_risk(self):
        weather_compo = SynthesisModuleFactory(
            weather_data_factory=lambda _: xr.DataArray(
                [0, 1, 2],
                coords={
                    "valid_time": [Datetime(2023, 3, 1, i).as_np_dt64 for i in range(3)]
                },
            ),
            geos=GeoCompositeFactory(all_sub_areas_factory=lambda _: ["Sub Areas"]),
            interface=SynthesisCompositeInterfaceFactory(
                has_risk=lambda x, y, z: (x, y, z)
            ),
        )
        reducer = SynthesisReducerFactory(parent=weather_compo)

        assert_identically_close(
            reducer.has_risk("Risk name"),
            (
                "Risk name",
                ["Sub Areas"],
                slice(
                    Datetime(2023, 3, 1).as_np_dt64, Datetime(2023, 3, 1, 2).as_np_dt64
                ),
            ),
        )

    def test_has_field(self):
        weather_compo = SynthesisModuleFactory(
            geos=GeoCompositeFactory(all_sub_areas_factory=lambda _: ["Sub Areas"]),
            interface=SynthesisCompositeInterfaceFactory(
                has_field=lambda x, y, z: (x, y, z)
            ),
        )
        reducer = SynthesisReducerFactory(parent=weather_compo)

        assert_identically_close(
            reducer.has_field("Risk name", "Field"),
            ("Risk name", "Field", ["Sub Areas"]),
        )

    def test_weather_data(self, assert_equals_result):
        lon, lat = [35], [40, 41, 42]
        ids = ["id1", "id2"]

        field = FieldCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[1.0, 2.0, 3.0]], coords={"longitude": lon, "latitude": lat}
            )
        )
        geos = GeoCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[[True, False, True]], [[False, True, False]]],
                coords={"id": ids, "longitude": lon, "latitude": lat},
            ),
            mask_id=ids,
        )

        reducer = SynthesisReducerFactory(
            geo_id="id1",
            parent=SynthesisModuleFactory(
                id="tempe", params={"tempe": field}, geos=geos
            ),
        )

        assert_equals_result(reducer.weather_data.to_dict())

    def test_weather_data_with_small_geos(self, assert_equals_result):
        lon, lat = [35], [40, 41, 42]
        ids = ["id"]

        field = FieldCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[1.0, 2.0, 3.0]], coords={"longitude": lon, "latitude": lat}
            )
        )
        geos = GeoCompositeFactory(
            compute_factory=lambda: xr.DataArray(
                [[[True]]], coords={"id": ids, "longitude": lon, "latitude": [41]}
            ),
            mask_id=ids,
        )

        reducer = SynthesisReducerFactory(
            geo_id="id",
            parent=SynthesisModuleFactory(
                id="tempe", params={"tempe": field}, geos=geos
            ),
        )

        assert_equals_result(reducer.weather_data.to_dict())
