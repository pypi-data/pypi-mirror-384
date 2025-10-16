from hestia_earth.models.cycle.completeness.excreta import run, MODEL_KEY

class_path = f"hestia_earth.models.cycle.completeness.{MODEL_KEY}"


def test_run():
    cycle = {}

    # not on cropland => no complete
    assert not run(cycle)

    # on cropland => complete
    cycle['site'] = {'siteType': 'cropland'}
    assert run(cycle) is True
