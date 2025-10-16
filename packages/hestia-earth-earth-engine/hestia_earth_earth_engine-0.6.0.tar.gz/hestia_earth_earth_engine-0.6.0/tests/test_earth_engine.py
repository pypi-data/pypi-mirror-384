from unittest.mock import patch

from hestia_earth.earth_engine import run

class_path = 'hestia_earth.earth_engine'


@patch(f"{class_path}.run_boundary")
def test_run_boundary(mock_run, *args):
    run({'boundaries': [1]})
    mock_run.assert_called_once()


@patch(f"{class_path}.run_coordinates")
def test_run_coordinates(mock_run, *args):
    run({'coordinates': [{'latitude': 1, 'longitude': 1}]})
    mock_run.assert_called_once()


@patch(f"{class_path}.run_gadm")
def test_run_gadm(mock_run, *args):
    run({'gadm-ids': ['GADM-GBR']})
    mock_run.assert_called_once()
