from unittest.mock import patch
import json
from tests.utils import fixtures_path

from hestia_earth.models.cycle.completeness import run, _should_run_model

class_path = 'hestia_earth.models.cycle.completeness'
fixtures_folder = f"{fixtures_path}/cycle/completeness"
cropResidue = [
    'aboveGroundCropResidueRemoved', 'aboveGroundCropResidueIncorporated', 'aboveGroundCropResidueTotal',
    'aboveGroundCropResidueLeftOnField', 'aboveGroundCropResidueBurnt',
    'belowGroundCropResidue'
]


def test_should_run_model():
    key = 'cropResidue'
    model = {'key': key, 'run': lambda *args: True}
    cycle = {'completeness': {}}

    # already complete => no run
    cycle['completeness'][key] = True
    assert not _should_run_model(model, cycle)

    # not complete => run
    cycle['completeness'][key] = False
    assert _should_run_model(model, cycle)


@patch(f"{class_path}.cropResidue.get_crop_residue_terms", return_value=cropResidue)
def test_run(*args):
    with open(f"{fixtures_folder}/cycle.jsonld", encoding='utf-8') as f:
        cycle = json.load(f)

    with open(f"{fixtures_folder}/result.jsonld", encoding='utf-8') as f:
        expected = json.load(f)

    value = run(cycle)
    assert value == expected


@patch(f"{class_path}.cropResidue.get_crop_residue_terms", return_value=cropResidue)
def test_run_orchard(*args):
    with open(f"{fixtures_folder}/orchard/cycle.jsonld", encoding='utf-8') as f:
        cycle = json.load(f)

    with open(f"{fixtures_folder}/orchard/result.jsonld", encoding='utf-8') as f:
        expected = json.load(f)

    value = run(cycle)
    assert value == expected
