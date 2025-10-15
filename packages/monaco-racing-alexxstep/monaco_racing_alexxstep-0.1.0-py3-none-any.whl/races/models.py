from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

__all__ = ["RaceRecord"]


@dataclass
class RaceRecord:
    """
    Запис даних одного гонщика.

    Attributes:
      abbreviation: Абревіатура гонщика (3 літери)
      driver: Повне ім'я гонщика
      team: Назва команди
      start: Час старту (datetime)
      stop: Час фінішу (datetime)
      errors: Список помилок валідації
    """

    abbreviation: str = ""
    driver: str = ""
    team: str = ""
    start: Optional[datetime] = None
    stop: Optional[datetime] = None
    errors: list[str] = field(default_factory=list)

    @property
    def duration(self) -> Optional[timedelta]:
        """
        Обчислює тривалість кола.

        Валідація:
        - Перевірка наявності start та stop
        - Перевірка що start < stop
        - Додавання помилок в self.errors якщо щось не так

        Returns:
          timedelta або None якщо є помилки
        """
        if self.start is None:
            error_msg = "Start time is missing"
            if error_msg not in self.errors:
                self.errors.append(error_msg)
            return None
        if self.stop is None:
            error_msg = "Stop time is missing"
            if error_msg not in self.errors:
                self.errors.append(error_msg)
            return None
        if self.start >= self.stop:
            error_msg = (
                f"Start time {self.start} "
                f"is greater than or equal "
                f"to stop time {self.stop}"
            )
            if error_msg not in self.errors:
                self.errors.append(error_msg)
            return None
        return self.stop - self.start

    @property
    def is_valid(self) -> bool:
        """Чи запис валідний (без помилок)"""
        return len(self.errors) == 0

    def format_duration(self) -> str:
        """
        Форматує тривалість кола.
        """
        if not self.duration:
            return "N/A"

        total_seconds = self.duration.total_seconds()
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60

        return f"{minutes}:{seconds:06.3f}"

    def __str__(self) -> str:
        """
        Форматує вивід запису.

        Формат для валідних записів:
        "Daniel Ricciardo | RED BULL RACING TAG HEUER | 1:12.013"

        Формат для невалідних:
        "Daniel Ricciardo | ERRORS: [список помилок]"

        Returns:
        Відформатований рядок
        """
        if not self.is_valid:
            errors_str = ", ".join(self.errors)
            return f"{self.driver} | ERRORS: {errors_str}"

        return f"{self.driver} | {self.team} | {self.format_duration()}"
