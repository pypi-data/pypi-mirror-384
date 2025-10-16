import pytest

import mfire.utils.mfxarray as xr
from mfire.composite.event import Category
from mfire.production.dataset import CDPDataset, CDPParam, CDPSummary, CDPValueParam
from mfire.utils.date import Datetime
from tests.composite.factories import (
    EventCompositeFactory,
    LevelCompositeFactory,
    RiskComponentCompositeFactory,
)
from tests.production.factories import CDPSummaryFactory


class TestCDPValueParam:
    def test_from_composite_fails(self):
        with pytest.raises(ValueError, match="However we get {'A'}"):
            CDPValueParam.from_composite(
                xr.Dataset({"B": (["A"], [1])}, coords={"A": [1]})
            )

    def test_from_composite(self):
        # Test with non-empty 2 events
        ds = xr.Dataset(
            data_vars={
                "occurrence": (["id"], [1.0], {"units": "m"}),
                "density": (["id"], [2.0], {"units": "m"}),
                "summarized_density": (["id"], [3.0], {"units": "m"}),
                "risk_density": (["id"], [4.0], {"units": "m"}),
                "risk_summarized_density": (["id"], [5.0], {"units": "m"}),
                "occurrence_event": (["id"], [6.0], {"units": "m"}),
                "occurrence_plain": (["id"], [6.0], {"units": "m"}),
                "occurrence_mountain": (["id"], [6.0], {"units": "m"}),
                "weatherVarName": (
                    ["id", "evt"],
                    [["weather_var_name1", "weather_var_name2"]],
                ),
                "other_var": (["id"], [7.0], {"units": "m"}),
            },
            coords={
                "evt": [1, 2],
                "id": ["id"],
                "areaName": "area_name",
                "areaType": "area_type",
            },
        )

        result = CDPValueParam.from_composite(ds.sel(id="id"))
        assert result == [
            CDPValueParam(ValueType="density", Unit="1", Value=2.0, Param=None),
            CDPValueParam(ValueType="occurrence", Unit="1", Value=1.0, Param=None),
            CDPValueParam(
                ValueType="other_var",
                Unit="unknown",
                Value=7.0,
                Param=CDPParam(Name="weather_var_name1", Stepsize=None),
            ),
            CDPValueParam(
                ValueType="summarized_density", Unit="1", Value=3.0, Param=None
            ),
        ]

        # Test with 2 empty events
        ds = xr.Dataset(
            data_vars={"other_var": (["id", "evt"], [[1.0, 2.0]], {"units": "m"})},
            coords={"evt": [1, 2], "id": ["id"]},
        )

        assert not CDPValueParam.from_composite(ds.sel(id="id"))


