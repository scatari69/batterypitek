"""Загрузка списка устройств: id + человекочитаемое имя.

Источник (по приоритету):
  1. Демо-режим — набор виртуальных устройств.
  2. YAML-файл DEVICES_CONFIG (по умолчанию config/devices.yml).
  3. Одно устройство из переменных окружения TUYA_DEVICE_ID / TUYA_DEVICE_NAME.
"""

import os
from dataclasses import dataclass

from .config import settings


@dataclass(frozen=True)
class Device:
    id: str
    name: str


def load_devices():
    # 1. Демо-режим.
    if settings.use_demo:
        from . import demo

        return [Device(d["id"], d["name"]) for d in demo.DEMO_DEVICES]

    # 2. YAML-файл со списком.
    path = settings.devices_config
    if path and os.path.exists(path):
        import yaml

        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        result = []
        for entry in data.get("devices", []) or []:
            did = str(entry.get("id", "")).strip()
            if not did:
                continue
            name = str(entry.get("name") or did).strip()
            result.append(Device(did, name))
        if result:
            return result

    # 3. Одно устройство из окружения.
    if settings.device_id:
        return [Device(settings.device_id, settings.device_name)]

    return []
