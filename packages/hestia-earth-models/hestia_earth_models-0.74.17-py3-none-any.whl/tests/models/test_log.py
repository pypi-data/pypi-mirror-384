from enum import Enum
from numpy import array
from pytest import mark

from hestia_earth.models.log import (
    format_bool, format_decimal_percentage, format_enum, format_float, format_int, format_nd_array, format_str
)


@mark.parametrize(
    "value, kwargs, expected",
    [
        (True, {}, "True"),
        (False, {}, "False"),
        ([], {}, "None"),
        ("str", {}, "None"),
        (None, {}, "None"),
        (None, {"default": "Override"}, "Override")
    ],
    ids=["True", "False", "list", "str", "None", "None w/ default"]
)
def test_format_bool(value, kwargs, expected):
    assert format_bool(value, **kwargs) == expected


@mark.parametrize(
    "value, kwargs, expected",
    [
        (3.141592653, {}, "314.159 pct"),
        (0, {}, "0 pct"),
        ("20", {}, "None"),
        (None, {}, "None"),
        (3.141592653, {"unit": "kg"}, "314.159 kg"),
        (3.141592653, {"ndigits": 4}, "314.1593 pct"),
        (None, {"default": "Override"}, "Override"),
    ],
    ids=["float", "zero", "str", "None", "float w/ unit", "float w/ ndigits", "None w/ default"]
)
def test_format_decimal_percentage(value, kwargs, expected):
    assert format_decimal_percentage(value, **kwargs) == expected


class TestEnum(Enum):
    WITH_LEGAL_CHARS = "with legal chars"
    WITH_RESERVED_CHARS = "with_reserved_chars"


@mark.parametrize(
    "value, kwargs, expected",
    [
        (TestEnum.WITH_LEGAL_CHARS, {}, TestEnum.WITH_LEGAL_CHARS.value),
        (TestEnum.WITH_RESERVED_CHARS, {}, "with-reserved-chars"),
        ("str", {}, "None"),
        (None, {}, "None"),
        (None, {"default": "Override"}, "Override")
    ],
    ids=["Enum w/ legal chars", "Enum w/ illegal chars", "str", "None", "None w/ default"]
)
def test_format_enum(value, kwargs, expected):
    assert format_enum(value, **kwargs) == expected


@mark.parametrize(
    "value, kwargs, expected",
    [
        (3.141592653, {}, "3.142"),
        (0, {}, "0"),
        ("20", {}, "None"),
        (None, {}, "None"),
        (3.141592653, {"unit": "kg"}, "3.142 kg"),
        (3.141592653, {"ndigits": 4}, "3.1416"),
        (None, {"default": "Override"}, "Override"),
    ],
    ids=["float", "zero", "str", "None", "float w/ unit", "float w/ ndigits", "None w/ default"]
)
def test_format_float(value, kwargs, expected):
    assert format_float(value, **kwargs) == expected


@mark.parametrize(
    "value, kwargs, expected",
    [
        (3.141592653, {}, "3"),
        (0, {}, "0"),
        ("20", {}, "None"),
        (None, {}, "None"),
        (3.141592653, {"unit": "kg"}, "3 kg"),
        (None, {"default": "Override"}, "Override")
    ],
    ids=["float", "zero", "str", "None", "float w/ unit", "None w/ default"]
)
def test_format_int(value, kwargs, expected):
    assert format_int(value, **kwargs) == expected


@mark.parametrize(
    "value, kwargs, expected",
    [
        (array(3.141592653), {}, "3.142 ± 0.0"),
        (array([1, 2, 3, 4]), {}, "2.5 ± 1.118"),
        (array([[11, 12, 13, 14], [21, 22, 23, 24]]), {}, "17.5 ± 5.123"),
        (3.141592653, {}, "3.142"),
        (0, {}, "0"),
        ("20", {}, "None"),
        (None, {}, "None"),
        (array(3.141592653), {"unit": "kg"}, "3.142 ± 0.0 kg"),
        (array(3.141592653), {"ndigits": 4}, "3.1416 ± 0.0"),
        (None, {"default": "Override"}, "Override"),
    ],
    ids=["scalar", "1d", "2d", "float", "zero", "str", "None", "float w/ unit", "float w/ ndigits", "None w/ default"]
)
def test_format_nd_array(value, kwargs, expected):
    assert format_nd_array(value, **kwargs) == expected


@mark.parametrize(
    "value, kwargs, expected",
    [
        ("string", {}, "string"),
        ("some_reserved:chars,get=replaced", {}, "some-reserved-chars-get-replaced"),
        ([], {}, "None"),
        (None, {}, "None"),
        (None, {"default": "Override"}, "Override")
    ],
    ids=["legal chars", "illegal chars", "list", "None", "None w/ default"]
)
def test_format_str(value, kwargs, expected):
    assert format_str(value, **kwargs) == expected
