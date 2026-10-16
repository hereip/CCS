# CCS
Command Complete Sir — Windows notifications for finished commands and autostart apps.

# CCS — Command Complete Sir

> «Сэр, ваша команда завершилась.» 🫡
> Windows-уведомления для долгих задач и автозагрузки.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-0078D4.svg)]()

Название пришло с мема «сэр, да, сэр!». Два «адъютанта»:

- **`ccs`** — *Command Complete Sir*: докладывает, когда команда в терминале завершилась
- **`acs`** — *Autostart Complete Sir*: докладывает, когда программы из автозагрузки поднялись

## Зачем

Ты запускаешь долгую сборку, обучение модели или бэкап — и уходишь пить кофе.
CCS стукнет по ушам уведомлением, когда всё закончится, чтобы не бегать проверять.
ACS пришлёт сводку после логина — все ли программы из автозагрузки запустились.

## Установка

Требуется **Windows 10/11** и **Python 3.9+**.

```cmd
git clone https://github.com/hereip/CCS.git
cd CCS
pip install -e .
```

После этого в `PATH` появятся команды `ccs` и `acs`.

## Использование

### CCS — уведомление о завершении команды

```cmd
ccs ping 127.0.0.1 -n 60
ccs --time --no-sound npm run build
ccs --title "Обучение модели" python train.py
ccs --timeout 600 long_task.exe
ccs --log make all
ccs --history
```

| Флаг | Описание |
|---|---|
| `--time` | Показать время выполнения в консоли |
| `--no-sound` | Без звукового сигнала |
| `--title <текст>` | Своё название в уведомлении |
| `--timeout <сек>` | Прервать команду через N секунд |
| `--log` | Сохранить запуск в историю |
| `--history` | Показать историю запусков |
| `--history-limit <N>` | Сколько записей показать (по умолчанию 20) |

⚠️ Флаги `ccs` должны идти **до** команды — всё после первого не-флага считается командой.

### ACS — проверка автозагрузки

```cmd
acs                            :: разовая проверка (одно уведомление в конце)
acs --live                     :: уведомление на каждый запущенный процесс
acs --show                     :: просто вывести список автозагрузки
acs --timeout 120              :: ждать дольше (по умолчанию 60с)
acs --exclude chrome,discord   :: игнорировать эти программы
acs --install                  :: прописать ACS в автозагрузку
acs --uninstall                :: убрать ACS из автозагрузки
```

| Флаг | Описание |
|---|---|
| `--live` | Уведомление на каждый процесс отдельно |
| `--timeout <сек>` | Сколько ждать загрузки (по умолчанию 60) |
| `--interval <сек>` | Частота проверки (по умолчанию 2.0) |
| `--exclude a,b,c` | Исключить программы из проверки |
| `--show` | Показать список автозагрузки |
| `--no-sound` | Без звука |
| `--install` | Добавить ACS в автозагрузку |
| `--uninstall` | Убрать ACS из автозагрузки |

## Откуда читается автозагрузка

- `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
- `HKLM\Software\Microsoft\Windows\CurrentVersion\Run`
- `HKLM\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run`
- `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`
- `%ProgramData%\Microsoft\Windows\Start Menu\Programs\Startup`

## История

CCS пишет историю в `%APPDATA%\ccs\history.jsonl`.
Посмотреть — `ccs --history`, или открыть файл вручную.

## Roadmap

- [x] `ccs run` — уведомления о завершении команд
- [x] `acs` — проверка автозагрузки
- [x] `acs --live` — мониторинг в реальном времени
- [x] `--install` / `--uninstall` для ACS
- [x] История запусков
- [ ] Telegram-уведомления
- [ ] Трей-иконка (pystray)
- [ ] Сборка одного `.exe` через PyInstaller
- [ ] Поддержка Планировщика задач как источника автозагрузки

## Лицензия

[MIT](LICENSE) © 2026 hereip
