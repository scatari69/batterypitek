"""Bootstrap-конфигурация из переменных окружения.

Это значения по умолчанию на первый запуск. После настройки через админ-панель
актуальные значения хранятся в DATA_DIR/settings.json (см. app/store.py) и имеют
приоритет над переменными окружения.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


class Settings:
    # --- Учётные данные Tuya IoT Platform (bootstrap) ---
    access_id: str = os.getenv("TUYA_ACCESS_ID", "").strip()
    access_key: str = os.getenv("TUYA_ACCESS_KEY", "").strip()
    endpoint: str = os.getenv("TUYA_API_ENDPOINT", "https://openapi.tuyaeu.com").strip().rstrip("/")

    # Список устройств (bootstrap): файл или одно устройство из окружения.
    devices_config: str = os.getenv("DEVICES_CONFIG", "config/devices.yml").strip()
    device_id: str = os.getenv("TUYA_DEVICE_ID", "").strip()
    device_name: str = os.getenv("TUYA_DEVICE_NAME", "Батарея").strip()

    poll_interval: int = int(os.getenv("POLL_INTERVAL", "10"))
    demo_mode: bool = _get_bool("DEMO_MODE", False)

    # Каталог для постоянных настроек (settings.json).
    data_dir: str = os.getenv("DATA_DIR", "data").strip()

    # Пароль админ-панели (bootstrap): если задан и пароль ещё не установлен —
    # будет использован при первом запуске.
    admin_password: str = os.getenv("ADMIN_PASSWORD", "").strip()

    @property
    def has_credentials(self) -> bool:
        return bool(self.access_id and self.access_key)

    @property
    def use_demo(self) -> bool:
        return self.demo_mode or not self.has_credentials


settings = Settings()