class TestCDPSummary:
    valid_time = [Datetime(2023, 3, 1, i).as_np_dt64 for i in range(1, 4)]
    risk_compo = None

    def test_init_dates(self):
        cdp = CDPSummaryFactory(ValidityDate="2023-03-01")
        assert cdp.ValidityDate == Datetime(2023, 3, 1)

    def _init_test_from_composite(self, final_risk_da: xr.DataArray):
        ds = xr.Dataset(
            {
                "units": (["evt"], ["m"]),
                "occurrence": (
                    ["id", "evt", "risk_level", "valid_time"],
                    [[[[True] * 3] * 3]],
                    {"units": "m"},
                ),
                "summarized_density": (
                    ["id", "evt", "risk_level"],
                    [[[1.0, 2.0, 3.0]]],
                    {"units": "m"},
                ),
                "max_var": (
                    ["id", "evt", "risk_level", "valid_time"],
                    [[[[4.0, 5.0, 6.0], [7.0, 8.0, 9.0], [10.0, 11.0, 12.0]]]],
                    {"units": "m"},
                ),
                "min_var": (
                    ["id", "evt", "risk_level", "valid_time"],
                    [[[[13.0, 14.0, 15.0], [16.0, 17.0, 18.0], [19.0, 20.0, 21.0]]]],
                    {"units": "m"},
                ),
                "rep_value_plain": (
                    ["id", "evt", "risk_level", "valid_time"],
                    [[[[22.0, 23.0, 24.0], [25.0, 26.0, 27.0], [28.0, 29.0, 30.0]]]],
                    {"units": "m"},
                ),
                "weatherVarName": (
                    ["id", "evt", "risk_level"],
                    [[["weather_1", "weather_2", "weather_3"]]],
                ),
            },
            coords={
                "id": ["geo_id"],
                "evt": [1],
                "valid_time": self.valid_time,
                "risk_level": [1, 2, 3],
            },
        )

        self.risk_compo = RiskComponentCompositeFactory(
            data=ds,
            final_risk_da_factory=final_risk_da,
            percent_uncertainty_factory=lambda _: 50,
            levels=[
                LevelCompositeFactory(
                    level=1,
                    events=[EventCompositeFactory(category=Category.QUANTITATIVE)],
                ),
                LevelCompositeFactory(level=2),
                LevelCompositeFactory(level=3),
            ],
        )

    def test_from_composite_with_final_levels(self):
        self._init_test_from_composite(
            final_risk_da=xr.DataArray(
                [[1, 2, 3]], coords={"id": ["geo_id"], "valid_time": self.valid_time}
            )
        )

        result = CDPSummary.from_composite(self.risk_compo, geo_id="geo_id")
        assert result == CDPSummary(
            ValidityDate=None,
            Level=3,
            PercentUncertainty=50,
            CodeUncertainty=32,
            Values=[
                CDPValueParam(ValueType="density", Unit="1", Value=3.0, Param=None),
                CDPValueParam(
                    ValueType="max_var",
                    Unit="m",
                    Value=12.0,
                    Param=CDPParam(Name="weather_3", Stepsize=None),
                ),
                CDPValueParam(
                    ValueType="min_var",
                    Unit="m",
                    Value=21.0,
                    Param=CDPParam(Name="weather_3", Stepsize=None),
                ),
                CDPValueParam(ValueType="occurrence", Unit="1", Value=1.0, Param=None),
                CDPValueParam(
                    ValueType="rep_value_plain",
                    Unit="m",
                    Value=30.0,
                    Param=CDPParam(Name="weather_3", Stepsize=None),
                ),
            ],
        )

    def test_from_composite_without_final_levels(self):
        self._init_test_from_composite(
            final_risk_da=xr.DataArray(
                [[0, 0, 0]], coords={"id": ["geo_id"], "valid_time": self.valid_time}
            )
        )
        result = CDPSummary.from_composite(self.risk_compo, geo_id="geo_id")
        assert result == CDPSummary(
            ValidityDate=None,
            Level=0,
            PercentUncertainty=50,
            CodeUncertainty=12,
            Values=[
                CDPValueParam(ValueType="density", Unit="1", Value=1.0, Param=None),
                CDPValueParam(
                    ValueType="max_var",
                    Unit="m",
                    Value=6.0,
                    Param=CDPParam(Name="weather_1", Stepsize=None),
                ),
                CDPValueParam(
                    ValueType="min_var",
                    Unit="m",
                    Value=13.0,
                    Param=CDPParam(Name="weather_1", Stepsize=None),
                ),
                CDPValueParam(ValueType="occurrence", Unit="1", Value=1.0, Param=None),
                CDPValueParam(
                    ValueType="rep_value_plain",
                    Unit="m",
                    Value=24.0,
                    Param=CDPParam(Name="weather_1", Stepsize=None),
                ),
            ],
        )

    def test_list_from_composite(self):
        valid_time = [Datetime(2023, 3, 1, i).as_np_dt64 for i in range(1, 4)]

        risk_compo = RiskComponentCompositeFactory(
            data=xr.Dataset(
                {
                    "occurrence": (
                        ["id", "evt", "risk_level", "valid_time"],
                        [[[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]]],
                    )
                },
                coords={
                    "id": ["geo_id"],
                    "evt": [1],
                    "valid_time": valid_time,
                    "risk_level": [1, 2, 3],
                },
            ),
            final_risk_da_factory=xr.DataArray(
                [[1, 2, 3]], coords={"id": ["geo_id"], "valid_time": valid_time}
            ),
        )

        result = CDPSummary.list_from_composite(risk_compo, geo_id="geo_id")
        assert result == [
            CDPSummary(
                ValidityDate=Datetime(2023, 3, 1, 1),
                Level=1,
                Values=[
                    CDPValueParam(
                        ValueType="occurrence", Unit="1", Value=1.0, Param=None
                    )
                ],
            ),
            CDPSummary(
                ValidityDate=Datetime(2023, 3, 1, 2),
                Level=2,
                Values=[
                    CDPValueParam(
                        ValueType="occurrence", Unit="1", Value=5.0, Param=None
                    )
                ],
            ),
            CDPSummary(
                ValidityDate=Datetime(2023, 3, 1, 3),
                Level=3,
                Values=[
                    CDPValueParam(
                        ValueType="occurrence", Unit="1", Value=9.0, Param=None
                    )
                ],
            ),
        ]


