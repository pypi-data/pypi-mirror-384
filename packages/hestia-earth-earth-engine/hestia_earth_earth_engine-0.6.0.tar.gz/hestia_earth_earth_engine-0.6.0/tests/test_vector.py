import os
import json
from tests.utils import fixtures_path

from hestia_earth.earth_engine.utils.vector import run_by_boundaries, run_by_coordinates, run_by_gadm_ids


with open(os.path.join(fixtures_path, 'vector.json'), encoding='utf-8') as f:
    data = json.load(f)


def test_run_by_boundaries():
    assert run_by_boundaries(data.get('collections'), data.get('boundaries')) == ['5180', 'PA0445']


def test_run_by_coordinates():
    assert run_by_coordinates(data.get('collections'), data.get('coordinates')) == ['9692', 'NT0704']


def test_run_by_gadm_ids():
    assert run_by_gadm_ids(data.get('collections'), data.get('gadm-ids')) == ['10435', 'AA1309']
