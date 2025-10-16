from unittest.mock import patch

from hestia_earth.earth_engine.gadm import EEType, run, get_distance_to_coordinates, get_id_by_coordinates

class_path = 'hestia_earth.earth_engine.gadm'
fake_results = [10]


@patch(f"{class_path}.load_region_geometry", return_value={})
@patch(f"{class_path}.batch_results", return_value=fake_results)
def test_run_vector(*args):
    results = run({
        'ee_type': EEType.VECTOR.value,
        'collections': [
            {'collection': '1', 'fields': 'a'},
            {'collection': '1', 'fields': 'b'}
        ],
        'gadm-ids': ['id1', 'id2']
    })
    assert results == fake_results


@patch(f"{class_path}.load_region_geometry", return_value={})
@patch(f"{class_path}.bands_from_collections", return_value=[])
@patch(f"{class_path}.combine_reducers", return_value=[])
@patch(f"{class_path}.batch_results", return_value=fake_results)
def test_run_raster(*args):
    results = run({
        'ee_type': EEType.RASTER.value,
        'collections': [
            {'collection': '1', 'fields': 'a'},
            {'collection': '1', 'fields': 'b'}
        ],
        'gadm-ids': ['id1', 'id2']
    })
    assert results == fake_results


class FakeInfo:
    def getInfo(*args):
        return {}


class FakeBounds:
    def first(*args):
        return FakeBounds()

    def get(*args):
        return FakeInfo()


class FakeGeometry:
    def distance(*args):
        return FakeInfo()


class FakeRegion:
    def geometry(*args):
        return FakeGeometry()

    def filterBounds(*args):
        return FakeBounds()


@patch(f"{class_path}.get_point", return_value={})
@patch(f"{class_path}.load_region_geometry", return_value=FakeGeometry)
def test_get_distance_to_coordinates(mock_load, *args):
    get_distance_to_coordinates('gadm_id', 10, -10)
    mock_load.assert_called_once()


@patch(f"{class_path}.get_point", return_value={})
@patch(f"{class_path}.load_region", return_value=FakeRegion)
def test_get_id_by_coordinates(mock_load, *args):
    get_id_by_coordinates(1, 10, -10)
    mock_load.assert_called_once()
