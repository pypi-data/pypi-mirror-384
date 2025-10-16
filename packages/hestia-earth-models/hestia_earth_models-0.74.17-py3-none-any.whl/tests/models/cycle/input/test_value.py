import json
from tests.utils import fixtures_path

from hestia_earth.models.cycle.input.value import MODEL_KEY, run, _should_run

class_path = f"hestia_earth.models.cycle.input.{MODEL_KEY}"
fixtures_folder = f"{fixtures_path}/cycle/input/{MODEL_KEY}"


def test_should_run():
    input = {}

    # without min/max => NO run
    assert not _should_run({})(input)

    # with min and max and value => NO run
    input = {
        'min': [5],
        'max': [50],
        'value': [25]
    }
    assert not _should_run({})(input)

    # with min and max but not value => run
    input = {
        'min': [5],
        'max': [10],
        'value': []
    }
    assert _should_run({})(input) is True


def test_run():
    with open(f"{fixtures_folder}/cycle.jsonld", encoding='utf-8') as f:
        cycle = json.load(f)

    with open(f"{fixtures_folder}/result.jsonld", encoding='utf-8') as f:
        expected = json.load(f)

    result = run(cycle)
    assert result == expected
