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


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


class Settings:
    # --- Учётные данные Tuya IoT Platform (bootstrap) ---
    access_id: str = os.getenv("TUYA_ACCESS_ID", "").strip()
    access_key: str = os.getenv("TUYA_ACCESS_KEY", "").strip()
    endpoint: str = os.getenv("TUYA_API_ENDPOINT", "https://openapi.tuyaeu.com").strip().rstrip("/")

    # Список устройств (bootstrap): файл или одно устройство из окружения.
    devices_config: str = os.getenv("DEVICES_CONFIG", "config/devices.yml").strip()
    device_id: str = os.getenv("TUYA_DEVICE_ID", "").strip()
    device_name: str = os.getenv("TUYA_DEVICE_NAME", "Батарея").strip()

    poll_interval: int = _get_int("POLL_INTERVAL", 10)
    demo_mode: bool = _get_bool("DEMO_MODE", False)

    # Целевой уровень заряда, % (bootstrap): до него считается оставшееся время
    # на дашборде, он же порог уведомления о низком заряде.
    target_soc: int = _get_int("TARGET_SOC", 30)

    # Оформление по умолчанию (bootstrap); допустимые значения — THEMES в app/store.py.
    theme: str = os.getenv("THEME", "").strip()

    # Язык по умолчанию (bootstrap); допустимые значения — LANGS в app/i18n.py.
    language: str = os.getenv("LANGUAGE", "").strip()

    # Ссылка на исходники в футере. AGPL-3.0 §13 требует, чтобы изменённая
    # версия давала своим пользователям доступ к исходному коду — форку нужно
    # указать здесь свой репозиторий. Пустая строка убирает ссылку.
    source_url: str = os.getenv(
        "SOURCE_URL", "https://github.com/scatari69/batterypitek").strip()

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
