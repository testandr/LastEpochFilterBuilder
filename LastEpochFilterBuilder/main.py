"""CLI заглушка для проекта Last Epoch Filter Generator."""
import argparse


def main():
    parser = argparse.ArgumentParser(description="Last Epoch Filter Generator CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("update", help="Обновить данные из Maxroll (заглушка)")
    sub.add_parser("generate", help="Сгенерировать фильтр (заглушка)")
    sub.add_parser("full-update", help="Обновить данные и сгенерировать фильтр (заглушка)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
    else:
        print(f"Команда '{args.command}' пока не реализована. Выполните следующую итерацию.")


if __name__ == "__main__":
    main()
