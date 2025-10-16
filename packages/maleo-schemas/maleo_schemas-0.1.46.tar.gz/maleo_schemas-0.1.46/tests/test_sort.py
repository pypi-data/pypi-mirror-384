import pytest
from pydantic import ValidationError
from maleo.enums.order import Order as OrderEnum
from src.mixins.sort import (
    SortColumn,
    Sorts,
    SortColumns,
    convert,
    is_sort_columns,
    is_sorts,
)

# ---------- SortColumn ----------


def test_sortcolumn_valid_from_string_asc():
    sc = SortColumn.from_string("created_at.asc")
    assert sc.name == "created_at"
    assert sc.order == OrderEnum.ASC
    assert sc.to_string() == "created_at.asc"


def test_sortcolumn_valid_from_string_desc():
    sc = SortColumn.from_string("updated_at.desc")
    assert sc.name == "updated_at"
    assert sc.order == OrderEnum.DESC
    assert sc.to_string() == "updated_at.desc"


def test_sortcolumn_invalid_format_raises():
    with pytest.raises(ValueError):
        SortColumn.from_string("invalid-format")


def test_sortcolumn_invalid_missing_order_raises():
    with pytest.raises(ValueError):
        SortColumn.from_string("created_at")


def test_sortcolumn_to_string_round_trip():
    original = SortColumn.from_string("name.asc")
    s = original.to_string()
    recreated = SortColumn.from_string(s)
    assert original == recreated


# ---------- is_sort_columns / is_sorts ----------


def test_is_sort_columns_and_is_sorts():
    sc = SortColumn.from_string("id.asc")
    assert is_sort_columns([sc])
    assert not is_sort_columns(["id.asc"])
    assert is_sorts(["id.asc"])
    assert not is_sorts([sc])


# ---------- convert() ----------


def test_convert_from_sortcolumns_to_strings():
    sc = SortColumn.from_string("created_at.asc")
    result = convert([sc])
    assert isinstance(result[0], str)
    assert result[0] == "created_at.asc"


def test_convert_from_strings_to_sortcolumns():
    sorts = ["updated_at.desc"]
    result = convert(sorts)
    assert isinstance(result[0], SortColumn)
    assert result[0].name == "updated_at"
    assert result[0].order == OrderEnum.DESC


def test_convert_invalid_type_raises():
    with pytest.raises(ValueError):
        convert([123])  # type: ignore


# ---------- Sorts class ----------


def test_sorts_from_sort_columns_and_back():
    sc = SortColumn.from_string("created_at.asc")
    sorts = Sorts.from_sort_columns([sc])
    assert isinstance(sorts.sorts[0], str)
    parsed = sorts.sort_columns[0]
    assert parsed.name == "created_at"


def test_sorts_invalid_string_format_raises():
    with pytest.raises(ValidationError):
        Sorts(sorts=["invalid-format"])


def test_sorts_default_value_is_valid():
    s = Sorts()
    assert s.sorts == ["id.asc"]
    assert s.sort_columns[0].name == "id"


# ---------- SortColumns class ----------


def test_sortcolumns_from_sorts_and_back():
    sorts = ["created_at.asc", "updated_at.desc"]
    sc_obj = SortColumns.from_sorts(sorts)
    assert isinstance(sc_obj.sort_columns[0], SortColumn)
    round_trip = sc_obj.sorts
    assert round_trip == sorts


def test_sortcolumns_default_value_is_valid():
    sc_obj = SortColumns()
    assert sc_obj.sort_columns[0].name == "id"
    assert sc_obj.sort_columns[0].order == OrderEnum.ASC
