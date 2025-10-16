import os
import json
import pytest
from unittest.mock import patch
from tests.utils import fixtures_path, fake_new_management

from hestia_earth.models.log import logRequirements
from hestia_earth.models.hestia.utils import (
    FOREST_LAND, PERMANENT_PASTURE, PERMANENT_CROPLAND, ANNUAL_CROPLAND, OTHER_LAND, TOTAL_CROPLAND,
    TOTAL_AGRICULTURAL_CHANGE
)
from hestia_earth.models.hestia.landCover import MODEL, MODEL_KEY, run

class_path = f"hestia_earth.models.{MODEL}.{MODEL_KEY}"
class_path_utils = f"hestia_earth.models.{MODEL}.{MODEL_KEY}_utils"
fixtures_folder = f"{fixtures_path}/{MODEL}/{MODEL_KEY}"
_folders = [
    d for d in os.listdir(fixtures_folder)
    if os.path.isdir(os.path.join(fixtures_folder, d)) and not d.startswith("_")
]


@pytest.mark.parametrize("subfolder", _folders)
@patch(f"{class_path}._new_management", side_effect=fake_new_management)
def test_run(mock, subfolder: str):
    folder = f"{fixtures_folder}/{subfolder}"
    with open(f"{folder}/site.jsonld", encoding='utf-8') as f:
        site = json.load(f)

    with open(f"{folder}/result.jsonld", encoding='utf-8') as f:
        expected = json.load(f)

    result = run(site)
    print(json.dumps(result, indent=2))
    assert result == expected


@patch(f"{class_path}.logShouldRun")
@patch(f"{class_path}.logRequirements", wraps=logRequirements)
@patch(f"{class_path_utils}._get_changes")
@patch(f"{class_path}.get_site_area_from_lookups", return_value={})
@patch(f"{class_path}._new_management", side_effect=fake_new_management)
def test_run_missing_changes_logs(mock_new_mgt, mock_area, mock_get_changes, mock_logRequirements, mock_logShouldRun):
    fake_changes = {
        FOREST_LAND: 0, ANNUAL_CROPLAND: 10, PERMANENT_CROPLAND: 20, PERMANENT_PASTURE: 70, OTHER_LAND: 0,
        TOTAL_CROPLAND: 30, TOTAL_AGRICULTURAL_CHANGE: 100
    }
    mock_get_changes.return_value = (fake_changes, [FOREST_LAND])

    folder = f"{fixtures_folder}/malaysia"
    with open(f"{folder}/site.jsonld", encoding='utf-8') as f:
        site = json.load(f)

    _ = run(site)
    mock_logRequirements.assert_any_call(
        site,
        model=MODEL,
        term="oilPalmTree",
        model_key=MODEL_KEY,
        country_id="GADM-MYS",
        site_type_allowed=True,
        allowed_land_use_types='Arable land;Permanent crops;Permanent meadows and pastures;Cropland',
        land_use_type='Permanent crops',
        values="year:2010_isValid:False_percentage:0_term-id:annualCropland_changes:10_site-area:0_"
        "site-area-from-lookup:None_missing-changes:Forest land;year:2010_isValid:False_percentage:0_term-id:forest_"
        "changes:0_site-area:0_site-area-from-lookup:None_missing-changes:Forest land;year:2010_isValid:False_"
        "percentage:99.6_term-id:oilPalmTree_changes:20_site-area:0.9958907764054092_site-area-from-lookup:None_"
        "missing-changes:Forest land;year:2010_isValid:False_percentage:0.411_term-id:otherLand_changes:0_"
        "site-area:0.004109223594590805_site-area-from-lookup:None_missing-changes:Forest land;year:2010_"
        "isValid:False_percentage:0_term-id:permanentPasture_changes:70_site-area:0_site-area-from-lookup:None_"
        "missing-changes:Forest land"
    )

    mock_logShouldRun.assert_any_call(site, MODEL, "oilPalmTree", False, model_key=MODEL_KEY)


def _fake_region_lookup(*args, **kwargs):
    """Returns obviously-wrong mock results from Brazil to be distinct from model."""
    return ("2010:55.0")


@patch(f"{class_path_utils}.get_region_lookup_value", side_effect=_fake_region_lookup)
@patch(f"{class_path}._new_management", side_effect=fake_new_management)
def test_landCover_from_lookup_run(mock_mgmt, mock_region_lookup, caplog):
    folder = f"{fixtures_folder}/_from_lookups"
    with open(f"{folder}/site.jsonld", encoding='utf-8') as f:
        site = json.load(f)

    with open(f"{folder}/result.jsonld", encoding='utf-8') as f:
        expected = json.load(f)

    result = run(site)
    mock_region_lookup.assert_called_with(
        lookup_name='region-crop-cropGroupingFAOSTAT-landCover-otherLand.csv',
        term_id='GADM-BRA',
        column='Maize (corn)',
        model='hestia',
        model_key='landCover'
    )
    assert result == expected
