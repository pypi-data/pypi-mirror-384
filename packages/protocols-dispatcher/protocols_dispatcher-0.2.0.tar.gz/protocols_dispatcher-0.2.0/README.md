# protocols_dispatcher

> **Гибкая асинхронная библиотека для диспетчеризации бинарных протоколов**

`protocols_dispatcher` упрощает жизнь, когда нужно:

* **принять поток байтов** → превратить в «пакеты» (словарь Python);
* **выбрать обработчик** по произвольным фильтрам;
* **отправить ответ** тем же транспортом или другим;
* легко **добавлять свои протоколы и транспорты** (TCP, serial, файлы — любые).

Библиотека уже используется в производственном проекте для работы с наборами микроконтроллеров и бинарных команд.

[![PyPI version](https://img.shields.io/pypi/v/protocols_dispatcher?color=brightgreen)](https://pypi.org/project/protocols_dispatcher/)
![License](https://img.shields.io/github/license/Enigma0960/protocols_dispatcher)

---

## 📦 Установка

```bash
# минимальный набор
pip install protocols_dispatcher

# + поддержка работы по последовательному порту через aioserial
pip install protocols_dispatcher[serial]
```

| extra    | что подтягивает                                    |   |
| -------- | -------------------------------------------------- | - |
| `serial` | [`aioserial`](https://pypi.org/project/aioserial/) |   |

---

## 🚀 Быстрый старт

```python
import asyncio
from protocols_dispatcher import Dispatcher, AbstractProtocol, AbstractTransport
from protocols_dispatcher.transports.serial import SerialTransport

class EchoProtocol(AbstractProtocol):
    async def matches(self, raw: bytes) -> bool:
        # «Принимаем» любой кадр
        return True

    async def deserialize(self, data: bytes):
        # Каждый пришедший фрейм — отдельный «пакет»
        return [dict(raw=data)]

    async def serialize(self, packet: dict):
        # Просто оборачиваем в префикс
        return b"ACK:" + packet["raw"]

async def main():
    proto     = EchoProtocol()
    transport = SerialTransport(port="/dev/ttyUSB0", baudrate=115200)

    dsp = Dispatcher(proto, transport)

    @dsp.handler()              # без фильтров — ловим всё
    async def handle(pkt):
        print("RX:", pkt["raw"].hex())
        # сформируем и отправим ответ
        return dict(raw=pkt["raw"])

    # транспорт запускается отдельной корутиной
    await transport.run()

asyncio.run(main())
```

---

## 🔍 Основные возможности

* **Асинхронность на всех уровнях** — от транспорта до callback-ов.
* **Паттерн «декоратор‑фильтр»**

  ```python
  @dispatcher.handler(MyFilter())
  def on_custom(pkt): ...
  ```

  либо через `router.handler(filter=..., protocol=...)`, если протоколов несколько.
* **ProtocolRouter** — маршрутизация, когда по одному каналу идёт несколько независимых бинарных протоколов.
* **Тестирование из коробки** — примерные `DummyProtocol` / `DummyTransport` и фикстуры для `pytest`.
* **Extras‑dependencies** — лишние зависимости ставятся только при необходимости.

---

## 🗂️ Структура проекта

```
📦 protocols_dispatcher
 ├─ __init__.py
 ├─ dispatcher.py          # ядро: AbstractProtocol / AbstractTransport / Dispatcher / ProtocolRouter
 ├─ transports/
 │   ├─ __init__.py
 │   └─ serial.py          # SerialTransport (опция [serial])
 └─ tests/
     ├─ helpers.py         # заглушки для юнит‑тестов
     ├─ conftest.py
     └─ ...
```

---

## 🧪 Запуск тестов

```bash
git clone https://github.com/your-github/protocols_dispatcher.git
cd protocols_dispatcher
pip install -e .[dev]      # dev‑зависимости: pytest, pytest-asyncio, ruff, mypy ...
pytest -q
```

---

## 🤝 Контрибьюция

1. Сделайте форк, создайте ветку `feature/whatever`.
2. `pre-commit install` — сразу проверит code‑style.
3. Напишите тесты к новому коду.
4. Отправьте PR и опишите, зачем change полезен.

---

## 📄 Лицензия

Проект распространяется под лицензией MIT — см. файл [LICENSE](LICENSE).

---

### 🙌 Авторы и благодарности

* **Игорь Супрядкин** — архитектура и основная реализация
* **ChatGPT** — помощь в проработке решений и написаний документации

> Если библиотека помогла вам — поставьте ⭐️ в GitHub и расскажите о ней коллегам!
