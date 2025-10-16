from hestia_earth.models.impact_assessment.post_checks.remove_cache_fields import run


def test_run():
    impact = {'cache': {}, 'added': ['cache']}
    assert run(impact) == {'added': []}
