from pathlib import Path
from typing import List, Optional, Tuple

from .models import RaceRecord
from .parsers import RaceDataParser

__all__ = ["RaceReport"]


class RaceReport:
    """Клас для побудови та форматування звіту"""

    @staticmethod
    def build_report(
        folder: Path,
        abbr_file: str = "abbreviations.txt",
        start_file: str = "start.log",
        end_file: str = "end.log",
        driver: Optional[str] = None,
        asc: bool = True,
    ) -> Tuple[List[RaceRecord], List[RaceRecord]]:
        """
        Будує звіт з даних гонок.

        Кроки:
        1. Парсинг файлів через RaceDataParser
        2. Валідація duration для кожного запису
        3. Розділення на good_records та bad_records
        4. Фільтрація за driver (якщо вказано)
        5. Сортування good_records за duration (asc/desc)

        Args:
            folder: Шлях до папки з даними
            abbr_file: Назва файлу з абревіатурами
            start_file: Назва файлу зі стартами
            end_file: Назва файлу з фінішами
            driver: Ім'я гонщика для фільтрації (опціонально)
            asc: True для сортування за зростанням

        Returns:
            (good_records, bad_records)
        """
        # Парсинг файлів
        records_dict = RaceDataParser.parse_files(
            folder, abbr_file, start_file, end_file
        )

        # Конвертувати словник у список
        all_records = list(records_dict.values())

        # Викликати duration для всіх записів (для валідації)
        for record in all_records:
            _ = record.duration

        # Розділити на валідні та невалідні
        good_records = [r for r in all_records if r.is_valid and r.duration]
        bad_records = [r for r in all_records if not r.is_valid or not r.duration]

        # Фільтрація за driver (якщо вказано)
        if driver:
            good_records = [r for r in good_records if r.driver == driver]

        # Сортування good_records за duration
        good_records.sort(key=lambda r: r.duration, reverse=not asc)

        # Повернути кортеж
        return good_records, bad_records

    @staticmethod
    def print_report(
        good_records: List[RaceRecord],
        bad_records: List[RaceRecord] = None,
        underline: int = 15,
    ) -> str:
        """
        Форматує звіт в рядок.

        Формат:
        1. Daniel Ricciardo | RED BULL RACING TAG HEUER | 1:12.013
        2. Sebastian Vettel | FERRARI | 1:12.415
        ...

        Якщо є bad_records - вивести в кінці з описом помилок.

        Args:
            good_records: Валідні записи (відсортовані)
            bad_records: Записи з помилками (опціонально)
            underline: Після якого місця підкреслення

        Returns:
            Відформатований рядок звіту
        """

        lines = []

        # Додати good_records з нумерацією
        for position, record in enumerate(good_records, start=1):
            # Форматування рядка
            line = (
                f"{position:2}. {record.driver:25}"
                f" | {record.team:32}"
                f" | {record.format_duration()}"
            )
            lines.append(line)

            # Додати підкреслення після underline позиції
            # Показуємо лінію тільки якщо є гонщики після цієї позиції
            if position == underline and position < len(good_records):
                lines.append("-" * 75)

        # Додати bad_records (якщо є)
        if bad_records:
            lines.append("")
            lines.append("=== Records with errors ===")
            for record in bad_records:
                lines.append(str(record))

        # Об'єднати рядки в один текст
        return "\n".join(lines)
