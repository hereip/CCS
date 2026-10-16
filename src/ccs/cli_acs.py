"""Точка входа команды acs — Autostart Complete Sir."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .autostart import (
    SELF_NAMES,
    get_autostart_entries,
    install_to_autostart,
    run_live,
    run_once,
    uninstall_from_autostart,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="acs",
        description="Autostart Complete Sir — проверка автозагрузки Windows.",
        usage="acs [флаги]",
        epilog="Примеры:\n"
               "  acs                          # разовая проверка, одно уведомление в конце\n"
               "  acs --live                   # уведомление на каждый процесс\n"
               "  acs --show                   # просто вывести список автозагрузки\n"
               "  acs --timeout 120            # ждать дольше\n"
               "  acs --exclude chrome,discord # игнорировать эти программы\n"
               "  acs --install                # прописать ACS в автозагрузку\n"
               "  acs --uninstall              # убрать ACS из автозагрузки",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"acs {__version__}")
    parser.add_argument("--live", action="store_true",
                        help="Уведомлять о каждом процессе отдельно")
    parser.add_argument("--timeout", type=int, default=60, metavar="СЕК",
                        help="Сколько секунд ждать загрузки (по умолчанию 60)")
    parser.add_argument("--interval", type=float, default=2.0, metavar="СЕК",
                        help="Частота проверки в секундах (по умолчанию 2.0)")
    parser.add_argument("--exclude", type=str, default="", metavar="СПИСОК",
                        help="Имена программ через запятую для исключения")
    parser.add_argument("--show", action="store_true",
                        help="Просто показать список автозагрузки")
    parser.add_argument("--no-sound", action="store_true",
                        help="Без звука")
    parser.add_argument("--install", action="store_true",
                        help="Добавить ACS в автозагрузку")
    parser.add_argument("--uninstall", action="store_true",
                        help="Удалить ACS из автозагрузки")
    return parser


def _filter_entries(entries: dict[str, str], excludes: set[str]) -> dict[str, str]:
    """Убирает из проверки себя и явные исключения."""
    result = {}
    for name, path in entries.items():
        low = name.lower()
        if low in excludes:
            continue
        # Отсеиваем собственные обёртки (acs.bat, ccs.exe и т.п.)
        if low in SELF_NAMES:
            continue
        # Отсеиваем, если имя начинается с acs (acs-something)
        if low.startswith("acs") and len(low) <= 6:
            continue
        result[name] = path
    return result


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.install:
        install_to_autostart()
        return 0
    if args.uninstall:
        uninstall_from_autostart()
        return 0

    excludes = {x.strip().lower() for x in args.exclude.split(",") if x.strip()}
    entries = get_autostart_entries()
    entries = _filter_entries(entries, excludes)

    if args.show:
        print(f"[ACS] Записей в автозагрузке: {len(entries)}\n")
        for name, path in sorted(entries.items()):
            print(f"  • {name}")
            print(f"      → {path}")
        return 0

    if not entries:
        print("[ACS] Автозагрузка пуста.")
        return 0

    sound = not args.no_sound
    if args.live:
        run_live(entries, timeout=args.timeout, interval=args.interval, sound=sound)
    else:
        run_once(entries, timeout=args.timeout, interval=args.interval, sound=sound)

    return 0


if __name__ == "__main__":
    sys.exit(main())
