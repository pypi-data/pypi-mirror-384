import os
import json
import pytest
from unittest.mock import patch
from tests.utils import fixtures_path, fake_new_product

from hestia_earth.models.hestia.aboveGroundCropResidue import MODEL, MODEL_KEY, run, _should_run

class_path = f"hestia_earth.models.{MODEL}.{MODEL_KEY}"
fixtures_folder = f"{fixtures_path}/{MODEL}/{MODEL_KEY}"
_folders = [d for d in os.listdir(fixtures_folder) if os.path.isdir(os.path.join(fixtures_folder, d))]


@patch(f"{class_path}._is_term_type_incomplete", return_value=True)
def test_should_run(*args):
    cycle = {'products': []}

    # no products => no run
    should_run, *args = _should_run(cycle)
    assert not should_run

    # product with total crop residue => run
    with open(f"{fixtures_folder}/with-total/cycle.jsonld", encoding='utf-8') as f:
        cycle = json.load(f)
    should_run, *args = _should_run(cycle)
    assert should_run is True


@pytest.mark.parametrize('folder', _folders)
@patch(f"{class_path}._is_term_type_incomplete", return_value=True)
@patch(f"{class_path}._new_product", side_effect=fake_new_product)
def test_run(mock_new_product, mock_complete, folder: str):
    with open(f"{fixtures_folder}/{folder}/cycle.jsonld", encoding='utf-8') as f:
        cycle = json.load(f)

    with open(f"{fixtures_folder}/{folder}/result.jsonld", encoding='utf-8') as f:
        expected = json.load(f)

    value = run(cycle)
    assert value == expected, folder
