import re
from datetime import datetime
from pathlib import Path
from typing import Dict

from .models import RaceRecord

__all__ = ["RaceDataParser"]


class RaceDataParser:
    """Парсер файлів з даними гонок"""

    # формат дати
    DATE_FORMAT = "%Y-%m-%d_%H:%M:%S.%f"

    # формат абревіатури
    ABBR_PATTERN = re.compile(r"^([A-Z]{3})_([^_]+)_(.+)$")

    # формат логування
    LOG_PATTERN = re.compile(
        r"^([A-Z]{3})"  # abbreviation: рівно 3 великі літери
        r"(\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2}\.\d{3,6})$"  # datetime
    )

    @classmethod
    def parse_files(
        cls,
        folder: Path,
        abbr_file: str = "abbreviations.txt",
        start_file: str = "start.log",
        end_file: str = "end.log",
    ) -> Dict[str, RaceRecord]:
        """
        Головний метод парсингу всіх файлів.

        Порядок:
        1. _read_abbreviations() - створює records_dict
        2. _read_start_log() - доповнює start
        3. _read_end_log() - доповнює stop

        Returns:
            Dict[abbreviation, RaceRecord]
        """

        # Створюємо records_dict
        records_dict = cls._read_abbreviations(folder, abbr_file)

        # Доповнюємо start
        records_dict = cls._read_start_stop_log(
            records_dict, folder, start_file, is_start=True
        )

        # Доповнюємо stop
        records_dict = cls._read_start_stop_log(
            records_dict, folder, end_file, is_start=False
        )

        return records_dict

    @classmethod
    def _read_abbreviations(cls, folder: Path, filename: str) -> Dict[str, RaceRecord]:
        """
        Читає abbreviations.txt

        Кроки:
        1. Перевірити наявність папки
        2. Перевірити наявність файлу
        3. Прочитати файл
        4. Валідувати формат кожного рядка
        5. Створити RaceRecord для кожного рядка
        6. Зберегти в словник {abbreviation: RaceRecord}

        Формат рядка: "DRR_Daniel Ricciardo_RED BULL RACING TAG HEUER"

        Валідація:
        - 3 літери abbreviation
        - Наявність підкреслень
        - Непусті поля

        Помилки:
        - Якщо формат невірний → додати в record.errors і продовжити
        """
        records_dict: Dict[str, RaceRecord] = {}
        file_path = folder / filename

        # Перевірка наявності папки
        if not folder.exists():
            raise FileNotFoundError(f"Folder {folder} does not exist")
        if not folder.is_dir():
            raise NotADirectoryError(f"Folder {folder} is not a directory")
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")

        # Прочитати файл
        with open(file_path, "r", encoding="utf-8") as file:
            for line_num, line in enumerate(file, start=1):
                line = line.strip()
                if not line:
                    continue

                match = cls.ABBR_PATTERN.match(line)
                if not match:
                    # Помилка в парсингу абревіатури
                    records_dict[line] = RaceRecord(abbreviation=line)
                    records_dict[line].errors.append(
                        f"{filename}, line {line_num}: Invalid format"
                    )
                    continue

                # Розділити абревіатуру на частини
                abbr, driver, team = match.groups()

                record = RaceRecord(abbreviation=abbr, driver=driver, team=team)
                records_dict[abbr] = record

        return records_dict

        # Валідація формату

    @classmethod
    def _read_start_stop_log(
        cls,
        records_dict: Dict[str, RaceRecord],
        folder: Path,
        filename: str,
        is_start: bool = True,
    ) -> Dict[str, RaceRecord]:
        """
        Читає start.log або end.log (один метод для обох).

        Кроки:
        1. Перевірити наявність файлу
        2. Прочитати файл
        3. Валідувати формат рядка
        4. Парсити datetime
        5. Знайти запис в records_dict за abbreviation
        6. Додати start або stop в залежності від is_start

        Формат: "DRR2018-05-24_12:14:12.054"

        Валідація:
        - 3 літери abbreviation
        - Правильний формат datetime

        Можливі помилки:
        - Abbreviation відсутня в records_dict → створити новий запис + додати помилку
        - Неправильний формат datetime → додати в errors

        Returns:
            Оновлений records_dict
        """
        file_path = folder / filename

        # Перевірка наявності файлу
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")

        # Прочитати файл
        with open(file_path, "r", encoding="utf-8") as file:
            for line_num, line in enumerate(file, start=1):
                line = line.strip()

                # пропустити порожні рядки
                if not line:
                    continue

                match = cls.LOG_PATTERN.match(line)
                if not match:
                    # Помилка в парсингу дати
                    records_dict[line] = RaceRecord(abbreviation=line)
                    records_dict[line].errors.append(
                        f"{filename}, line {line_num}: Invalid format"
                    )
                    continue

                # Витягуємо abbreviation та datetime
                abbr, datetime_str = match.groups()

                if abbr not in records_dict:
                    # Абревіатура відсутня в records_dict
                    records_dict[abbr] = RaceRecord(abbreviation=abbr)
                    records_dict[abbr].errors.append(
                        f"{filename}, line {line_num}: Abbreviation {abbr} not found"
                    )
                    continue

                # Парсимо datetime
                try:
                    dt = datetime.strptime(datetime_str, cls.DATE_FORMAT)
                except ValueError as e:
                    # Помилка в парсингу datetime
                    records_dict[abbr].errors.append(
                        f"{filename}, line {line_num}: "
                        f"Invalid datetime format, error: {e}"
                    )
                    continue

                # Додаємо start або stop
                if is_start:
                    records_dict[abbr].start = dt
                else:
                    records_dict[abbr].stop = dt

        return records_dict
