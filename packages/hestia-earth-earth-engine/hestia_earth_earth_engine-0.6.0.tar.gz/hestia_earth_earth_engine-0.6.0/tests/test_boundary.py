from unittest.mock import patch

from hestia_earth.earth_engine.boundary import EEType, run

class_path = 'hestia_earth.earth_engine.boundary'
fake_results = [10]


@patch(f"{class_path}.load_geometry", return_value={})
@patch(f"{class_path}.batch_results", return_value=fake_results)
def test_run_vector(*args):
    results = run({
        'ee_type': EEType.VECTOR.value,
        'collections': [
            {'collection': '1', 'fields': 'a'},
            {'collection': '1', 'fields': 'b'}
        ],
        'boundaries': [{}, {}]
    })
    assert results == fake_results


@patch(f"{class_path}.load_geometry", return_value={})
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
        'boundaries': [{}, {}]
    })
    assert results == fake_results
