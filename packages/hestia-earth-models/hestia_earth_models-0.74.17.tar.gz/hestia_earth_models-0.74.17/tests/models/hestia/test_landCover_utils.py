import pytest

from hestia_earth.models.hestia.utils import (
    FOREST_LAND, PERMANENT_PASTURE, PERMANENT_CROPLAND, ANNUAL_CROPLAND, OTHER_LAND
)
from hestia_earth.models.hestia.landCover_utils import (
    _get_changes, _estimate_maximum_forest_change,
    _site_area_sum_to_100, _get_sums_of_crop_expansion, _get_sum_for_land_category, _scale_values_to_one,
    _get_most_common_or_alphabetically_first, _get_land_cover_lookup_suffix, _get_ratio_between_land_use_types
)


@pytest.mark.parametrize(
    "terms,expected_output",
    [
        (   # Only term
            ["Annual crops", "Annual crops"],
            "Annual crops"
        ),
        (  # Most common
            ["Perennial crops", "Perennial crops", "Annual crops"],
            "Perennial crops"
        ),
        (   # Tied frequency, Alphabetically first
            ["Perennial crops", "Perennial crops", "Annual crops", "Annual crops"],
            "Annual crops"
        )
    ]
)
def test_get_most_common_or_alphabetically_first(terms, expected_output):
    actual_result = _get_most_common_or_alphabetically_first(terms)
    assert actual_result == expected_output


def test_get_changes():
    result, missing_values = _get_changes(
        country_id="GADM-AFG",
        reference_year=2010
    )
    assert (
        result == {
            "Arable land": -117.0,
            "Cropland": -123.0,
            "Forest land": 0,
            "Other land": 123.0,
            "Land area": 0,
            "Permanent crops": -6.0,
            "Permanent meadows and pastures": 0,
            "Total agricultural change": -123.0
        }
    )


@pytest.mark.parametrize(
    "description,inputs,expected_output",
    [
        (
            "Annual cropland gain from forest",
            {
                "forest_change": -1000,
                "total_cropland_change": 1000,
                "pasture_change": 0,
                "total_agricultural_change": 1000
            },
            -1000
        ),
        (
            "Pasture gain from forest",
            {
                "forest_change": -1000,
                "total_cropland_change": 0,
                "pasture_change": 1000,
                "total_agricultural_change": 1000
            },
            -1000
        ),
        (
            "Brazil",
            {
                "forest_change": -77317,
                "total_cropland_change": 5201,
                "pasture_change": -8267,
                "total_agricultural_change": -3066
            },
            -5201
        ),
        (
            "Argentina",
            {
                "forest_change": -4990,
                "total_cropland_change": 11408,
                "pasture_change": -12705,
                "total_agricultural_change": -1297
            },
            -4990
        ),
        (
            "Madagascar",
            {
                "forest_change": -1131,
                "total_cropland_change": 275,
                "pasture_change": 4295,
                "total_agricultural_change": 4570
            },
            -1131
        ),
        (
            "Afforestation",
            {
                "forest_change": 100,
                "total_cropland_change": -1000,
                "pasture_change": -50,
                "total_agricultural_change": -1000
            },
            0
        ),
        (
            "Pasture gain more than forest loss",
            {
                "forest_change": -49,
                "total_cropland_change": -1000,
                "pasture_change": 50,
                "total_agricultural_change": -950
            },
            -49
        )
    ]
)
def test_estimate_maximum_forest_change(description, inputs, expected_output):
    assert _estimate_maximum_forest_change(**inputs) == expected_output, description


@pytest.mark.parametrize(
    "description,inputs,expected_result",
    [
        ("All zeros, OK", {"a": 0, "b": 0, "c": 0.0, "d": 0.0}, True),
        ("Exactly 1, OK", {"a": 0.1, "b": 0.5, "c": 0.4, "d": 0.0}, True),
        ("Almost 1, OK", {"a": 0.1, "b": 0.5, "c": 0.4, "d": 0.01}, True),
        ("Less than 1, Fail", {"a": 0.1, "b": 0, "c": 0.0, "d": 0.65}, False),
        ("More than 1, Fail", {"a": 0.15, "b": 0.7, "c": 0.0, "d": 0.65}, False),
    ]
)
def test_check_sum_of_percentages(description, inputs, expected_result):
    assert _site_area_sum_to_100(dict_of_percentages=inputs) == expected_result


def test_get_sums_of_crop_expansion():
    result = _get_sums_of_crop_expansion(
        country_id="GADM-AFG",
        year=2010,
        include_negatives=True
    )
    assert result == (753973.3, 18354.0)

    result = _get_sums_of_crop_expansion(
        country_id="GADM-AFG",
        year=2010,
        include_negatives=False
    )
    assert result == (940270.0, 28139.0)


def test_get_sum_for_land_category():
    values = {
        "mangoes_guavas_and_mangosteens": "2022:5",
        "kiwi_fruit": "2020:4",
        "maize_corn": "2020:3",
        "other_beans_green": "2021:2",
        "olives": "2020:-1"
    }
    fao_stat_to_ipcc_type = {
            "mangoes_guavas_and_mangosteens": "Perennial crops",
            'kiwi_fruit': "Perennial crops",
            'maize_corn': "Annual crops",
            'other_beans_green': "Annual crops",
            'olives': "Perennial crops"
    }
    result = _get_sum_for_land_category(
        values=values,
        year=2020,
        ipcc_land_use_category="Perennial crops",
        fao_stat_to_ipcc_type=fao_stat_to_ipcc_type,
        include_negatives=True
    )
    assert result == 3.0


@pytest.mark.parametrize(
    "dictionary,expected_result",
    [
        (
            {"a": 0, "b": 0, "c": 0},
            {"a": 0, "b": 0, "c": 0}
        ),
        (
            {"a": 1000},
            {"a": 1}
        ),
        (
            {"a": 10, "b": 5, "c": 3},
            {"a": 0.5556, "b": 0.2778, "c": 0.1667}
        )
    ]
)
def test_scale_values_to_one(dictionary, expected_result):
    result = _scale_values_to_one(dictionary)
    for k, v in result.items():
        assert k in expected_result
        assert round(v, 3) == round(expected_result[k], 3)


@pytest.mark.parametrize(
    "land_type,expected",
    [
        (FOREST_LAND, "forest"),
        (ANNUAL_CROPLAND, "annualCropland"),
        (PERMANENT_CROPLAND, "permanentCropland"),
        (PERMANENT_PASTURE, "permanentPasture"),
        (OTHER_LAND, "otherLand"),
    ]
)
def test_get_land_cover_lookup_suffix(land_type: str, expected: str):
    assert _get_land_cover_lookup_suffix(land_type=land_type) == expected, land_type


def test_get_ratio_between_land_use_types():
    result = _get_ratio_between_land_use_types(
        country_id="GADM-ZWE",
        reference_year=2004,
        first_land_use_term="Arable land",
        second_land_use_term="Permanent crops"
    )
    assert result == (3800.0, 57.417)
