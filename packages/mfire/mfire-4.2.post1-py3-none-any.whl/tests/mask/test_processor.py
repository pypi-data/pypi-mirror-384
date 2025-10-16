from pathlib import Path

import pytest
from shapely import box

import mfire.utils.mfxarray as xr
from mfire.mask.processor import GridProcessor
from mfire.settings.constants import LANGUAGES
from tests.functions_test import assert_identically_close
from tests.mask.factories import GridProcessorFactory, ProcessorFactory


class TestProcessor:
    def test_init_shared_config(self):
        processor = ProcessorFactory(
            config={"config_language": "xxx"}, _shared_config={}
        )
        assert processor.shared_config == {"language": "xxx"}

    def test_compute_fails(self):
        processor = ProcessorFactory(config={"config_language": "xxx"})
        with pytest.raises(
            ValueError,
            match='Data dictionary must include a "file" key specifying the output '
            "filename.",
        ):
            processor.compute()

    def test_compute(self, tmp_path):
        # With hash
        output_path = tmp_path / "folder1" / "file1.nc"
        ProcessorFactory(
            config={
                "config_language": "fr",
                "file": output_path,
                "mask_hash": "mask_hash",
            },
            merged_ds_factory=xr.Dataset({"grid": [True, False]}),
        ).compute()
        assert_identically_close(
            xr.open_dataset(output_path),
            xr.Dataset({"grid": [True, False]}, attrs={"md5sum": "mask_hash"}),
        )

        # Without hash
        output_path = tmp_path / "folder2" / "file2.nc"
        ProcessorFactory(
            config={"config_language": "fr", "file": output_path, "geos": "test"},
            merged_ds_factory=xr.Dataset({"grid": [True, False]}),
        ).compute()
        assert_identically_close(
            xr.open_dataset(output_path),
            xr.Dataset({"grid": [True, False]}, attrs={"md5sum": "098f6bcd"}),
        )


class TestGridProcessor:
    inputs_dir: Path = Path(__file__).parent / "inputs"

    def test_init_areas(self, assert_equals_result):
        # Test without axe
        assert GridProcessorFactory().areas == {
            "id1": {
                "name": "area_name1",
                "alt_name": "sur la zone",
                "type": "",
                "shape": box(-4.04, 47.04, -4, 47),
            }
        }

        # Test with axe
        assert_equals_result(
            GridProcessorFactory(
                features=[
                    {
                        "id": "id1",
                        "properties": {"name": "axe_name1", "is_axe": True},
                        "geometry": box(-4.04, 47.04, -4, 47),
                    }
                ]
            ).areas
        )

    def test_area_name(self):
        assert GridProcessor.area_name({"name": "nom"}) == "nom"
        assert GridProcessor.area_name({"label": "nom"}) == "nom"
        assert GridProcessor.area_name({"alt_label": "nom"}) == "nom"
        assert GridProcessor.area_name({"areaName": "nom"}) == "nom"
        assert GridProcessor.area_name({"area_name": "nom"}) == "nom"

        with pytest.raises(
            ValueError, match="Area name not found in properties dictionary"
        ):
            _ = GridProcessor.area_name({"notknownkey": "nom"})

    def test_alt_area_name(self, assert_equals_result):
        grid_processor = GridProcessorFactory()

        assert grid_processor.alt_area_name({"alt_label": "XXX_(YYY)"}) == "YYY"

        # Test extra_fields properties for foreign languages
        for language in LANGUAGES:
            if language == "fr":
                continue

            grid_processor.set_language(language)
            assert (
                grid_processor.alt_area_name(
                    {
                        "alt_label": "XXX_(YYY)",
                        "extra_fields": {f"field_inter_{language}": "ZZZ"},
                    }
                )
                == "ZZZ"
            )

        # Test translations of "on the area"
        assert_equals_result(
            {
                language: grid_processor.alt_area_name(
                    {"alt_label": "XXX", "label": "YYY"}
                )
                for language in grid_processor.iter_languages()
            }
        )

    def test_grid_da(self):
        assert GridProcessorFactory().grid_da.name == "franxl1s100"

    def test_centered_grid_da(self):
        # Test with already centered grid
        assert GridProcessorFactory().centered_grid_da.longitude.values[0] < 0

        # Test with not centered grid
        grid_proc = GridProcessorFactory(grid_name="glob01")
        assert grid_proc.grid_da.longitude.values[0] == 0
        assert grid_proc.centered_grid_da.longitude.values[0] == -180

    def test_lon_step(self):
        assert_identically_close(GridProcessorFactory().lon_step, 0.01)

    def test_lat_step(self):
        assert_identically_close(GridProcessorFactory().lat_step, -0.01)

    def test_bounds(self):
        grid_proc = GridProcessorFactory(
            features=[],
            areas={
                "id1": {"shape": box(-10, -5, -9, -4)},
                "id2": {"shape": box(14, -5, 15, -4)},
                "id3": {"shape": box(-10, 4, -9, 5)},
                "id4": {"shape": box(13, 4, 14, 5)},
            },
        )
        assert grid_proc.bounds == (-10, -5, 15, 5)

    def test_subgrid(self, assert_equals_result):
        assert_equals_result(GridProcessorFactory().subgrid.to_dict())

    def test_offset_lon(self):
        assert GridProcessorFactory().offset_lon == 196
        assert GridProcessorFactory(grid_name="glob01").offset_lon == 1760

    def test_offset_lat(self):
        assert GridProcessorFactory().offset_lat == 446
        assert GridProcessorFactory(grid_name="glob01").offset_lat == 430

    def test_str_tree(self, assert_equals_result):
        assert_equals_result(GridProcessorFactory().str_tree.geometries)

    def test_array(self, assert_equals_result):
        assert_equals_result(GridProcessorFactory().array)

    def test_compute(self, assert_equals_result):
        assert_equals_result(
            {
                "without_axe": GridProcessorFactory().compute().to_dict(),
                "with_axe": GridProcessorFactory(
                    features=[
                        {
                            "id": "id1",
                            "properties": {"name": "axe_name1", "is_axe": True},
                            "geometry": box(-4.04, 47.04, -4, 47),
                        }
                    ]
                )
                .compute()
                .to_dict(),
            }
        )
