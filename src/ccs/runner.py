"""Запуск команды, замер времени, таймаут, уведомление."""

from __future__ import annotations

import subprocess
import sys
import time
from typing import Optional

from .history import log_run
from .notify import notify_error, notify_success


def run_command(
    cmd: str,
    *,
    show_time: bool = False,
    sound: bool = True,
    title: Optional[str] = None,
    timeout: Optional[int] = None,
    log: bool = False,
) -> int:
    """Запускает команду и уведомляет о завершении.

    Args:
        cmd: Команда целиком (строка).
        show_time: Показать время в консоли после завершения.
        sound: Играть звук.
        title: Своё название в уведомлении.
        timeout: Прервать через N секунд (None — без лимита).
        log: Записать в history.jsonl.

    Returns:
        Код возврата команды (или 124 при таймауте).
    """
    print(f"[CCS] Запуск: {cmd}")
    if timeout:
        print(f"[CCS] Лимит: {timeout}с")
    start = time.time()

    timed_out = False
    try:
        proc = subprocess.Popen(cmd, shell=True)
        try:
            returncode = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            proc.wait()
            returncode = 124  # стандартный код для timeout
    except KeyboardInterrupt:
        print("\n[CCS] Прервано пользователем (Ctrl+C).")
        elapsed = time.time() - start
        notify_error(
            "✗ Прервано, сэр",
            f"Команда остановлена через {elapsed:.1f}с.",
            sound=sound,
        )
        return 130

    elapsed = time.time() - start
    minutes, seconds = divmod(int(elapsed), 60)
    time_str = f"{minutes}м {seconds}с" if minutes else f"{seconds}с"

    # --- Уведомление ---
    if timed_out:
        n_title = "⏱ Таймаут, сэр"
        n_msg = f"Команда прервана через {timeout}с.\n{cmd[:80]}"
    elif returncode == 0:
        n_title = title or "✓ Готово, сэр"
        n_msg = f"Команда выполнена за {time_str}.\n{cmd[:80]}"
    else:
        n_title = f"✗ Ошибка, сэр (код {returncode})"
        n_msg = f"Команда упала за {time_str}.\n{cmd[:80]}"

    if timed_out or returncode != 0:
        notify_error(n_title, n_msg, sound=sound)
    else:
        notify_success(n_title, n_msg, sound=sound)

    # --- Консольный вывод ---
    if show_time or timed_out:
        print(f"[CCS] Время: {time_str}")
    print(f"[CCS] Код возврата: {returncode}")

    # --- Лог ---
    if log:
        log_run(cmd, returncode, elapsed, title=title)

    return returncode
