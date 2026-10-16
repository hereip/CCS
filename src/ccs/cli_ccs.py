"""Точка входа команды ccs — Command Complete Sir."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .history import show_history
from .runner import run_command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ccs",
        description="Command Complete Sir — уведомление о завершении команды.",
        usage="ccs [флаги] <команда> [аргументы...]",
        epilog="Примеры:\n"
               "  ccs ping 127.0.0.1 -n 60\n"
               "  ccs --time --no-sound npm run build\n"
               "  ccs --title \"Сборка\" make all\n"
               "  ccs --history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"ccs {__version__}")
    parser.add_argument("--time", action="store_true",
                        help="Показать время выполнения")
    parser.add_argument("--no-sound", action="store_true",
                        help="Без звукового сигнала")
    parser.add_argument("--title", type=str, default=None,
                        help="Своё название в уведомлении")
    parser.add_argument("--timeout", type=int, default=None, metavar="СЕК",
                        help="Прервать команду через N секунд")
    parser.add_argument("--log", action="store_true",
                        help="Сохранить запуск в историю")
    parser.add_argument("--history", action="store_true",
                        help="Показать историю запусков и выйти")
    parser.add_argument("--history-limit", type=int, default=20, metavar="N",
                        help="Сколько записей истории показать (по умолчанию 20)")
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="Команда и её аргументы (всё после флагов)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.history:
        show_history(limit=args.history_limit)
        return 0

    if not args.command:
        parser.print_help()
        return 1

    cmd = " ".join(args.command)
    return run_command(
        cmd,
        show_time=args.time,
        sound=not args.no_sound,
        title=args.title,
        timeout=args.timeout,
        log=args.log,
    )


if __name__ == "__main__":
    sys.exit(main())
