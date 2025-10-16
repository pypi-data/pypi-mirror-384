from shapely.geometry import shape as SHAshape

from mfire.mask.cardinal_mask import CardinalMasks


class TestCardinalMasks:
    def test_init_fails(self):
        pass

    def test_test_area(self):
        # Test with point
        geo = SHAshape({"type": "Point", "coordinates": [1, 1]})
        cm = CardinalMasks(geo, "parent_compass")
        assert cm.test_area(geo) is False

        # Test with Polygon
        geo = SHAshape(
            {
                "type": "Polygon",
                "coordinates": [[[1, 1], [1, 41], [81, 41], [81, 1], [1, 1]]],
            }
        )
        cm = CardinalMasks(geo, "parent_compass")

        # one sub zone ok
        sub = SHAshape(
            {
                "type": "Polygon",
                "coordinates": [[[1, 1], [1, 20], [20, 20], [20, 1], [1, 1]]],
            }
        )
        assert cm.test_area(sub) is True

        # the second sub zone too close of an existant subzone
        sub = SHAshape(
            {
                "type": "Polygon",
                "coordinates": [[[1, 1], [1, 20], [20, 20], [20, 1], [1, 1]]],
            }
        )
        cm.l_result = [sub]
        assert cm.test_area(sub) is False

        # sub zone too big compare to geo zone
        sub = SHAshape(
            {
                "type": "Polygon",
                "coordinates": [[[1, 1], [1, 41], [81, 41], [81, 1], [1, 1]]],
            }
        )
        assert cm.test_area(sub) is False

        # sub zone too small compare to geo zone
        sub = SHAshape(
            {
                "type": "Polygon",
                "coordinates": [[[1, 1], [1, 2], [2, 2], [2, 1], [1, 1]]],
            }
        )
        assert cm.test_area(sub) is False

    def test_get_rect_mask(self):
        geo = SHAshape(
            {
                "type": "Polygon",
                "coordinates": [[[1, 1], [1, 41], [81, 41], [81, 1], [1, 1]]],
            }
        )
        cm = CardinalMasks(geo, "parent_compass")
        lon_scale = 0.5
        lat_scale = 0.5
        origin = (41, 21)
        rslt = cm.get_rect_mask(lon_scale, lat_scale, origin)
        refpoly = "POLYGON ((21 11, 21 31, 61 31, 61 11, 21 11))"
        assert refpoly == str(rslt)

    def test_make_name(self):
        geo = SHAshape(
            {
                "type": "Polygon",
                "coordinates": [[[1, 1], [1, 4], [3, 4], [3, 1], [1, 1]]],
            }
        )
        cm = CardinalMasks(geo, "parent_compass")
        result = cm.make_name("Nord")
        assert result == "dans le Nord"
        result = cm.make_name("Ouest")
        assert result == "dans l'Ouest"
        result = cm.make_name("SmallSud")
        assert result == "dans une petite partie Sud"
        result = cm.make_name("SmallOuest")
        assert result == "dans une petite partie Ouest"

    def test_make_all_masks(self, assert_equals_result):
        geo_shape = SHAshape(
            {
                "type": "Polygon",
                "coordinates": [
                    [[0, 0.005], [0, 0.005], [0.005, 0.005], [0.005, 0], [0, 0]]
                ],
            }
        )
        cm = CardinalMasks(geo_shape, area_id="parent_compass")
        assert_equals_result(cm.all_masks)