class TestCDPDataset:
    def test_from_composite(self):
        # when risk is not computed
        risk_compo = RiskComponentCompositeFactory()
        assert CDPDataset.from_composite(risk_compo, geo_id="geo_id") == CDPDataset(
            ShortSummary=CDPSummary(Level=0, Values=[]), Summary=[]
        )

        # when risk is computed
        valid_time = [Datetime(2023, 3, 1, i).as_np_dt64 for i in range(1, 4)]
        risk_ds = xr.Dataset(
            {
                "occurrence": (
                    ["id", "evt", "risk_level", "valid_time"],
                    [[[[True] * 3] * 3]],
                    {"units": "m"},
                ),
                "summarized_density": (
                    ["id", "evt", "risk_level"],
                    [[[1.0, 2.0, 3.0]]],
                    {"units": "m"},
                ),
                "max_var": (
                    ["id", "evt", "risk_level", "valid_time"],
                    [[[[4.0, 5.0, 6.0], [7.0, 8.0, 9.0], [10.0, 11.0, 12.0]]]],
                    {"units": "m"},
                ),
                "min_var": (
                    ["id", "evt", "risk_level", "valid_time"],
                    [[[[13.0, 14.0, 15.0], [16.0, 17.0, 18.0], [19.0, 20.0, 21.0]]]],
                    {"units": "m"},
                ),
                "rep_value_plain": (
                    ["id", "evt", "risk_level", "valid_time"],
                    [[[[22.0, 23.0, 24.0], [25.0, 26.0, 27.0], [28.0, 29.0, 30.0]]]],
                    {"units": "m"},
                ),
                "weatherVarName": (
                    ["id", "evt", "risk_level"],
                    [[["weather_1", "weather_2", "weather_3"]]],
                ),
            },
            coords={
                "id": ["geo_id"],
                "evt": [1],
                "valid_time": valid_time,
                "risk_level": [1, 2, 3],
            },
        )

        risk_compo = RiskComponentCompositeFactory(
            data=risk_ds,
            final_risk_da_factory=xr.DataArray(
                [[1, 2, 3]], coords={"id": ["geo_id"], "valid_time": valid_time}
            ),
            levels=[
                LevelCompositeFactory(level=1),
                LevelCompositeFactory(level=2),
                LevelCompositeFactory(level=3),
            ],
            percent_uncertainty_factory=lambda _: 50,
        )

        result = CDPDataset.from_composite(risk_compo, geo_id="geo_id")
        assert result == CDPDataset(
            ShortSummary=CDPSummary(
                ValidityDate=None,
                Level=3,
                PercentUncertainty=50,
                CodeUncertainty=32,
                Values=[
                    CDPValueParam(ValueType="density", Unit="1", Value=3.0, Param=None),
                    CDPValueParam(
                        ValueType="max_var",
                        Unit="unknown",
                        Value=12.0,
                        Param=CDPParam(Name="weather_3", Stepsize=None),
                    ),
                    CDPValueParam(
                        ValueType="min_var",
                        Unit="unknown",
                        Value=21.0,
                        Param=CDPParam(Name="weather_3", Stepsize=None),
                    ),
                    CDPValueParam(
                        ValueType="occurrence", Unit="1", Value=1.0, Param=None
                    ),
                    CDPValueParam(
                        ValueType="rep_value_plain",
                        Unit="unknown",
                        Value=30.0,
                        Param=CDPParam(Name="weather_3", Stepsize=None),
                    ),
                ],
            ),
            Summary=[
                CDPSummary(
                    ValidityDate=Datetime(2023, 3, 1, 1),
                    Level=1,
                    Values=[
                        CDPValueParam(
                            ValueType="max_var",
                            Unit="unknown",
                            Value=4.0,
                            Param=CDPParam(Name="weather_1", Stepsize=1),
                        ),
                        CDPValueParam(
                            ValueType="min_var",
                            Unit="unknown",
                            Value=13.0,
                            Param=CDPParam(Name="weather_1", Stepsize=1),
                        ),
                        CDPValueParam(
                            ValueType="occurrence", Unit="1", Value=1.0, Param=None
                        ),
                        CDPValueParam(
                            ValueType="rep_value_plain",
                            Unit="unknown",
                            Value=22.0,
                            Param=CDPParam(Name="weather_1", Stepsize=1),
                        ),
                    ],
                ),
                CDPSummary(
                    ValidityDate=Datetime(2023, 3, 1, 2),
                    Level=2,
                    Values=[
                        CDPValueParam(
                            ValueType="max_var",
                            Unit="unknown",
                            Value=8.0,
                            Param=CDPParam(Name="weather_2", Stepsize=1),
                        ),
                        CDPValueParam(
                            ValueType="min_var",
                            Unit="unknown",
                            Value=17.0,
                            Param=CDPParam(Name="weather_2", Stepsize=1),
                        ),
                        CDPValueParam(
                            ValueType="occurrence", Unit="1", Value=1.0, Param=None
                        ),
                        CDPValueParam(
                            ValueType="rep_value_plain",
                            Unit="unknown",
                            Value=26.0,
                            Param=CDPParam(Name="weather_2", Stepsize=1),
                        ),
                    ],
                ),
                CDPSummary(
                    ValidityDate=Datetime(2023, 3, 1, 3),
                    Level=3,
                    Values=[
                        CDPValueParam(
                            ValueType="max_var",
                            Unit="unknown",
                            Value=12.0,
                            Param=CDPParam(Name="weather_3", Stepsize=1),
                        ),
                        CDPValueParam(
                            ValueType="min_var",
                            Unit="unknown",
                            Value=21.0,
                            Param=CDPParam(Name="weather_3", Stepsize=1),
                        ),
                        CDPValueParam(
                            ValueType="occurrence", Unit="1", Value=1.0, Param=None
                        ),
                        CDPValueParam(
                            ValueType="rep_value_plain",
                            Unit="unknown",
                            Value=30.0,
                            Param=CDPParam(Name="weather_3", Stepsize=1),
                        ),
                    ],
                ),
            ],
        )
