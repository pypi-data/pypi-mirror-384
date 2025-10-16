from pytest import mark

from hestia_earth.models.ipcc2019.organicCarbonPerHa_utils import format_bool_list, format_float_list


@mark.parametrize(
    "value, expected",
    [
        ([True, True, False], "True True False"),
        ([], "None"),
        (["Yes", "No", ""], "None None None"),
        (None, "None")
    ],
    ids=["list", "empty list", "list[str]", "None"]
)
def test_format_bool_list(value, expected):
    assert format_bool_list(value) == expected


@mark.parametrize(
    "value, expected",
    [
        ([3.14, 31.4, 314], "3.1 31.4 314"),
        ([], "None"),
        (["Yes", "No", ""], "None None None"),
        (None, "None")
    ],
    ids=["list", "empty list", "list[str]", "None"]
)
def test_format_number_list(value, expected):
    assert format_float_list(value) == expected
