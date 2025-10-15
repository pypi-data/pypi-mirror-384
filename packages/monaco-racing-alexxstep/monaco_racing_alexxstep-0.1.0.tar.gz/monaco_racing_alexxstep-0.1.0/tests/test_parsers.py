from datetime import datetime
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.races.models import RaceRecord
from src.races.parsers import RaceDataParser

# ================================
# TESTS 1:
# ================================


def test_read_abbreviations_folder_not_found():
    """Тест коли папка не знайдена"""
    folder = Path("nonexistent_folder")
    filename = "abbreviations.txt"

    with patch.object(Path, "exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            RaceDataParser._read_abbreviations(folder, filename)


def test_read_abbreviations_file_not_found():
    """Тест коли файл не знайдений"""
    folder = Path(__file__).parent / "data"
    filename = "nonexistent_file.txt"

    # Моки для Path.exists та Path.is_dir
    with (
        patch.object(Path, "exists", side_effect=[True, False]),
        patch.object(Path, "is_dir", return_value=True),
    ):
        with pytest.raises(FileNotFoundError):
            RaceDataParser._read_abbreviations(folder, filename)


# Валідні дані для abbreviations.txt
valid_abbreviations_data = """DRR_Daniel Ricciardo_RED BULL RACING TAG HEUER
SVF_Sebastian Vettel_FERRARI
LHM_Lewis Hamilton_MERCEDES
"""


def test_read_abbreviations_valid_data():
    """Тест коли дані валідні"""

    folder = Path(__file__).parent / "data"
    filename = "abbreviations.txt"

    with (
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "is_dir", return_value=True),
        patch("builtins.open", mock_open(read_data=valid_abbreviations_data)),
    ):
        records = RaceDataParser._read_abbreviations(folder, filename)

        assert len(records) == 3
        assert "DRR" in records
        assert "SVF" in records
        assert "LHM" in records
        assert records["DRR"].driver == "Daniel Ricciardo"
        assert records["DRR"].team == "RED BULL RACING TAG HEUER"
        assert records["SVF"].driver == "Sebastian Vettel"
        assert records["SVF"].team == "FERRARI"
        assert records["LHM"].driver == "Lewis Hamilton"
        assert records["LHM"].team == "MERCEDES"


# Валідні дані для start.log
valid_start_log_data = """DRR2018-05-24_12:14:12.054000
SVF2018-05-24_12:02:58.917000
LHM2018-05-24_12:18:20.125000
"""


def test_read_start_log_valid_data():
    folder = Path(__file__).parent / "data"
    filename = "start.log"

    # Спочатку створюємо словник з записами (як після abbreviations)
    records_dict = {
        "DRR": RaceRecord(
            abbreviation="DRR", driver="Daniel Ricciardo", team="RED BULL"
        ),
        "SVF": RaceRecord(
            abbreviation="SVF", driver="Sebastian Vettel", team="FERRARI"
        ),
        "LHM": RaceRecord(abbreviation="LHM", driver="Lewis Hamilton", team="MERCEDES"),
    }

    #
    with (
        patch.object(Path, "exists", return_value=True),
        patch("builtins.open", mock_open(read_data=valid_start_log_data)),
    ):
        result = RaceDataParser._read_start_stop_log(
            records_dict, folder, filename, is_start=True
        )

        assert result["DRR"].start == datetime(2018, 5, 24, 12, 14, 12, 54000)
        assert result["SVF"].start == datetime(2018, 5, 24, 12, 2, 58, 917000)
        assert result["LHM"].start == datetime(2018, 5, 24, 12, 18, 20, 125000)


# Валідні дані для end.log
valid_end_log_data = """DRR2018-05-24_12:15:24.067000
SVF2018-05-24_12:04:03.332000
LHM2018-05-24_12:19:32.538000
"""


def test_read_end_log_valid_data():
    """Тест коли дані валідні"""

    folder = Path(__file__).parent / "data"
    filename = "end.log"

    # Спочатку створюємо словник з записами (як після abbreviations)
    records_dict = {
        "DRR": RaceRecord(
            abbreviation="DRR", driver="Daniel Ricciardo", team="RED BULL"
        ),
        "SVF": RaceRecord(
            abbreviation="SVF", driver="Sebastian Vettel", team="FERRARI"
        ),
        "LHM": RaceRecord(abbreviation="LHM", driver="Lewis Hamilton", team="MERCEDES"),
    }

    # Mock файлу
    with (
        patch.object(Path, "exists", return_value=True),
        patch("builtins.open", mock_open(read_data=valid_end_log_data)),
    ):
        result = RaceDataParser._read_start_stop_log(
            records_dict, folder, filename, is_start=False
        )

        assert result["DRR"].stop == datetime(2018, 5, 24, 12, 15, 24, 67000)
        assert result["SVF"].stop == datetime(2018, 5, 24, 12, 4, 3, 332000)
        assert result["LHM"].stop == datetime(2018, 5, 24, 12, 19, 32, 538000)


def test_read_log_abbreviation_not_in_dict():
    """Тест коли abbreviation відсутня в словнику."""

    folder = Path(__file__).parent / "data"
    filename = "start.log"

    records_dict = {}

    log_data = "XXX2018-05-24_12:14:12.054000"

    with (
        patch.object(Path, "exists", return_value=True),
        patch("builtins.open", mock_open(read_data=log_data)),
    ):
        result = RaceDataParser._read_start_stop_log(
            records_dict, folder, filename, is_start=True
        )

        assert "XXX" in result
        assert len(result["XXX"].errors) > 0
        assert "not found" in result["XXX"].errors[0].lower()


def test_read_log_invalid_datetime():
    """Тест з невалідним datetime форматом."""
    folder = Path("data")
    filename = "start.log"

    # Створюємо запис
    records_dict = {
        "DRR": RaceRecord(abbreviation="DRR", driver="Daniel Ricciardo"),
    }

    # Log з невалідним datetime (місяць 13, година 25)
    log_data = "DRR2018-13-99_25:99:99.999000\n"

    with (
        patch.object(Path, "exists", return_value=True),
        patch("builtins.open", mock_open(read_data=log_data)),
    ):
        result = RaceDataParser._read_start_stop_log(
            records_dict, folder, filename, is_start=True
        )

        assert "DRR" in result
        assert len(result["DRR"].errors) > 0
        assert "invalid datetime format" in result["DRR"].errors[0].lower()


def test_parse_files_integration():
    """Інтеграційний тест parse_files з усіма файлами."""
    folder = Path("data")

    # Mock для всіх трьох файлів
    def mock_open_side_effect(file_path, *args, **kwargs):
        file_path_str = str(file_path)

        if "abbreviations.txt" in file_path_str:
            return mock_open(read_data=valid_abbreviations_data)()
        elif "start.log" in file_path_str:
            return mock_open(read_data=valid_start_log_data)()
        elif "end.log" in file_path_str:
            return mock_open(read_data=valid_end_log_data)()

        raise FileNotFoundError(f"File not found: {file_path}")

    with (
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "is_dir", return_value=True),
        patch("builtins.open", side_effect=mock_open_side_effect),
    ):
        records = RaceDataParser.parse_files(folder)

        # Перевірки
        assert len(records) == 3
        assert all(r.start is not None for r in records.values())
        assert all(r.stop is not None for r in records.values())

        # Перевірка конкретного запису
        drr = records["DRR"]
        assert drr.driver == "Daniel Ricciardo"
        assert drr.start is not None
        assert drr.stop is not None
        assert drr.duration is not None
