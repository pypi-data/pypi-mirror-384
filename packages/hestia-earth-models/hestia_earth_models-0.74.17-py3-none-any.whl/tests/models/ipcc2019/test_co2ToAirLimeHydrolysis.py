from unittest.mock import patch
import json
from tests.utils import fixtures_path, fake_new_emission

from hestia_earth.models.ipcc2019.co2ToAirLimeHydrolysis import MODEL, TERM_ID, run, _should_run

class_path = f"hestia_earth.models.{MODEL}.{TERM_ID}"
fixtures_folder = f"{fixtures_path}/{MODEL}/{TERM_ID}"


def test_should_run():
    # no inputs => no run
    cycle = {'inputs': []}
    should_run, *args = _should_run(cycle)
    assert not should_run

    # with kg CaCO3 input => no run
    cycle['inputs'].append({
        'term': {
            'units': 'kg CaCO3',
            'termType': 'soilAmendment'
        },
        'value': [100]
    })
    should_run, *args = _should_run(cycle)
    assert not should_run

    # with kg MgCO3 input => run
    cycle['inputs'].append({
        'term': {
            'units': 'kg CaMg(CO3)2',
            'termType': 'soilAmendment'
        },
        'value': [100]
    })
    should_run, *args = _should_run(cycle)
    assert should_run is True


@patch(f"{class_path}._new_emission", side_effect=fake_new_emission)
def test_run(*args):
    with open(f"{fixtures_folder}/cycle.jsonld", encoding='utf-8') as f:
        cycle = json.load(f)

    with open(f"{fixtures_folder}/result.jsonld", encoding='utf-8') as f:
        expected = json.load(f)

    value = run(cycle)
    assert value == expected
