"""Минимальный клиент Tuya Cloud API.

Реализует подпись запросов (HMAC-SHA256, "signature v2"), кэширование токена
и получение статуса/спецификации устройства. Без внешних зависимостей, кроме
requests, чтобы поведение было прозрачным и не ломалось на обновлениях SDK.

Документация подписи: https://developer.tuya.com/en/docs/iot/singnature
"""

import hashlib
import hmac
import json
import threading
import time

import requests


class TuyaError(Exception):
    """Ошибка на стороне Tuya Cloud (неуспешный ответ API)."""


class TuyaClient:
    def __init__(self, access_id: str, access_key: str, endpoint: str, timeout: int = 15):
        self.access_id = access_id
        self.access_key = access_key
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout

        self._token = ""
        self._token_expire_at = 0.0
        self._lock = threading.Lock()
        self._session = requests.Session()

    # ------------------------------------------------------------------ #
    # Подпись
    # ------------------------------------------------------------------ #
    def _sign(self, payload: str) -> str:
        return (
            hmac.new(
                self.access_key.encode("utf-8"),
                payload.encode("utf-8"),
                hashlib.sha256,
            )
            .hexdigest()
            .upper()
        )

    @staticmethod
    def _string_to_sign(method: str, path: str, body: str = "") -> str:
        content_sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest()
        # method \n content-sha256 \n signature-headers \n url
        # signature-headers оставляем пустой строкой (мы их не подписываем).
        return f"{method}\n{content_sha256}\n\n{path}"

    # ------------------------------------------------------------------ #
    # Токен
    # ------------------------------------------------------------------ #
    def _get_token(self, force: bool = False) -> str:
        with self._lock:
            if not force and self._token and time.time() < self._token_expire_at - 30:
                return self._token

            path = "/v1.0/token?grant_type=1"
            t = str(int(time.time() * 1000))
            payload = self.access_id + t + self._string_to_sign("GET", path)
            headers = {
                "client_id": self.access_id,
                "sign": self._sign(payload),
                "t": t,
                "sign_method": "HMAC-SHA256",
            }
            resp = self._session.get(self.endpoint + path, headers=headers, timeout=self.timeout)
            data = resp.json()
            if not data.get("success"):
                raise TuyaError(
                    f"Не удалось получить токен: {data.get('msg')} (code {data.get('code')})"
                )
            result = data["result"]
            self._token = result["access_token"]
            self._token_expire_at = time.time() + int(result.get("expire_time", 7200))
            return self._token

    # ------------------------------------------------------------------ #
    # Запросы к API
    # ------------------------------------------------------------------ #
    def _request(self, method: str, path: str, _retry: bool = True):
        token = self._get_token()
        t = str(int(time.time() * 1000))
        payload = self.access_id + token + t + self._string_to_sign(method, path)
        headers = {
            "client_id": self.access_id,
            "access_token": token,
            "sign": self._sign(payload),
            "t": t,
            "sign_method": "HMAC-SHA256",
        }
        resp = self._session.request(
            method, self.endpoint + path, headers=headers, timeout=self.timeout
        )
        data = resp.json()
        if not data.get("success"):
            code = data.get("code")
            # 1010/1011/1004 — токен истёк/невалиден: обновляем и пробуем ещё раз.
            if _retry and code in (1010, 1011, 1004):
                self._get_token(force=True)
                return self._request(method, path, _retry=False)
            raise TuyaError(f"Ошибка API: {data.get('msg')} (code {code})")
        return data["result"]

    # ------------------------------------------------------------------ #
    # Высокоуровневые методы
    # ------------------------------------------------------------------ #
    def get_status(self, device_id: str):
        """Текущие значения точек данных: [{"code": ..., "value": ...}, ...]."""
        return self._request("GET", f"/v1.0/devices/{device_id}/status")

    def get_specifications(self, device_id: str):
        """Спецификация устройства: типы, единицы, масштаб точек данных."""
        return self._request("GET", f"/v1.0/devices/{device_id}/specifications")

    def get_device(self, device_id: str):
        """Мета-информация об устройстве (имя, онлайн/офлайн, категория)."""
        return self._request("GET", f"/v1.0/devices/{device_id}")

    def get_thing_properties(self, device_id: str):
        """Свойства по «Thing»-модели (v2.0). Часто полнее, чем /v1.0 status:
        включает кастомные DP (заряд, ёмкость), которых нет в стандартном статусе."""
        result = self._request("GET", f"/v2.0/cloud/thing/{device_id}/shadow/properties") or {}
        return result.get("properties", []) or []

    def get_thing_model(self, device_id: str):
        """Полная модель устройства (v2.0): единицы измерения и масштаб всех свойств."""
        result = self._request("GET", f"/v2.0/cloud/thing/{device_id}/model") or {}
        raw = result.get("model")
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return {}
        return raw or {}

    def get_associated_devices(self, page_size: int = 100):
        """Все устройства, привязанные к аккаунтам проекта (для авто-поиска)."""
        devices = []
        last_row_key = ""
        for _ in range(50):  # предохранитель от бесконечной пагинации
            path = f"/v1.0/iot-01/associated-users/devices?size={page_size}"
            if last_row_key:
                path += f"&last_row_key={last_row_key}"
            result = self._request("GET", path) or {}
            devices.extend(result.get("devices", []) or [])
            if not result.get("has_next"):
                break
            last_row_key = result.get("last_row_key", "")
            if not last_row_key:
                break
        return devices
