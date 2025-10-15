from datetime import datetime, timedelta

import pytest

from src.races.models import RaceRecord

# ================================
# TESTS
# ================================


# Тести для створення записів
def test_create_empty_record():
    record = RaceRecord()
    assert record.abbreviation == ""
    assert record.driver == ""
    assert record.team == ""
    assert record.start is None
    assert record.stop is None
    assert record.errors == []


def test_create_record_with_data():
    record = RaceRecord(
        abbreviation="DRR",
        driver="Daniel Ricciardo",
        team="RED BULL RACING TAG HEUER",
    )
    assert record.abbreviation == "DRR"
    assert record.driver == "Daniel Ricciardo"
    assert record.team == "RED BULL RACING TAG HEUER"


# Тести для валідації duration
valid_duration_cases = [
    # (start, stop, expected_seconds)
    (
        datetime(2018, 5, 24, 12, 2, 58, 917000),
        datetime(2018, 5, 24, 12, 4, 3, 332000),
        64.415,
    ),
    (
        datetime(2018, 5, 24, 12, 14, 12, 54000),
        datetime(2018, 5, 24, 12, 15, 24, 67000),
        72.013,
    ),
    (
        datetime(2018, 5, 24, 12, 0, 0, 0),
        datetime(2018, 5, 24, 12, 1, 12, 434000),
        72.434,
    ),
]


@pytest.mark.parametrize("start, stop, expected_seconds", valid_duration_cases)
def test_valid_duration(start, stop, expected_seconds):
    record = RaceRecord(
        abbreviation="TST",
        driver="Test Surname",
        team="TestTeam",
        start=start,
        stop=stop,
    )
    duration = record.duration

    assert duration is not None
    assert isinstance(duration, timedelta)
    assert duration.total_seconds() == pytest.approx(expected_seconds, rel=0.001)


# Тести для невалідних duration (відсутні дані)
invalid_duration_missing_cases = [
    # (start, stop, error_keyword)
    (None, datetime(2018, 5, 24, 12, 4, 3), "start"),
    (datetime(2018, 5, 24, 12, 2, 58), None, "stop"),
]


@pytest.mark.parametrize("start,stop,error_keyword", invalid_duration_missing_cases)
def test_duration_missing_data(start, stop, error_keyword):
    """Тест duration з відсутніми start/stop."""
    record = RaceRecord(abbreviation="TEST", start=start, stop=stop)

    duration = record.duration

    assert duration is None
    assert any(error_keyword.lower() in error.lower() for error in record.errors)


# Тести для невалідних duration (start >= stop)
def test_duration_start_after_stop():
    """Тест duration коли start >= stop."""
    record = RaceRecord(
        abbreviation="KRF",
        start=datetime(2018, 5, 24, 12, 15, 0),
        stop=datetime(2018, 5, 24, 12, 14, 0),
    )

    duration = record.duration

    assert duration is None
    assert any("start" in error.lower() for error in record.errors)


# Тести для is_valid (позитивні)
def test_is_valid_true():
    """Тест is_valid для валідного запису."""
    record = RaceRecord(
        abbreviation="FAM",
        start=datetime(2018, 5, 24, 12, 2, 58),
        stop=datetime(2018, 5, 24, 12, 4, 3),
    )

    _ = record.duration  # Викликаємо для перевірок

    assert record.is_valid is True


# Тести для is_valid (негативні)
def test_is_valid_false():
    """Тест is_valid для невалідного запису."""
    record = RaceRecord()
    record.errors.append("Test error")

    assert record.is_valid is False


# Тести для форматування duration
format_duration_cases = [
    # (start, stop, expected_format)
    (
        datetime(2018, 5, 24, 12, 0, 0),
        datetime(2018, 5, 24, 12, 1, 12, 13000),
        "1:12.013",
    ),
    (
        datetime(2018, 5, 24, 12, 0, 0),
        datetime(2018, 5, 24, 12, 1, 4, 415000),
        "1:04.415",
    ),
    (
        datetime(2018, 5, 24, 12, 0, 0),
        datetime(2018, 5, 24, 12, 0, 59, 999000),
        "0:59.999",
    ),
]


@pytest.mark.parametrize("start,stop,expected_format", format_duration_cases)
def test_format_duration(start, stop, expected_format):
    """Тест форматування duration."""
    record = RaceRecord(
        abbreviation="TST",
        start=start,
        stop=stop,
    )

    formatted_duration = record.format_duration()
    assert formatted_duration == expected_format


# Тест для форматування порожнього duration
def test_format_duration_none():
    """Тест форматування коли duration = None."""
    record = RaceRecord()

    formatted = record.format_duration()

    assert formatted == "N/A"


# Тести для __str__
def test_str_valid_record():
    """Тест __str__ для валідного запису."""
    record = RaceRecord(
        abbreviation="DRR",
        driver="Daniel Ricciardo",
        team="RED BULL RACING",
        start=datetime(2018, 5, 24, 12, 14, 12, 54000),
        stop=datetime(2018, 5, 24, 12, 15, 24, 67000),
    )

    result = str(record)

    assert "Daniel Ricciardo" in result
    assert "RED BULL RACING" in result
    assert "1:12.013" in result


# Тест кейси для __str__


def test_str_invalid_record():
    """Тест __str__ для невалідного запису."""
    record = RaceRecord(driver="Test Driver")
    record.errors.append("Test error")

    result = str(record)

    assert "Test Driver" in result
    assert "ERRORS" in result
    assert "Test error" in result
