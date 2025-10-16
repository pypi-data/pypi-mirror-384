from unittest.mock import patch
from tests.utils import TERM

from hestia_earth.models.utils.indicator import _new_indicator

class_path = 'hestia_earth.models.utils.indicator'


@patch(f"{class_path}.include_methodModel", side_effect=lambda n, x: n)
@patch(f"{class_path}.download_term", return_value=TERM)
def test_new_indicator(*args):
    # with a Term as string
    indicator = _new_indicator('term', value=0)
    assert indicator == {
        '@type': 'Indicator',
        'term': TERM,
        'value': 0
    }

    # with a Term as dict
    indicator = _new_indicator(TERM, value=0)
    assert indicator == {
        '@type': 'Indicator',
        'term': TERM,
        'value': 0
    }
