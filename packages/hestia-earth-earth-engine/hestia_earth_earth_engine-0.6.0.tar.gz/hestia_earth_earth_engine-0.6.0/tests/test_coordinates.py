from unittest.mock import patch

from hestia_earth.earth_engine.coordinates import EEType, run

class_path = 'hestia_earth.earth_engine.coordinates'


@patch(f"{class_path}._run_vector_ee")
def test_run(mock_run, *args):
    values = [10, 11]
    mock_run.return_value = values
    results = run({
        'ee_type': EEType.VECTOR.value,
        'collections': [
            {'collection': '1'},
            {'collection': '1'}
        ],
        'coordinates': [{}, {}]
    })
    assert results == values
