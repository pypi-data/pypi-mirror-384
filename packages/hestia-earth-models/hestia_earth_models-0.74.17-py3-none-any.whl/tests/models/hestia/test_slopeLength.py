from unittest.mock import patch, Mock

from hestia_earth.models.hestia.slopeLength import run

class_path = 'hestia_earth.models.hestia.slopeLength'


@patch(f"{class_path}.related_cycles")
def test_not_run(mock_related_cycles: Mock):
    mock_related_cycles.return_value = [
        {'products': [{'primary': True, 'term': {'@id': 'wheatGrain'}}]}
    ]
    result = run({})
    assert not result


@patch(f"{class_path}.related_cycles")
def test_run(mock_related_cycles: Mock):
    mock_related_cycles.return_value = [
        {'products': [{'primary': True, 'term': {'@id': 'riceGrainInHuskFlooded'}}]}
    ]
    result = run({})
    assert result[0]['value'] == [0]
