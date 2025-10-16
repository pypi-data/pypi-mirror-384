import json
from os.path import isfile
from pytest import mark
from unittest.mock import patch, MagicMock

from hestia_earth.models.hestia.soilClassification import MODEL, run, _should_run

from tests.utils import fake_new_measurement, fixtures_path

NAME = "soilClassification"

class_path = f"hestia_earth.models.{MODEL}.{NAME}"
fixtures_folder = f"{fixtures_path}/{MODEL}/{NAME}"


def _load_fixture(file_name: str, default=None):
    path = f"{fixtures_folder}/{file_name}.jsonld"
    if isfile(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


# subfolder, should_run
PARAMS_SHOULD_RUN = [
    ("single-org-with-date", True),                              # Single histosol measurement, with date
    ("single-org-without-date", True),                           # Single histosol measurement, no date
    ("multiple-org-values-single-node-with-dates", True),        # Multiple histosol measurements, with dates, single node # noqa: E501
    ("multiple-org-values-multiple-nodes-with-dates", True),     # Multiple histosol measurements, with dates, two nodes
    ("multiple-org-values-multiple-nodes-without-dates", True),  # Multiple histosol measurements, no dates
    ("multiple-org-values-multiple-nodes-mixed-dates", True),    # Multiple histosol measurements, inconsistent dates
    ("single-min-equal-100", True),                              # No histosol measurement, mineral measurements equal 100% # noqa: E501
    ("single-min-less-than-100", True),                          # No histosol measurement, other soilType measurements do not equal 100% # noqa: E501
    ("no-measurements", True),                                   # No histosol measurement, no other soilType measurements -> return default # noqa: E501
    ("multiple-org-values-multiple-depths", True),               # Multiple histosol measurements, with different depths
    ("org-and-min-less-than-100", True),                         # Total soil types do not equal 100%
    ("non-standard-depths", True),                               # Non-standard depths
    ("min-with-dates-less-than-100-org-without-dates", True),    # Mineral soils with dates, histosols without
    ("min-with-dates-equal-100-org-without-dates", True),        # Mineral soils with dates (equal 100%), histosols without # noqa: E501
    ("0-30-without-dates-0-50-with-dates", True),                # No dates for 0-30, dates for 0-50
    ("no-dates-no-depth", True),                                 # No dates, no depths
    ("mixed-depths-choose-standard", True),                      # Mix of standard, non-standard and missing depths -> choose standard depths # noqa: E501
    ("mixed-depths-choose-non-standard", True),                  # Mix of non-standard and missing depths -> choose non-standard depths # noqa: E501
]
IDS_SHOULD_RUN = [p[0] for p in PARAMS_SHOULD_RUN]


@mark.parametrize("subfolder, expected", PARAMS_SHOULD_RUN, ids=IDS_SHOULD_RUN)
def test_should_run(
    subfolder: str,
    expected: bool
):
    site = _load_fixture(f"{subfolder}/site", {})

    result, *_ = _should_run(site)
    assert result == expected


PARAMS_RUN = [subfolder for subfolder, should_run in PARAMS_SHOULD_RUN if should_run]


@mark.parametrize("subfolder", PARAMS_RUN)
@patch(f"{class_path}._new_measurement", side_effect=fake_new_measurement)
def test_run(
    _mock_new_measurement: MagicMock,
    subfolder: str
):
    site = _load_fixture(f"{subfolder}/site", {})
    expected = _load_fixture(f"{subfolder}/result", {})

    result = run(site)
    assert result == expected
