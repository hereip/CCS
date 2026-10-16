"""ACS — Autostart Complete Sir.

Читает автозагрузку Windows (реестр + папки Startup),
ждёт запуска программ и уведомляет.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

try:
    import winreg
except ImportError:
    print("[ACS] Модуль winreg доступен только на Windows.", file=sys.stderr)
    winreg = None  # type: ignore

try:
    import psutil
except ImportError:
    print("[ACS] Установи psutil: pip install psutil", file=sys.stderr)
    raise

from .notify import notify_error, notify_info, notify_success


# --- Источники автозагрузки ---------------------------------------------------

RUN_KEYS = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run") if winreg else None,
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run") if winreg else None,
    (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run") if winreg else None,
]
RUN_KEYS = [k for k in RUN_KEYS if k is not None]

STARTUP_DIRS = [
    Path.home() / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup",
    Path("C:/ProgramData/Microsoft/Windows/Start Menu/Programs/Startup"),
]

# Имена, которые никогда не проверяем (сам ACS, обёртки)
SELF_NAMES = {"acs", "acs.bat", "acs.exe", "ccs", "ccs.bat", "ccs.exe", "python", "pythonw"}


# --- Чтение автозагрузки ------------------------------------------------------

def get_autostart_entries() -> dict[str, str]:
    """Возвращает {имя: команда_запуска} из реестра и папок Startup."""
    entries: dict[str, str] = {}

    for hive, path in RUN_KEYS:
        try:
            with winreg.OpenKey(hive, path) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        entries[name] = value
                        i += 1
                    except OSError:
                        break
        except FileNotFoundError:
            continue

    for d in STARTUP_DIRS:
        if d.exists():
            for f in d.iterdir():
                if f.suffix.lower() in (".lnk", ".exe", ".bat", ".cmd"):
                    entries[f"[Startup] {f.stem}"] = str(f)

    return entries


def extract_exe_name(value: str) -> str:
    """Из строки автозагрузки вытаскивает имя .exe (в нижнем регистре)."""
    value = value.strip()
    if not value:
        return ""

    # Путь в кавычках: "C:\Program Files\App\app.exe" --arg
    if value.startswith('"'):
        end = value.find('"', 1)
        if end > 0:
            return Path(value[1:end]).name.lower()

    # Без кавычек, но с аргументами: C:\App\app.exe --arg
    low = value.lower()
    idx = low.find(".exe")
    if idx > 0:
        path_part = value[: idx + 4]
        return Path(path_part).name.lower()

    return Path(value).name.lower()


def is_running(exe_name: str) -> bool:
    """Запущен ли процесс с таким именем .exe?"""
    if not exe_name:
        return False
    for proc in psutil.process_iter(["name"]):
        try:
            name = proc.info.get("name")
            if name and name.lower() == exe_name:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


# --- Режим «ждём и докладываем» ----------------------------------------------

def wait_all_loaded(
    entries: dict[str, str],
    timeout: int = 60,
    interval: float = 2.0,
) -> tuple[list[str], list[str], int]:
    """Ждёт, пока все процессы из автозагрузки запустятся.

    Returns:
        (загруженные, отсутствующие, время_ожидания_сек)
    """
    expected = {n: extract_exe_name(p) for n, p in entries.items()}
    expected = {n: e for n, e in expected.items() if e}

    print(f"[ACS] Ожидаем {len(expected)} процессов из автозагрузки...")
    start = time.time()

    while time.time() - start < timeout:
        missing = [n for n, exe in expected.items() if not is_running(exe)]
        if not missing:
            break
        loaded_count = len(expected) - len(missing)
        preview = ", ".join(missing[:5])
        more = f" (+{len(missing) - 5})" if len(missing) > 5 else ""
        print(f"[ACS] {loaded_count}/{len(expected)}: ждём {preview}{more}")
        time.sleep(interval)

    elapsed = int(time.time() - start)
    loaded = [n for n, exe in expected.items() if is_running(exe)]
    missing = [n for n, exe in expected.items() if not is_running(exe)]
    return loaded, missing, elapsed


def run_once(entries: dict[str, str], timeout: int, interval: float, sound: bool) -> None:
    """Разовая проверка: ждём загрузки, потом одно сводное уведомление."""
    loaded, missing, elapsed = wait_all_loaded(entries, timeout=timeout, interval=interval)
    total = len(loaded) + len(missing)

    if not missing:
        notify_success(
            "✓ Autostart Complete, Sir",
            f"Все {total} программ запущены за {elapsed}с.",
            duration=10,
            sound=sound,
        )
    else:
        preview = ", ".join(missing[:8])
        more = f" (+{len(missing) - 8})" if len(missing) > 8 else ""
        notify_error(
            "⚠ Autostart — не всё запустилось",
            f"Запущено {len(loaded)}/{total} за {elapsed}с.\n"
            f"Не поднялись: {preview}{more}",
            duration=12,
            sound=sound,
        )


def run_live(entries: dict[str, str], timeout: int, interval: float, sound: bool) -> None:
    """Живой режим: уведомление на каждый стартующй процесс."""
    expected = {n: extract_exe_name(p) for n, p in entries.items()}
    expected = {n: e for n, e in expected.items() if e}

    print(f"[ACS] Живой мониторинг {len(expected)} процессов...")
    start = time.time()
    seen: set[str] = set()

    while time.time() - start < timeout:
        for name, exe in expected.items():
            if name in seen:
                continue
            if is_running(exe):
                seen.add(name)
                elapsed = int(time.time() - start)
                notify_info(
                    f"✓ {name} запущен",
                    f"Процесс {exe} поднялся за {elapsed}с.",
                    duration=4,
                    sound=sound,
                )
                print(f"[ACS] {name} ({exe}) запущен за {elapsed}с")
        if len(seen) == len(expected):
            break
        time.sleep(interval)

    missing = [n for n in expected if n not in seen]
    if missing:
        notify_error(
            "⚠ Autostart — не всё запустилось",
            f"Не поднялись: {', '.join(missing[:8])}",
            duration=10,
            sound=sound,
        )
    else:
        notify_success(
            "✓ Autostart Complete, Sir",
            f"Все {len(expected)} процессов подняты.",
            duration=8,
            sound=sound,
        )


# --- Install / Uninstall ------------------------------------------------------

ACS_REG_NAME = "CommandCompleteSir_ACS"


def install_to_autostart() -> None:
    """Прописывает ACS в HKCU\\...\\Run."""
    if not winreg:
        print("[ACS] Установка автозапуска доступна только на Windows.")
        return

    # pythonw.exe — без окна консоли
    python_exe = Path(sys.executable)
    pythonw = python_exe.with_name("pythonw.exe")
    exe = pythonw if pythonw.exists() else python_exe

    cmd = f'"{exe}" -m ccs.cli_acs'

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, ACS_REG_NAME, 0, winreg.REG_SZ, cmd)
        print(f"[ACS] Установлено в автозагрузку:\n  {cmd}")
    except OSError as e:
        print(f"[ACS] Не удалось установить: {e}")


def uninstall_from_autostart() -> None:
    """Убирает ACS из автозагрузки."""
    if not winreg:
        return
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.DeleteValue(key, ACS_REG_NAME)
        print("[ACS] Удалено из автозагрузки.")
    except FileNotFoundError:
        print("[ACS] ACS не найден в автозагрузке.")
    except OSError as e:
        print(f"[ACS] Не удалось удалить: {e}")
