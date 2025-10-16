from pathlib import Path
from unittest.mock import PropertyMock, patch

import pytest

import mfire.utils.mfxarray as xr
from mfire.composite.production import ProductionComposite
from mfire.settings import SETTINGS_DIR
from mfire.utils import recursive_format
from mfire.utils.date import Datetime
from mfire.utils.json import JsonFile
from tests.composite.factories import (
    EventCompositeFactory,
    FieldCompositeFactory,
    GeoCompositeFactory,
    LevelCompositeFactory,
    ProductionCompositeFactory,
    RiskComponentCompositeFactory,
    SynthesisComponentCompositeFactory,
    SynthesisModuleFactory,
)


class TestProductionComposite:
    inputs_dir: Path = Path(__file__).parent / "inputs"

    def test_init_shared(self):
        production = ProductionCompositeFactory(
            config_language="XXX",
            config_time_zone="YYY",
            components=[
                RiskComponentCompositeFactory(),
                SynthesisComponentCompositeFactory(),
            ],
        )

        expected = {"language": "XXX", "time_zone": "YYY"}
        assert production.shared_config == expected
        assert production.components[0].shared_config == expected
        assert production.components[1].shared_config == expected

    def test_sorted_components(self):
        production = ProductionCompositeFactory(
            components=[
                SynthesisComponentCompositeFactory(id="id_1"),
                RiskComponentCompositeFactory(id="id_2"),
                SynthesisComponentCompositeFactory(id="id_3"),
                RiskComponentCompositeFactory(id="id_4"),
            ]
        )
        assert [component.id for component in production.sorted_components] == [
            "id_2",
            "id_4",
            "id_1",
            "id_3",
        ]

    @pytest.mark.parametrize(
        "components,expected",
        [
            # No fog
            ([SynthesisComponentCompositeFactory()], None),
            ([RiskComponentCompositeFactory(hazard_name="Pluies")], None),
            (
                [
                    SynthesisComponentCompositeFactory(),
                    RiskComponentCompositeFactory(hazard_name="Pluies"),
                ],
                None,
            ),
            # No information about fog
            (
                [
                    RiskComponentCompositeFactory(
                        hazard_name="Brouillard",
                        final_risk_da_factory=xr.DataArray(
                            [[1]],
                            coords={
                                "valid_time": [Datetime(2023, 3, 1)],
                                "id": ["id3"],
                            },
                        ),
                    )
                ],
                None,
            ),
            (
                [
                    RiskComponentCompositeFactory(
                        hazard_name="Brouillard",
                        final_risk_da_factory=xr.DataArray(
                            [[1]],
                            coords={
                                "valid_time": [Datetime(2023, 2, 1)],
                                "id": ["id1"],
                            },
                        ),
                    )
                ],
                None,
            ),
            # Mist without occurrence
            (
                [
                    RiskComponentCompositeFactory(
                        hazard_name="Brouillard",
                        final_risk_da_factory=xr.DataArray(
                            [[0]],
                            coords={
                                "valid_time": [Datetime(2023, 3, 1)],
                                "id": ["id1"],
                            },
                        ),
                    )
                ],
                False,
            ),
            # Mist with occurrence
            (
                [
                    SynthesisComponentCompositeFactory(),
                    RiskComponentCompositeFactory(hazard_name="Pluies"),
                    RiskComponentCompositeFactory(
                        hazard_name="Brouillard",
                        final_risk_da_factory=xr.DataArray(
                            [[1, 0]],
                            coords={
                                "valid_time": [Datetime(2023, 3, 1)],
                                "id": ["id1", "id2"],
                            },
                        ),
                    ),
                ],
                True,
            ),
            (
                [
                    SynthesisComponentCompositeFactory(),
                    RiskComponentCompositeFactory(hazard_name="Pluies"),
                    RiskComponentCompositeFactory(
                        hazard_name="Brouillard",
                        final_risk_da_factory=xr.DataArray(
                            [[0, 1]],
                            coords={
                                "valid_time": [Datetime(2023, 3, 1)],
                                "id": ["id1", "id2"],
                            },
                        ),
                    ),
                ],
                True,
            ),
        ],
    )
    def test_has_risk(self, components, expected):
        valid_time = slice(Datetime(2023, 3, 1), Datetime(2023, 3, 1, 2))
        assert (
            ProductionCompositeFactory(components=components).has_risk(
                "Brouillard", valid_time=valid_time, ids=["id1", "id2"]
            )
            == expected
        )

    @pytest.mark.parametrize(
        "risk_infos, extreme_values, expected",
        [
            (
                {"pm_sep": False, "activated_risk": False, "plain_max": 10},
                {"pm_sep": False, "activated_risk": False},
                {"pm_sep": False, "activated_risk": False, "plain_max": 10},
            ),
            (
                {"pm_sep": False, "activated_risk": False},
                {"pm_sep": False, "activated_risk": False, "plain_max": 10},
                {"pm_sep": False, "activated_risk": False, "plain_max": 10},
            ),
            (
                {"pm_sep": False, "activated_risk": False, "mountain_max": 10},
                {"pm_sep": False, "activated_risk": False},
                {"pm_sep": False, "activated_risk": False, "mountain_max": 10},
            ),
            (
                {"pm_sep": False, "activated_risk": False},
                {"pm_sep": False, "activated_risk": False, "mountain_max": 10},
                {"pm_sep": False, "activated_risk": False, "mountain_max": 10},
            ),
            (
                {"pm_sep": False, "activated_risk": False},
                {"pm_sep": False, "activated_risk": False, "plain_max": None},
                {"pm_sep": False, "activated_risk": False},
            ),
            (
                {"pm_sep": False, "activated_risk": False},
                {"pm_sep": False, "activated_risk": False, "mountain_max": None},
                {"pm_sep": False, "activated_risk": False},
            ),
            (
                {"pm_sep": False, "activated_risk": False, "mountain_max": 10},
                {"pm_sep": True, "activated_risk": False},
                {"pm_sep": True, "activated_risk": False, "mountain_max": 10},
            ),
            (
                {"pm_sep": False, "activated_risk": False, "plain_max": 10},
                {"pm_sep": True, "activated_risk": False, "mountain_max": 20},
                {
                    "pm_sep": True,
                    "activated_risk": False,
                    "plain_max": 10,
                    "mountain_max": 20,
                },
            ),
            (
                {"pm_sep": False, "activated_risk": False, "plain_max": 10},
                {"pm_sep": False, "activated_risk": False, "plain_max": 10},
                {"pm_sep": False, "activated_risk": False, "plain_max": 10},
            ),
            (
                {"pm_sep": False, "activated_risk": False, "plain_max": 10},
                {"pm_sep": False, "activated_risk": False, "plain_max": 20},
                {"pm_sep": False, "activated_risk": False, "plain_max": 20},
            ),
            (
                {"pm_sep": False, "activated_risk": False, "mountain_max": 10},
                {"pm_sep": False, "activated_risk": False, "mountain_max": 20},
                {"pm_sep": False, "activated_risk": False, "mountain_max": 20},
            ),
            (
                {"pm_sep": False, "activated_risk": False, "mountain_max": 20},
                {"pm_sep": False, "activated_risk": False, "mountain_max": 20},
                {"pm_sep": False, "activated_risk": False, "mountain_max": 20},
            ),
            (
                {
                    "pm_sep": True,
                    "activated_risk": False,
                    "plain_max": 10,
                    "mountain_max": 30,
                },
                {
                    "pm_sep": True,
                    "activated_risk": False,
                    "plain_max": 40,
                    "mountain_max": 20,
                },
                {
                    "pm_sep": True,
                    "activated_risk": False,
                    "plain_max": 40,
                    "mountain_max": 30,
                },
            ),
            (
                {
                    "pm_sep": True,
                    "activated_risk": False,
                    "plain_max": 10,
                    "mountain_max": 30,
                },
                {
                    "pm_sep": True,
                    "activated_risk": False,
                    "plain_max": 40,
                    "mountain_max": 20,
                },
                {
                    "pm_sep": True,
                    "activated_risk": False,
                    "plain_max": 40,
                    "mountain_max": 30,
                },
            ),
            (
                {"pm_sep": False, "activated_risk": False, "plain_max": 10},
                {
                    "pm_sep": True,
                    "activated_risk": True,
                    "plain_max": 5,
                    "mountain_max": 20,
                },
                {
                    "pm_sep": True,
                    "activated_risk": True,
                    "plain_max": 5,
                    "mountain_max": 20,
                },
            ),
            (
                {"pm_sep": False, "activated_risk": True, "plain_max": 10},
                {
                    "pm_sep": True,
                    "activated_risk": False,
                    "plain_max": 5,
                    "mountain_max": 30,
                },
                {"pm_sep": True, "activated_risk": True, "plain_max": 10},
            ),
            (
                {"pm_sep": False, "activated_risk": False, "plain_min": 10},
                {"pm_sep": False, "activated_risk": False},
                {"pm_sep": False, "activated_risk": False, "plain_min": 10},
            ),
            (
                {"pm_sep": False, "activated_risk": False},
                {"pm_sep": False, "activated_risk": False, "plain_min": 10},
                {"pm_sep": False, "activated_risk": False, "plain_min": 10},
            ),
            (
                {"pm_sep": False, "activated_risk": False, "mountain_min": 10},
                {"pm_sep": False, "activated_risk": False},
                {"pm_sep": False, "activated_risk": False, "mountain_min": 10},
            ),
            (
                {"pm_sep": False, "activated_risk": False},
                {"pm_sep": False, "activated_risk": False, "mountain_min": 10},
                {"pm_sep": False, "activated_risk": False, "mountain_min": 10},
            ),
            (
                {"pm_sep": False, "activated_risk": False},
                {"pm_sep": False, "activated_risk": False, "plain_min": None},
                {"pm_sep": False, "activated_risk": False},
            ),
            (
                {"pm_sep": False, "activated_risk": False},
                {"pm_sep": False, "activated_risk": False, "mountain_min": None},
                {"pm_sep": False, "activated_risk": False},
            ),
            (
                {"pm_sep": False, "activated_risk": False, "mountain_min": 10},
                {"pm_sep": True, "activated_risk": False},
                {"pm_sep": True, "activated_risk": False, "mountain_min": 10},
            ),
            (
                {"pm_sep": False, "activated_risk": False, "plain_min": 10},
                {"pm_sep": True, "activated_risk": False, "mountain_min": 20},
                {
                    "pm_sep": True,
                    "activated_risk": False,
                    "plain_min": 10,
                    "mountain_min": 20,
                },
            ),
            (
                {"pm_sep": False, "activated_risk": False, "plain_min": 10},
                {"pm_sep": False, "activated_risk": False, "plain_min": 10},
                {"pm_sep": False, "activated_risk": False, "plain_min": 10},
            ),
            (
                {"pm_sep": False, "activated_risk": False, "plain_min": 10},
                {"pm_sep": False, "activated_risk": False, "plain_min": 20},
                {"pm_sep": False, "activated_risk": False, "plain_min": 10},
            ),
            (
                {"pm_sep": True, "activated_risk": False, "mountain_min": 10},
                {"pm_sep": True, "activated_risk": False, "mountain_min": 20},
                {"pm_sep": True, "activated_risk": False, "mountain_min": 10},
            ),
            (
                {"pm_sep": True, "activated_risk": False, "mountain_min": 20},
                {"pm_sep": True, "activated_risk": False, "mountain_min": 20},
                {"pm_sep": True, "activated_risk": False, "mountain_min": 20},
            ),
            (
                {
                    "pm_sep": True,
                    "activated_risk": False,
                    "plain_min": 10,
                    "mountain_min": 30,
                },
                {
                    "pm_sep": True,
                    "activated_risk": False,
                    "plain_min": 40,
                    "mountain_min": 20,
                },
                {
                    "pm_sep": True,
                    "activated_risk": False,
                    "plain_min": 10,
                    "mountain_min": 20,
                },
            ),
            (
                {
                    "pm_sep": False,
                    "activated_risk": False,
                    "plain_min": 10,
                    "mountain_min": 30,
                },
                {
                    "pm_sep": True,
                    "activated_risk": False,
                    "plain_min": 40,
                    "mountain_min": 20,
                },
                {
                    "pm_sep": True,
                    "activated_risk": False,
                    "plain_min": 10,
                    "mountain_min": 20,
                },
            ),
            (
                {
                    "pm_sep": True,
                    "activated_risk": False,
                    "plain_min": 10,
                    "mountain_min": 30,
                },
                {
                    "pm_sep": True,
                    "activated_risk": True,
                    "plain_min": 40,
                    "mountain_min": 50,
                },
                {
                    "pm_sep": True,
                    "activated_risk": True,
                    "plain_min": 40,
                    "mountain_min": 50,
                },
            ),
            (
                {
                    "pm_sep": True,
                    "activated_risk": True,
                    "plain_min": 10,
                    "mountain_min": 20,
                },
                {
                    "pm_sep": True,
                    "activated_risk": False,
                    "plain_min": 5,
                    "mountain_min": 30,
                },
                {
                    "pm_sep": True,
                    "activated_risk": True,
                    "plain_min": 10,
                    "mountain_min": 20,
                },
            ),
            (
                {
                    "pm_sep": True,
                    "activated_risk": True,
                    "plain_min": 10,
                    "plain_max": 50,
                    "mountain_min": 20,
                    "mountain_max": 60,
                },
                {
                    "pm_sep": True,
                    "activated_risk": True,
                    "plain_min": 5,
                    "mountain_min": 30,
                    "mountain_max": 100,
                    "extra_key": 100,
                },
                {
                    "pm_sep": True,
                    "activated_risk": True,
                    "plain_min": 5,
                    "plain_max": 50,
                    "mountain_min": 20,
                    "mountain_max": 100,
                },
            ),
            (
                {
                    "pm_sep": False,
                    "activated_risk": False,
                    "plain_min": 10,
                    "plain_max": 50,
                },
                {
                    "pm_sep": False,
                    "activated_risk": False,
                    "plain_min": 5,
                    "extra_key": 100,
                },
                {
                    "pm_sep": False,
                    "activated_risk": False,
                    "plain_min": 5,
                    "plain_max": 50,
                },
            ),
        ],
    )
    def test_update_risk_infos(self, risk_infos, extreme_values, expected):
        ProductionComposite.update_risk_infos(
            risk_infos, extreme_values, ["min", "max"]
        )
        assert "pm_sep" in risk_infos
        assert "activated_risk" in risk_infos
        assert risk_infos == expected

    @pytest.mark.parametrize(
        "hazard_names, conf",
        [
            (
                # "GUST" field_name of RiskComponentComposite (with critical values)
                # mismatches with the targeted field_name "RAF__HAUTEUR10"
                # -> empty returned risk_infos
                ["Rafales"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Rafales",
                        "field_name": "GUST",  # mismatches
                        "is_multizone": True,
                        "pm_sep": False,
                        "risk_infos": {},
                        "critical_values": {
                            "RAF__HAUTEUR10": {
                                "plain": {"value": 66.0, "occurrence": True}
                            }
                        },
                    }
                ],
            ),
            (
                # "GUST" hazard_name of RiskComponentComposite (with risk_infos)
                # mismatches with the looked hazard_name "RAF__HAUTEUR10"
                # -> empty returned risk_infos
                ["Rafales"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Gust",  # mismatches
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": False,
                        "pm_sep": False,
                        "risk_infos": {"activated_risk": False, "plain_max": 53.0},
                        "critical_values": {},
                    }
                ],
            ),
            # hazard_name and field_name match but risk_infos and critical_values conf
            # are empty -> empty returned risk_infos
            (
                ["Rafales"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Rafales",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": False,
                        "pm_sep": False,
                        "risk_infos": {"activated_risk": False},
                        "critical_values": {},
                    }
                ],
            ),
            # hazard_name and field_name match, risk_infos not empy and
            # critical_values conf are empty -> returned risk_infos contains
            # only the elements of input risk_infos
            (
                ["Rafales"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Rafales",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": False,
                        "pm_sep": True,
                        "risk_infos": {
                            "activated_risk": False,
                            "mountain_max": 53.0,
                            "mountain_min": 42.0,
                            "plain_max": 39.0,
                            "plain_min": 30.0,
                        },
                        "critical_values": {},
                    }
                ],
            ),
            # hazard_name and field_name match, risk_infos is empy and
            # critical_values conf are not empty -> returned risk_infos contains
            # only the elements of input critical_values
            (
                ["Rafales"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Rafales",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": True,
                        "pm_sep": True,
                        "risk_infos": {},
                        "critical_values": {
                            "RAF__HAUTEUR10": {
                                "plain": {"value": 66.0, "occurrence": True},
                                "mountain": {"value": 94.0, "occurrence": True},
                            }
                        },
                    }
                ],
            ),
            # hazard_name and field_name match, risk_infos contains only pm_sep and
            # critical_values conf are not empty -> returned risk_infos contains
            # the elements of input critical_values and pm_sep
            (
                ["Rafales"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Rafales",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": True,
                        "pm_sep": False,
                        "risk_infos": {},
                        "critical_values": {
                            "RAF__HAUTEUR10": {
                                "plain": {"value": 66.0, "occurrence": True}
                            }
                        },
                    }
                ],
            ),
            # hazard_name and field_name match with the given RiskComponentComposite
            (
                ["Rafales"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Rafales",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": False,
                        "pm_sep": True,
                        "risk_infos": {
                            "activated_risk": False,
                            "mountain_max": 53.0,
                            "mountain_min": 42.0,
                            "plain_max": 72.0,
                            "plain_min": 30.0,
                        },
                        "critical_values": {},
                    }
                ],
            ),
            # hazard_name and field_name match with the 2 given RiskComponentComposite
            (
                ["Rafales"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Rafales",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": False,
                        "pm_sep": False,
                        "risk_infos": {
                            "activated_risk": False,
                            "plain_max": 52.0,
                            "plain_min": 30.0,
                        },
                        "critical_values": {},
                    },
                    {
                        "synth_geo_id": "id2",
                        "hazard_name": "Rafales",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": True,
                        "pm_sep": True,
                        "risk_infos": {},
                        "critical_values": {
                            "RAF__HAUTEUR10": {
                                "plain": {"value": 66.0, "occurrence": True},
                                "mountain": {"value": 105.0, "occurrence": True},
                            }
                        },
                    },
                ],
            ),
            (
                # hazard_names and field_name match with the 2 given
                # RiskComponentComposite
                ["Rafales", "Vent"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Rafales",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": False,
                        "pm_sep": True,
                        "risk_infos": {
                            "activated_risk": False,
                            "mountain_max": 53.0,
                            "mountain_min": 42.0,
                            "plain_max": 39.0,
                            "plain_min": 30.0,
                        },
                        "critical_values": {},
                    },
                    {
                        "synth_geo_id": "id2",
                        "hazard_name": "Vent",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": True,
                        "pm_sep": False,
                        "risk_infos": {},
                        "critical_values": {
                            "RAF__HAUTEUR10": {
                                "mountain": {"value": 105.0, "occurrence": True}
                            }
                        },
                    },
                ],
            ),
            (
                # hazard_names and field_name match with the 2 given
                # RiskComponentComposite
                ["Rafales", "Vent"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Rafales",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": False,
                        "pm_sep": True,
                        "risk_infos": {
                            "activated_risk": False,
                            "mountain_max": 53.0,
                            "mountain_min": 42.0,
                            "plain_max": 39.0,
                            "plain_min": 30.0,
                        },
                        "critical_values": {},
                    },
                    {
                        "synth_geo_id": "id2",
                        "hazard_name": "Vent",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": True,
                        "pm_sep": False,
                        "risk_infos": {},
                        "critical_values": {
                            "RAF__HAUTEUR10": {
                                "mountain": {"value": 105.0, "occurrence": True}
                            }
                        },
                    },
                ],
            ),
            (
                # hazard_names and field_name match with the 2 given
                # RiskComponentComposite
                ["Rafales", "Vent"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Rafales",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": False,
                        "pm_sep": True,
                        "risk_infos": {
                            "activated_risk": True,
                            "mountain_max": 53.0,
                            "mountain_min": 42.0,
                            "plain_max": 39.0,
                            "plain_min": 30.0,
                        },
                        "critical_values": {},
                    },
                    {
                        "synth_geo_id": "id2",
                        "hazard_name": "Vent",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": True,
                        "pm_sep": False,
                        "risk_infos": {},
                        "critical_values": {
                            "RAF__HAUTEUR10": {
                                "mountain": {"value": 105.0, "occurrence": True}
                            }
                        },
                    },
                ],
            ),
            (
                # "GUST" field_name of RiskComponentComposite (with a risk_infos)
                # mismatches with the targeted field_name "RAF__HAUTEUR10"
                # -> empty returned risk_infos
                ["Rafales"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Rafales",
                        "field_name": "GUST",  # mismatches
                        "is_multizone": False,
                        "pm_sep": True,
                        "risk_infos": {
                            "activated_risk": False,
                            "mountain_max": 78.0,
                            "plain_max": 53.0,
                        },
                        "critical_values": {},
                    }
                ],
            ),
            (
                # "GUST" hazard_name of RiskComponentComposite (with a critical values)
                # mismatches with the looked hazard_name "RAF__HAUTEUR10"
                # -> empty returned risk_infos
                ["Rafales"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Gust",  # mismatches
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": True,
                        "pm_sep": False,
                        "risk_infos": {},
                        "critical_values": {
                            "RAF__HAUTEUR10": {
                                "plain": {"value": 66.0, "occurrence": True}
                            }
                        },
                    }
                ],
            ),
            # hazard_name and field_name match, risk_infos contains only pm_sep and
            # critical_values conf are not empty -> returned risk_infos contains
            # the elements of input critical_values and pm_sep
            (
                ["Rafales"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Rafales",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": True,
                        "pm_sep": False,
                        "risk_infos": {},
                        "critical_values": {
                            "RAF__HAUTEUR10": {
                                "plain": {"value": 70.0, "occurrence": True}
                            }
                        },
                    }
                ],
            ),
            # hazard_name and field_name match, risk_infos contains only pm_sep and
            # critical_values conf are not empty but with occurrence as False
            # -> empty returned risk_infos
            (
                ["Rafales"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Rafales",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": True,
                        "pm_sep": False,
                        "risk_infos": {},
                        "critical_values": {
                            "RAF__HAUTEUR10": {
                                "plain": {"value": 70.0, "occurrence": False}
                            }
                        },
                    }
                ],
            ),
            # hazard_name and field_name match, risk_infos contains only pm_sep and
            # critical_values conf are not empty but with occurrence as False
            # -> empty returned risk_infos
            (
                ["Rafales"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Rafales",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": True,
                        "pm_sep": True,
                        "risk_infos": {},
                        "critical_values": {
                            "RAF__HAUTEUR10": {
                                "mountain": {"value": 70.0, "occurrence": False}
                            }
                        },
                    }
                ],
            ),
            # hazard_name and field_name match, risk_infos contains pm_sep as True and
            # critical_values has:
            # - plain value with risk (occurence is True)
            # - mountain value without risk (occurence is False)
            # -> both plain and mountain values are kept
            (
                ["Rafales"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Rafales",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": True,
                        "pm_sep": True,
                        "risk_infos": {},
                        "critical_values": {
                            "RAF__HAUTEUR10": {
                                "plain": {"value": 125.0, "occurrence": True},
                                "mountain": {"value": 132.0, "occurrence": False},
                            }
                        },
                    }
                ],
            ),
            # hazard_name and field_name match, risk_infos contains pm_sep as True and
            # critical_values has:
            # - plain value without risk (occurence is False)
            # - mountain value without risk (occurence is False)
            # -> no risk so both plain and mountain values are not kept
            (
                ["Rafales"],  # hazard_names
                [
                    {
                        "synth_geo_id": "id1",
                        "hazard_name": "Rafales",
                        "field_name": "RAF__HAUTEUR10",
                        "is_multizone": True,
                        "pm_sep": True,
                        "risk_infos": {},
                        "critical_values": {
                            "RAF__HAUTEUR10": {
                                "plain": {"value": 125.0, "occurrence": False},
                                "mountain": {"value": 132.0, "occurrence": False},
                            }
                        },
                    }
                ],
            ),
        ],
    )
    def test_get_risk_infos(self, hazard_names, conf: list[dict], assert_equals_result):
        # conf is a list of RiskComponentComposite configurations. For each risk
        # component. conf:
        # - hazard_name is its hazard_name
        # - "risk_infos" is the dict returning by its method get_risk_infos
        # - "critical_values" is the dict returning by risk_builder.get_critical_values
        # where risk_builder is its related RiskBuilder created by Manager
        def all_sub_areas(geo):
            # Factory of all_sub_areas method. It simulates that id3 synth_geo_id is the
            # union of id2 and id1 geo ids.
            if geo in ["id1", "id2"]:
                return [geo]
            if geo == "id3":
                return ["id1", "id2", geo]
            raise KeyError

        # Creation of a ProductionCompositeFactory with some
        # RiskComponentCompositeFactory (created with input conf) and with a
        # SynthesisComponentCompositeFactory
        production = ProductionCompositeFactory(
            components=[
                RiskComponentCompositeFactory(
                    hazard_name=elt["hazard_name"],
                    geos=[elt["synth_geo_id"]],
                    levels_factory=[
                        LevelCompositeFactory(
                            events_factory=[
                                EventCompositeFactory(
                                    geos=GeoCompositeFactory(
                                        all_sub_areas_factory=all_sub_areas
                                    ),
                                    field=FieldCompositeFactory(name=elt["field_name"]),
                                )
                            ]
                        )
                    ],
                    compute_factory=lambda: True,
                )
                for elt in conf
            ]
        )

        synth_geo_id: str = "id3"
        production.components.append(
            SynthesisComponentCompositeFactory(
                geos=[synth_geo_id],
                compute_factory=lambda: "not_null",
                weathers=[SynthesisModuleFactory()],
            )
        )

        class RiskMocker:
            """Class to mock the get_risk_infos and get_critical_values methods."""

            def __init__(self, confs: list[dict]):
                self.conf = confs

                for i, conf_elt in enumerate(self.conf):
                    if conf_elt["risk_infos"]:
                        self.conf[i]["risk_infos"]["pm_sep"] = self.conf[i]["pm_sep"]

            @classmethod
            def _get_boolean(cls, conf_elt: dict, key: str) -> bool:
                return conf_elt[key]

            @property
            def risk_infos(self) -> list[dict]:
                mocked_values = []

                for conf_elt in self.conf:
                    if conf_elt["is_multizone"] is False:
                        assert "activated_risk" in conf_elt["risk_infos"]
                        assert "pm_sep" in conf_elt["risk_infos"]
                        assert conf_elt["critical_values"] == {}

                        conf_cur = {"activated_risk": False, "pm_sep": False}
                        if conf_elt.get("field_name") == "RAF__HAUTEUR10":
                            conf_cur = conf_elt["risk_infos"]
                        mocked_values.append(conf_cur)

                return mocked_values

            @property
            def critical_values(self) -> list[dict]:
                mocked_values = []

                for conf_elt in self.conf:
                    if conf_elt["is_multizone"] is True:
                        assert conf_elt["risk_infos"] == {}

                        conf_cur = {}
                        if conf_elt.get("field_name") == "RAF__HAUTEUR10":
                            conf_cur = conf_elt["critical_values"]
                        mocked_values.append(conf_cur)

                return mocked_values

            @property
            def is_multizone(self) -> list[bool]:
                return [
                    self._get_boolean(conf_elt, "is_multizone")
                    for conf_elt in self.conf
                ]

            @property
            def pm_sep(self) -> list[bool]:
                return [self._get_boolean(conf_elt, "pm_sep") for conf_elt in self.conf]

        compo_mock: RiskMocker = RiskMocker(conf)

        with (
            patch(
                "mfire.text.risk.builder.RiskBuilder.compute",
                lambda builder: "Risque text",
            ),
            patch(
                "mfire.text.manager.Manager._compute_synthesis",
                lambda text_manager, geo_id: f"Texte type={text_manager.parent.type} "
                f"for geo {geo_id}",
            ),
        ):
            production.compute()

        # Here we mock get_risk_infos and is_plain_mountain_separated methods of
        # RiskComponentComposite and get_critical_values and is_multizone of
        # RiskBuilder
        with (
            patch(
                "mfire.composite.component.RiskComponentComposite.get_risk_infos"
            ) as compo_mock_risk_infos,
            patch(
                "mfire.text.risk.reducer.RiskReducer.get_critical_values"
            ) as builder_mock_critical_values,
            patch(
                "mfire.composite.component.RiskComponentComposite."
                "is_plain_mountain_separated"
            ) as compo_mock_sep,
            patch(
                "mfire.composite.component.RiskComponentComposite.replace_critical",
                lambda builder, d: (d["value"], d["value"]),
            ),
            patch(
                "mfire.text.risk.builder.RiskBuilder.is_multizone",
                new_callable=PropertyMock,
            ) as builder_mock_is_multizone,
        ):
            compo_mock_risk_infos.side_effect = compo_mock.risk_infos
            builder_mock_critical_values.side_effect = compo_mock.critical_values
            compo_mock_sep.side_effect = compo_mock.pm_sep
            builder_mock_is_multizone.side_effect = compo_mock.is_multizone

            # valid_time and data_types arguments are not used because of
            # get_critical_values's and get_risk_infos's mocks
            risk_infos = production.get_risk_infos(
                hazard_names,
                "RAF__HAUTEUR10",
                synth_geo_id,  # synth_geo_id
                slice(Datetime(2023, 3, 3).as_np_dt64),
                ["min", "max"],
            )

            # Format the result as a JSON with "input" and "output" keys
            res: dict = {
                "input": {"hazard_names": hazard_names, "conf": conf},
                "output": risk_infos,
            }

            assert_equals_result(res)

    def test_compute(self):
        production = ProductionCompositeFactory(
            components=[
                RiskComponentCompositeFactory(geos=["geo1"]),
                RiskComponentCompositeFactory(
                    geos=["geo2"],
                    compute_factory=lambda: xr.Dataset(
                        {"A": ("B", [1])},
                        coords={"B": [1]},  # we force to have non-empty risk
                    ),
                ),
                SynthesisComponentCompositeFactory(
                    geos=["geo3"], compute_factory=lambda: "not_null"
                ),
            ]
        )
        with patch(
            "mfire.text.manager.Manager.compute",
            lambda text_manager: f"Texte type={text_manager.parent.type}",
        ):
            assert production.compute() == [
                None,
                {"geo2": "Texte type=risk"},
                {"geo3": "Texte type=text"},
            ]

    @pytest.mark.parametrize("config", ["small_conf_text.json", "small_conf_risk.json"])
    def test_integration(self, root_path_cwd, config, assert_equals_result):
        # We need to CWD in root since we load an altitude field
        data = JsonFile(self.inputs_dir / config).load()
        data_prod = next(iter(data.values()))
        prod = ProductionComposite(
            **recursive_format(data_prod, values={"settings_dir": SETTINGS_DIR})
        )

        assert_equals_result(prod)
