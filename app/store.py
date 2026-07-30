"""Постоянное хранилище настроек + рантайм-состояние приложения.

Настройки читаются из DATA_DIR/settings.json и имеют приоритет над переменными
окружения (bootstrap). Админ-панель меняет настройки на лету — клиент Tuya и
список устройств пересобираются без перезапуска.
"""

import json
import os
import secrets
import threading
from pathlib import Path

from . import auth, demo
from .config import settings
from .devices import Device, load_devices
from .tuya_client import TuyaClient

_ALLOWED_UPDATE = {"access_id", "access_key", "endpoint", "poll_interval", "demo_mode", "devices"}


class Store:
    def __init__(self):
        self.path = Path(settings.data_dir) / "settings.json"
        self._lock = threading.RLock()
        self._data: dict = {}
        self._client: TuyaClient | None = None
        self._client_sig = None
        self.load()

    # ---------------------------------------------------------------- I/O --
    def load(self):
        with self._lock:
            if self.path.exists():
                try:
                    self._data = json.loads(self.path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    self._data = {}
            else:
                self._data = {}

            changed = False
            if not self._data.get("server_secret"):
                self._data["server_secret"] = secrets.token_hex(32)
                changed = True
            if settings.admin_password and not self._data.get("admin_password_hash"):
                self._data["admin_password_hash"] = auth.hash_password(settings.admin_password)
                changed = True
            # Первичное заполнение списка устройств из env/yaml (не в демо-режиме).
            if "devices" not in self._data and not self._effective_demo():
                seeded = [{"id": d.id, "name": d.name} for d in load_devices()]
                if seeded:
                    self._data["devices"] = seeded
                    changed = True
            if changed:
                self._save_unlocked()

    def _save_unlocked(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp, self.path)
        except OSError as exc:
            # Не роняем приложение, если каталог настроек недоступен для записи.
            # Настройки продолжат действовать до перезапуска, но не сохранятся на диск.
            print(f"[store] ВНИМАНИЕ: не удалось сохранить настройки в {self.path}: {exc}. "
                  f"Проверьте права на каталог DATA_DIR.", flush=True)

    # ------------------------------------------------------------ Getters --
    @property
    def access_id(self) -> str:
        return (self._data.get("access_id") or settings.access_id).strip()

    @property
    def access_key(self) -> str:
        return (self._data.get("access_key") or settings.access_key).strip()

    @property
    def endpoint(self) -> str:
        return (self._data.get("endpoint") or settings.endpoint).strip().rstrip("/")

    @property
    def poll_interval(self) -> int:
        try:
            return int(self._data.get("poll_interval") or settings.poll_interval)
        except (TypeError, ValueError):
            return settings.poll_interval

    @property
    def demo_mode(self) -> bool:
        if "demo_mode" in self._data:
            return bool(self._data["demo_mode"])
        return settings.demo_mode

    def has_credentials(self) -> bool:
        return bool(self.access_id and self.access_key)

    def _effective_demo(self) -> bool:
        return self.demo_mode or not self.has_credentials()

    @property
    def use_demo(self) -> bool:
        return self._effective_demo()

    def devices(self):
        if self.use_demo:
            return [Device(d["id"], d["name"]) for d in demo.DEMO_DEVICES]
        if "devices" in self._data:
            return [Device(d["id"], d.get("name") or d["id"]) for d in self._data["devices"]]
        return load_devices()

    def device_map(self):
        return {d.id: d for d in self.devices()}

    # ------------------------------------------------------------- Client --
    def client(self):
        """Клиент Tuya для обычных операций (None в демо-режиме)."""
        if self.use_demo:
            return None
        return self.build_client(self.access_id, self.access_key, self.endpoint)

    def build_client(self, access_id: str, access_key: str, endpoint: str) -> TuyaClient:
        sig = (access_id, access_key, endpoint.rstrip("/"))
        with self._lock:
            if self._client is None or self._client_sig != sig:
                self._client = TuyaClient(*sig)
                self._client_sig = sig
            return self._client

    # --------------------------------------------------------------- Auth --
    @property
    def auth_enabled(self) -> bool:
        return bool(self._data.get("admin_password_hash"))

    def verify_password(self, password: str) -> bool:
        return auth.verify_password(password, self._data.get("admin_password_hash", ""))

    def set_password(self, password: str):
        with self._lock:
            self._data["admin_password_hash"] = auth.hash_password(password)
            self._save_unlocked()

    def _sign_key(self) -> str:
        return self._data.get("server_secret", "") + ":" + self._data.get("admin_password_hash", "")

    def make_token(self) -> str:
        return auth.make_token(self._sign_key())

    def verify_token(self, token: str) -> bool:
        return auth.verify_token(token, self._sign_key())

    # ------------------------------------------------------------- Update --
    def update(self, patch: dict):
        with self._lock:
            for key, value in patch.items():
                if key not in _ALLOWED_UPDATE:
                    continue
                if key == "access_key" and not value:
                    continue  # пустой секрет = оставить прежний
                if key == "endpoint" and value:
                    value = str(value).strip().rstrip("/")
                self._data[key] = value
            self._client = None  # пересобрать клиент под новые реквизиты
            self._save_unlocked()

    # -------------------------------------------------------- Public view --
    def public_settings(self) -> dict:
        ak = self.access_key
        return {
            "access_id": self.access_id,
            "endpoint": self.endpoint,
            "poll_interval": self.poll_interval,
            "demo_mode": self.demo_mode,
            "use_demo": self.use_demo,
            "has_key": bool(ak),
            "key_hint": ("••••" + ak[-4:]) if len(ak) >= 4 else ("••••" if ak else ""),
            # Список для редактора — сохранённая конфигурация, а не демо-устройства.
            "devices": [{"id": d.get("id"), "name": d.get("name") or d.get("id")}
                        for d in self._data.get("devices", []) or []],
            "auth_enabled": self.auth_enabled,
        }


store = Store()
