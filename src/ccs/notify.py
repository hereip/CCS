"""Единый модуль уведомлений для CCS и ACS.

Использует plyer, если установлен, иначе падает обратно на PowerShell MessageBox.
Звук — через winsound (только Windows).
"""

from __future__ import annotations

import subprocess
import sys
import time

# --- Опциональные зависимости -------------------------------------------------

try:
    from plyer import notification as _plyer_notification
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False

try:
    import winsound
    HAS_SOUND = True
except ImportError:
    HAS_SOUND = False  # не Windows или нет модуля

# --- Звуковые сигналы ---------------------------------------------------------

# (частота Гц, длительность мс)
SOUND_SUCCESS = [(880, 150), (1200, 250)]
SOUND_ERROR = [(600, 200), (400, 350)]
SOUND_INFO = [(1000, 200)]


def _play_sound(pattern):
    """Проигрывает последовательность beep-ов."""
    if not HAS_SOUND:
        return
    try:
        for freq, dur in pattern:
            winsound.Beep(freq, dur)
            time.sleep(0.03)
    except Exception:
        # на некоторых системах winsound.Beep может кидать ошибку
        pass


# --- PowerShell fallback ------------------------------------------------------

_PS_FALLBACK = (
    '[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms") | Out-Null;'
    '[System.Windows.Forms.MessageBox]::Show("{msg}", "{title}")'
)


def _notify_powershell(title: str, message: str):
    """Фоллбэк через MessageBox, если plyer недоступен."""
    ps = _PS_FALLBACK.format(
        title=title.replace('"', "'"),
        msg=message.replace('"', "'"),
    )
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", ps],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception as e:
        print(f"[CCS] Не удалось показать уведомление: {e}", file=sys.stderr)


# --- Основная функция ---------------------------------------------------------

def notify(
    title: str,
    message: str,
    duration: int = 8,
    sound: bool = True,
    sound_type: str = "info",
) -> None:
    """Показывает уведомление и (опционально) играет звук.

    Args:
        title: Заголовок уведомления.
        message: Текст уведомления.
        duration: Сколько секунд показывать (plyer).
        sound: Играть ли звук.
        sound_type: 'success' | 'error' | 'info'.
    """
    if HAS_PLYER:
        try:
            _plyer_notification.notify(
                title=title,
                message=message,
                app_name="Command Complete Sir",
                timeout=duration,
            )
        except Exception as e:
            print(f"[CCS] plyer не сработал: {e}, пробую PowerShell...", file=sys.stderr)
            _notify_powershell(title, message)
    else:
        _notify_powershell(title, message)

    if sound:
        pattern = {
            "success": SOUND_SUCCESS,
            "error": SOUND_ERROR,
            "info": SOUND_INFO,
        }.get(sound_type, SOUND_INFO)
        _play_sound(pattern)


def notify_success(title: str, message: str, duration: int = 8, sound: bool = True) -> None:
    notify(title, message, duration=duration, sound=sound, sound_type="success")


def notify_error(title: str, message: str, duration: int = 8, sound: bool = True) -> None:
    notify(title, message, duration=duration, sound=sound, sound_type="error")


def notify_info(title: str, message: str, duration: int = 6, sound: bool = True) -> None:
    notify(title, message, duration=duration, sound=sound, sound_type="info")
