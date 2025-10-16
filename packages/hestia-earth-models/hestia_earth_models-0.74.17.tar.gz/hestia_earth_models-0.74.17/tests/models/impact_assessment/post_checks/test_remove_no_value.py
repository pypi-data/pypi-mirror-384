from hestia_earth.models.impact_assessment.post_checks.remove_no_value import run


def test_run():
    impacts = [
        {'value': 10},
        {'value': 0},
        {'value': None},
        {}
    ]
    impact = {'impacts': impacts}
    assert run(impact) == {
        'impacts': [
            {'value': 10},
            {'value': 0}
        ]
    }
