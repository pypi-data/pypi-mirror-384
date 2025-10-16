import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from src.mixins.filter import (
    DateFilter,
    Filters,
    DateFilters,
    convert,
    is_date_filters,
    is_filters,
)

# ---------- DateFilter ----------


def test_datefilter_valid_both_datetimes():
    filters = DateFilter(
        name="valid_name",
        from_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        to_date=datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
    )
    assert filters.from_date == datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert filters.to_date == datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)


def test_datefilter_valid_only_from_date():
    filters = DateFilter(
        name="valid_name", from_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    )
    assert filters.from_date == datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert filters.to_date is None


def test_datefilter_valid_only_to_date():
    filters = DateFilter(
        name="valid_name",
        to_date=datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
    )
    assert filters.to_date == datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    assert filters.from_date is None


def test_datefilter_invalid_no_datetimes():
    with pytest.raises(ValidationError) as exc_info:
        DateFilter(name="valid_name")  # ❌ neither datetime provided

    errors = exc_info.value.errors()
    assert any(
        "Either 'from_date' or 'to_date' must have value" in e["msg"] for e in errors
    )


def test_datefilter_invalid_to_date_before_from_date():
    with pytest.raises(ValidationError) as exc_info:
        DateFilter(
            name="valid_name",
            from_date=datetime(2024, 12, 31, 12, 0, 0, tzinfo=timezone.utc),
            to_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        )  # ❌ reversed order

    errors = exc_info.value.errors()
    assert any("can not be more than 'to_date'" in e["msg"] for e in errors)


def test_datefilter_valid_equal_datetimes():
    filters = DateFilter(
        name="valid_name",
        from_date=datetime(2024, 5, 20, 15, 30, 0, tzinfo=timezone.utc),
        to_date=datetime(2024, 5, 20, 15, 30, 0, tzinfo=timezone.utc),
    )
    assert filters.from_date == filters.to_date


# ---------- DateFilter.from_string ----------


def test_valid_datefilter_from_only():
    df = DateFilter.from_string("created_at|from::2025-01-01T00:00:00+00:00")
    assert df.name == "created_at"
    assert df.from_date == datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert df.to_date is None


def test_valid_datefilter_to_only():
    df = DateFilter.from_string("updated_at|to::2025-01-31T23:59:59+00:00")
    assert df.name == "updated_at"
    assert df.from_date is None
    assert df.to_date == datetime(2025, 1, 31, 23, 59, 59, tzinfo=timezone.utc)


def test_valid_datefilter_both_from_and_to():
    df = DateFilter.from_string(
        "created_at|from::2025-01-01T00:00:00+00:00|to::2025-01-31T23:59:59+00:00"
    )
    assert df.name == "created_at"
    assert df.from_date is not None and df.to_date is not None
    assert df.from_date < df.to_date


def test_invalid_datefilter_format_raises():
    with pytest.raises(ValueError):
        DateFilter.from_string("invalid_format_string")


def test_invalid_datefilter_missing_dates_raises():
    with pytest.raises(ValueError):
        DateFilter.from_string("created_at")


# ---------- DateFilter.to_string ----------


def test_to_string_round_trip():
    df = DateFilter.from_string(
        "created_at|from::2025-01-01T00:00:00+00:00|to::2025-01-31T23:59:59+00:00"
    )
    s = df.to_string()
    df2 = DateFilter.from_string(s)
    assert df == df2


# ---------- is_date_filters / is_filters ----------


def test_is_date_filters_and_is_filters():
    df = DateFilter.from_string("created_at|from::2025-01-01T00:00:00+00:00")
    assert is_date_filters([df])
    assert not is_date_filters(["created_at|from::2025-01-01T00:00:00+00:00"])
    assert is_filters(["created_at|from::2025-01-01T00:00:00+00:00"])
    assert not is_filters([df])


# ---------- convert() ----------


def test_convert_from_datefilter_to_strings():
    df = DateFilter.from_string("created_at|from::2025-01-01T00:00:00+00:00")
    result = convert([df])
    assert isinstance(result[0], str)
    assert "created_at" in result[0]


def test_convert_from_strings_to_datefilters():
    filters = ["created_at|from::2025-01-01T00:00:00+00:00"]
    result = convert(filters)
    assert isinstance(result[0], DateFilter)
    assert result[0].name == "created_at"


def test_convert_invalid_type_raises():
    with pytest.raises(ValueError):
        convert([123])  # type: ignore # neither DateFilter nor str


# ---------- Filters class ----------


def test_filters_from_date_filters_and_back():
    df = DateFilter.from_string("created_at|from::2025-01-01T00:00:00+00:00")
    filters = Filters.from_date_filters([df])
    assert isinstance(filters.filters[0], str)
    parsed = filters.date_filters[0]
    assert parsed.name == "created_at"


def test_filters_validation_strips_invalid_strings():
    filters = Filters(
        filters=["valid_field|from::2025-01-01T00:00:00+00:00", "invalid_format"]
    )
    # Accessing .date_filters should raise because "invalid_format" can't be parsed
    with pytest.raises(ValueError):
        _ = filters.date_filters


# ---------- DateFilters class ----------


def test_datefilters_from_filters_and_back():
    filters = ["created_at|from::2025-01-01T00:00:00+00:00"]
    df_obj = DateFilters.from_filters(filters)
    assert isinstance(df_obj.date_filters[0], DateFilter)
    round_trip = df_obj.filters
    assert round_trip == filters
