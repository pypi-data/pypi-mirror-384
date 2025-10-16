import geojson
from shapely import MultiPoint, Point

from tests.configuration.factories import FeatureCollectionFactory, FeatureConfigFactory
from tests.functions_test import assert_identically_close


class TestFeatureConfig:
    def test_init_geometry(self):
        # good init
        assert FeatureConfigFactory(geometry=None).geometry is None

        geometry = {"type": "Point", "coordinates": (0, 1)}
        assert_identically_close(
            FeatureConfigFactory(geometry=geometry).geometry, geometry
        )

        assert_identically_close(
            FeatureConfigFactory(geometry=MultiPoint([(0, 0), (0, 1)])).geometry,
            {"coordinates": ((0.0, 0.0), (0.0, 1.0)), "type": "MultiPoint"},
        )

        # bad inits
        assert (
            FeatureConfigFactory(geometry=geojson.Point((0, 1, 2, 3, 4))).geometry
            is None
        )
        assert (
            FeatureConfigFactory(
                geometry={"type": "LineString", "coordinates": [[0, 0], [0, 0]]}
            ).geometry
            is None
        )
        assert (
            FeatureConfigFactory(
                geometry={"type": "LineString", "coordinates": [[0, 0], [190, 0]]}
            ).geometry
            is None
        )
        assert (
            FeatureConfigFactory(
                geometry={"type": "LineString", "coordinates": [[0, 0], [0, 100]]}
            ).geometry
            is None
        )

    def test_init_name_property_from_label(self):
        feature = FeatureConfigFactory(
            properties={"label": "PROM_Axe1_(Axe 1)_(Nom axe 1)"}
        )
        assert feature.properties["name"] == "Nom axe 1"

        assert not FeatureConfigFactory().properties

    def test_shape(self):
        assert (
            str(
                FeatureConfigFactory(
                    geometry={"type": "Point", "coordinates": (0, 0)}
                ).shape
            )
            == "POINT (0 0)"
        )
        assert FeatureConfigFactory(geometry=None).shape is None


class TestFeatureCollection:
    def test_hash(self, assert_equals_result):
        assert_equals_result(FeatureCollectionFactory().hash)

    def test_init_features(self):
        features_conf = FeatureCollectionFactory(
            features=[FeatureConfigFactory(), FeatureConfigFactory(geometry=None)]
        )
        assert len(features_conf.features) == 1

    def test_centroid(self):
        centroid = FeatureCollectionFactory().centroid
        assert isinstance(centroid, Point)
        assert_identically_close(centroid.x, 13.40529)
        assert_identically_close(centroid.y, 52.47415)
