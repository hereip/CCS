"""История запусков CCS — пишем в %APPDATA%\\ccs\\history.jsonl."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path


def _history_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    d = Path(base) / "ccs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _history_file() -> Path:
    return _history_dir() / "history.jsonl"


def log_run(
    command: str,
    returncode: int,
    elapsed: float,
    title: str | None = None,
) -> None:
    """Добавляет запись о запуске в history.jsonl."""
    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "command": command,
        "returncode": returncode,
        "elapsed": round(elapsed, 3),
        "title": title,
    }
    try:
        with _history_file().open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"[CCS] Не удалось записать историю: {e}")


def read_history(limit: int = 20) -> list[dict]:
    """Читает последние N записей (новые — первыми)."""
    path = _history_file()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    entries = []
    for line in lines[-limit:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(entries))


def show_history(limit: int = 20) -> None:
    """Печатает историю в консоль."""
    entries = read_history(limit)
    if not entries:
        print("[CCS] История пуста.")
        return
    print(f"[CCS] Последние {len(entries)} запусков:\n")
    for e in entries:
        status = "✓" if e["returncode"] == 0 else "✗"
        t = e["ts"].replace("T", " ")
        print(
            f"  {status} {t}  {e['elapsed']:>7.2f}с  "
            f"[{e['returncode']:>3}]  {e['command'][:60]}"
        )
