import argparse
from pathlib import Path

from .report import RaceReport

__all__ = ["CLI"]


class CLI:
    """Command Line Interface для racing report"""

    @staticmethod
    def run() -> None:
        """
        Точка входу CLI.

        Команди:
        1. --files <folder> --asc/--desc
           Показує список всіх гонщиків

        2. --files <folder> --driver "Sebastian Vettel"
           Показує статистику конкретного гонщика

        Приклади:
        python report.py --files data/
        python report.py --files data/ --desc
        python report.py --files data/ --driver "Daniel Ricciardo"

        Args:
            folder: Шлях до папки з даними
            asc: True для сортування за зростанням
            desc: True для сортування за спаданням
            driver: Ім'я гонщика для фільтрації (опціонально)

        Returns:
            None
        """

        # Створення parser
        parser = argparse.ArgumentParser(
            description="Monaco 2018 Racing Q1 Report",
            formatter_class=argparse.RawTextHelpFormatter,
            epilog="""
                    Examples:
                      monaco-report --files data/
                      monaco-report --files data/ --desc
                      monaco-report --files data/ --driver "Sebastian Vettel"
                                """,
        )

        # Додавання обовязкового аргументу --files
        parser.add_argument(
            "--files",
            type=str,
            required=True,
            help="Path to folder with data files "
            "(abbreviations.txt, start.log, end.log)",
        )

        # Додавання опціонального аргументу --asc/--desc
        order_group = parser.add_mutually_exclusive_group()
        order_group.add_argument(
            "--asc", action="store_true", help="Sort ascending (default)"
        )
        order_group.add_argument("--desc", action="store_true", help="Sort descending")

        # Додавання опціонального аргументу --driver
        parser.add_argument(
            "--driver", type=str, help="Show statistics for specific driver"
        )

        # Парсинг аргументів
        args = parser.parse_args()

        # Визначення порядку сортування
        asc = not args.desc  # За замовчуванням asc=True

        # Визначення шляху до папки з даними
        folder = Path(args.files)

        if not folder.exists():
            print(f"Folder {folder} does not exist")
            return

        if not folder.is_dir():
            print(f"Folder {folder} is not a directory")
            return

        # Побудова звіту
        try:
            good_records, bad_records = RaceReport.build_report(
                folder=folder, driver=args.driver, asc=asc
            )
            # Якщо немає записів, вивести повідомлення
            if not good_records and not bad_records:
                print("No records found")
                return

            if args.driver and not good_records:
                print(f"Driver {args.driver} not found or has no records")
                if bad_records:
                    print("=== Records with errors ===")
                    for record in bad_records:
                        print(record)
                return

            # Якщо є записів, вивести звіт
            report_text = RaceReport.print_report(
                good_records=good_records, bad_records=bad_records
            )

            # Вивести заголовок
            print("=" * 70)
            if args.driver:
                print(f"REPORT FOR DRIVER: {args.driver}")
            else:
                order_text = "ASC" if asc else "DESC"
                print(f"MONACO 2018 RACING Q1 REPORT ({order_text} ORDER)")
            print("=" * 70)
            print()

            # Вивести звіт
            print(report_text)

        except FileNotFoundError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


def main():
    """Entry point для пакету"""
    CLI.run()


if __name__ == "__main__":
    main()
