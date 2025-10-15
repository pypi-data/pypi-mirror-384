from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from src.races.models import RaceRecord
from src.races.report import RaceReport

# ================================================
# Test RaceReport.build_report
# ================================================


def create_test_records():
    # Створюємо тестові записи з валідними та невалідними датами

    return {
        "SVF": RaceRecord(
            abbreviation="SVF",
            driver="Sebastian Vettel",
            team="FERRARI",
            start=datetime(2018, 5, 24, 12, 2, 58, 917000),
            stop=datetime(2018, 5, 24, 12, 4, 3, 332000),
        ),
        "LHM": RaceRecord(
            abbreviation="LHM",
            driver="Lewis Hamilton",
            team="MERCEDES",
            start=datetime(2018, 5, 24, 12, 18, 20, 125000),
            stop=datetime(2018, 5, 24, 12, 19, 32, 585000),
        ),
        "DRR": RaceRecord(
            abbreviation="DRR",
            driver="Daniel Ricciardo",
            team="RED BULL RACING TAG HEUER",
            start=datetime(2018, 5, 24, 12, 14, 12, 54000),
            # start > stop - невалідно
            stop=datetime(2018, 5, 24, 12, 11, 24, 67000),
        ),
    }


# ================================================
# STEP 2: Тест build_report з моками
# ================================================


def test_build_report_with_mock():
    """Тест build_report з моками"""

    folder = Path("data")

    test_records = create_test_records()

    with patch(
        "src.races.report.RaceDataParser.parse_files", return_value=test_records
    ):
        good_records, bad_records = RaceReport.build_report(folder)

        assert len(good_records) == 2
        assert len(bad_records) == 1

        assert good_records[0].driver == "Sebastian Vettel"
        assert good_records[1].driver == "Lewis Hamilton"


def test_build_report_with_driver_filter():
    """Тест build_report з фільтрацією за driver"""

    folder = Path("data")

    test_records = create_test_records()

    with patch(
        "src.races.report.RaceDataParser.parse_files", return_value=test_records
    ):
        good_records, bad_records = RaceReport.build_report(
            folder, driver="Sebastian Vettel"
        )

        assert len(good_records) == 1
        assert good_records[0].driver == "Sebastian Vettel"


def test_build_report_descending_order():
    """Тест build_report з descending сортуванням."""
    folder = Path("data")

    test_records = create_test_records()

    with patch(
        "src.races.report.RaceDataParser.parse_files", return_value=test_records
    ):
        good_records, bad_records = RaceReport.build_report(folder, asc=False)

        # Перевірки: найповільніший перший
        assert len(good_records) == 2
        assert good_records[0].driver == "Lewis Hamilton"  # Повільніший
        assert good_records[1].driver == "Sebastian Vettel"  # Швидший


def test_print_report_basic():
    """Тест базового форматування print_report."""
    # Створюємо прості записи
    good_records = [
        RaceRecord(
            abbreviation="SVF",
            driver="Sebastian Vettel",
            team="FERRARI",
            start=datetime(2018, 5, 24, 12, 2, 58, 917000),
            stop=datetime(2018, 5, 24, 12, 4, 3, 332000),
        ),
        RaceRecord(
            abbreviation="LHM",
            driver="Lewis Hamilton",
            team="MERCEDES",
            start=datetime(2018, 5, 24, 12, 18, 20, 125000),
            stop=datetime(2018, 5, 24, 12, 19, 32, 538000),
        ),
    ]

    result = RaceReport.print_report(good_records)

    # Перевірки
    assert "Sebastian Vettel" in result
    assert "Lewis Hamilton" in result
    assert "FERRARI" in result
    assert "MERCEDES" in result
    assert "1:04.415" in result  # Duration для SVF
    assert "1:12.413" in result  # Duration для LHM


def test_print_report_with_underline():
    """Тест print_report з підкресленням після 15-го місця."""
    # Створюємо 17 записів
    good_records = []
    for i in range(1, 18):  # 1 до 17
        record = RaceRecord(
            abbreviation=f"T{i:02d}",
            driver=f"Driver {i}",
            team=f"Team {i}",
            start=datetime(2018, 5, 24, 12, 0, 0),
            stop=datetime(2018, 5, 24, 12, 1, 12, i * 1000),
        )
        good_records.append(record)

    result = RaceReport.print_report(good_records, underline=15)

    # Перевірки
    assert "Driver 1" in result
    assert "Driver 15" in result
    assert "Driver 16" in result
    assert "Driver 17" in result

    # Перевіряємо що є підкреслення
    assert "-" * 70 in result or "-" * 71 in result
