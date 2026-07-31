"""Генератор демо-данных — правдоподобные показания без обращения к Tuya.

Проходит через тот же путь нормализации, что и реальные данные: возвращает
«сырой» статус и спецификацию, как их отдал бы Tuya Cloud. Каждое виртуальное
устройство ведёт себя по-своему (разный заряд, кто-то разряжается, кто-то нет).
"""

import math
import time

from . import i18n

# Виртуальные устройства для демо-режима. Имя здесь — запасное: показываем
# перевод по ключу demo.<id> (см. app/i18n.py), см. device_name().
DEMO_DEVICES = [
    {"id": "demo-garage", "name": "Гараж — LiFePO4 100Ah",
     "capacity": 100.0, "base_soc": 72, "phase": 0.0, "mode": "discharge"},
    {"id": "demo-home", "name": "Дом — резервный АКБ 200Ah",
     "capacity": 200.0, "base_soc": 54, "phase": 1.7, "mode": "discharge"},
    {"id": "demo-van", "name": "Кемпер — 120Ah",
     "capacity": 120.0, "base_soc": 88, "phase": 3.1, "mode": "charge"},
    {"id": "demo-solar", "name": "Солар-буфер 280Ah",
     "capacity": 280.0, "base_soc": 41, "phase": 4.6, "mode": "discharge"},
]

_BY_ID = {d["id"]: d for d in DEMO_DEVICES}

# Спецификация, имитирующая типовой кулоновский счётчик (значения масштабируются).
DEMO_SPEC = {
    "category": "z nldcp",
    "status": [
        {"code": "cur_voltage", "type": "Integer",
         "values": '{"unit":"V","min":0,"max":10000,"scale":2,"step":1}'},
        {"code": "cur_current", "type": "Integer",
         "values": '{"unit":"A","min":-10000,"max":10000,"scale":2,"step":1}'},
        {"code": "cur_power", "type": "Integer",
         "values": '{"unit":"W","min":0,"max":100000,"scale":1,"step":1}'},
        {"code": "battery_percentage", "type": "Integer",
         "values": '{"unit":"%","min":0,"max":100,"scale":0,"step":1}'},
        {"code": "remain_capacity", "type": "Integer",
         "values": '{"unit":"Ah","min":0,"max":100000,"scale":2,"step":1}'},
        {"code": "total_capacity", "type": "Integer",
         "values": '{"unit":"Ah","min":0,"max":100000,"scale":2,"step":1}'},
        {"code": "temp_current", "type": "Integer",
         "values": '{"unit":"℃","min":-40,"max":120,"scale":0,"step":1}'},
        {"code": "cumulative_discharge", "type": "Integer",
         "values": '{"unit":"Ah","min":0,"max":1000000,"scale":2,"step":1}'},
    ],
}


def device_name(device_id: str, lang: str | None = None) -> str:
    """Имя виртуального устройства на нужном языке."""
    key = f"demo.{device_id}"
    name = i18n.t(lang, key)
    if name != key:
        return name
    cfg = _BY_ID.get(device_id)
    return cfg["name"] if cfg else device_id


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def demo_status(device_id=None):
    cfg = _BY_ID.get(device_id, DEMO_DEVICES[0])
    t = time.time()
    phase = cfg["phase"]
    cap = cfg["capacity"]

    # Медленный дрейф заряда, чтобы дашборд «жил».
    soc = _clamp(cfg["base_soc"] + 8.0 * math.sin(t / 240.0 + phase), 3.0, 100.0)

    ripple = 0.8 + 0.2 * math.sin(t / 30.0 + phase)
    if cfg["mode"] == "charge":
        current = cap * 0.05 * ripple            # заряд, +A (~0.05C)
    else:
        current = -cap * 0.05 * ripple           # разряд, -A (~0.05C)

    voltage = 12.9 + 0.5 * math.sin(t / 40.0 + phase)
    power = abs(voltage * current)
    temp = 24.0 + 4.0 * math.sin(t / 120.0 + phase)
    remain_ah = cap * soc / 100.0

    return [
        {"code": "cur_voltage", "value": round(voltage * 100)},
        {"code": "cur_current", "value": round(current * 100)},
        {"code": "cur_power", "value": round(power * 10)},
        {"code": "battery_percentage", "value": round(soc)},
        {"code": "remain_capacity", "value": round(remain_ah * 100)},
        {"code": "total_capacity", "value": round(cap * 100)},
        {"code": "temp_current", "value": round(temp)},
        {"code": "cumulative_discharge", "value": round((1000.0 + (t % 500)) * 100)},
    ]


def demo_specifications(device_id=None):
    return DEMO_SPEC
