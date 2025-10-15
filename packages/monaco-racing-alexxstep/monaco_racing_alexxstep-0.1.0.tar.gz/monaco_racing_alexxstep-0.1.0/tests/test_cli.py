import sys
from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from src.races.cli import CLI
from src.races.models import RaceRecord

# ================================================
# Test --help
# ================================================


def test_cli_help():
    """Тест --help"""

    # Імітуємо аргументи командного рядка
    test_args = ["monaco-report", "--help"]

    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as e:
            CLI.run()

        # argparse повертає 0 при --help
        assert e.value.code == 0


def test_cli_missing_files_argument():
    """Тест помилки при відсутності аргументу --files"""

    test_args = ["monaco-report"]

    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as e:
            CLI.run()

        # argparse повертає 2 при відсутності обов'язкового аргументу
        assert e.value.code == 2


def test_cli_folder_not_found():
    """Тест помилки при відсутності папки"""

    test_args = ["monaco-report", "--files", "invalid_folder"]

    with (
        patch.object(sys, "argv", test_args),
        patch.object(Path, "exists", return_value=False),
        patch("sys.stdout", new_callable=StringIO) as mock_stdout,
    ):
        CLI.run()

        output = mock_stdout.getvalue()
        assert "does not exist" in output


def test_cli_successful_run():
    """Тест успішного запуску CLI"""

    test_args = ["monaco-report", "--files", "data/"]

    fake_record = RaceRecord(
        abbreviation="DRR",
        driver="Daniel Ricciardo",
        team="RED BULL RACING TAG HEUER",
        start=datetime(2018, 5, 24, 12, 14, 12, 54000),
        stop=datetime(2018, 5, 24, 12, 15, 24, 67000),
    )

    # моки для всього ланцюжка
    with (
        patch.object(sys, "argv", test_args),
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "is_dir", return_value=True),
        patch(
            "src.races.report.RaceReport.build_report", return_value=([fake_record], [])
        ),
        patch("sys.stdout", new_callable=StringIO) as mock_stdout,
    ):
        CLI.run()

        output = mock_stdout.getvalue()

        # перевірка виводу
        assert "Daniel Ricciardo" in output
        assert "RED BULL RACING TAG HEUER" in output
        assert "1:12.013" in output


def test_cli_with_driver_filter():
    """Тест CLI з фільтрацією за driver"""

    test_args = ["monaco-report", "--files", "data/", "--driver", "Daniel Ricciardo"]

    fake_record = RaceRecord(
        abbreviation="DRR",
        driver="Daniel Ricciardo",
        team="RED BULL RACING TAG HEUER",
        start=datetime(2018, 5, 24, 12, 14, 12, 54000),
        stop=datetime(2018, 5, 24, 12, 15, 24, 67000),
    )

    with (
        patch.object(sys, "argv", test_args),
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "is_dir", return_value=True),
        patch(
            "src.races.report.RaceReport.build_report", return_value=([fake_record], [])
        ),
        patch("sys.stdout", new_callable=StringIO) as mock_stdout,
    ):
        CLI.run()

        output = mock_stdout.getvalue()

        # перевірка виводу
        assert "Daniel Ricciardo" in output
        assert "RED BULL RACING TAG HEUER" in output
        assert "1:12.013" in output
