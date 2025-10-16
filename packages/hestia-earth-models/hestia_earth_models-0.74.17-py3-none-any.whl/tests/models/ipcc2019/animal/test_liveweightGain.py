from unittest.mock import patch
import json
from tests.utils import fixtures_path, fake_new_property

from hestia_earth.models.ipcc2019 import MODEL
from hestia_earth.models.ipcc2019.animal.liveweightGain import TERM_ID, run

utils_path = '.'.join(['hestia_earth', 'models', MODEL, 'animal', 'utils'])
class_path = f"hestia_earth.models.{MODEL}.animal.{TERM_ID}"
fixtures_folder = f"{fixtures_path}/{MODEL}/animal/{TERM_ID}"


@patch(f"{utils_path}._new_property", side_effect=fake_new_property)
def test_run(*args):
    with open(f"{fixtures_folder}/cycle.jsonld", encoding='utf-8') as f:
        cycle = json.load(f)

    with open(f"{fixtures_folder}/result.jsonld", encoding='utf-8') as f:
        expected = json.load(f)

    value = run(cycle)
    assert value == expected
