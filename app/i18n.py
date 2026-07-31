"""Локализация серверных сообщений.

Здесь только то, что рождается на сервере: ответы API, тексты уведомлений в
Telegram и имена демо-устройств. Весь интерфейс переводится на клиенте —
словари лежат в app/static/i18n.js.

Язык ответа API берётся из заголовка X-BM-Lang (его шлёт клиент, см. i18n.js),
а если заголовка нет — из общей настройки в админ-панели. Уведомления в
Telegram всегда идут на языке по умолчанию: получателя-браузера у них нет.
"""

LANGS = ("ru", "uk", "en")
LANG_DEFAULT = LANGS[0]

MESSAGES: dict[str, dict[str, str]] = {
    "ru": {
        # --- Публичный API ---
        "err.unknown_device": "Неизвестное устройство",
        "err.auth_required": "Требуется авторизация",
        "err.generic": "Ошибка: {msg}",
        "err.internal": "Внутренняя ошибка: {msg}",

        # --- Админ-панель ---
        "admin.wrong_password": "Неверный пароль",
        "admin.need_creds": "Укажите Access ID и Access Secret",
        "admin.conn_error": "Ошибка соединения: {msg}",
        "admin.conn_ok": "Подключение успешно. Устройств в аккаунте: {n}",
        "admin.conn_token_only": "Токен получен, но список устройств недоступен: {msg}",
        "admin.save_creds_first": "Сначала укажите и сохраните реквизиты Tuya",
        "admin.pw_too_short": "Пароль слишком короткий (минимум 4 символа)",
        "admin.pw_wrong_current": "Неверный текущий пароль",

        # --- Telegram ---
        "tg.need_token": "Укажите токен бота",
        "tg.need_chat": "Укажите ID чата",
        "tg.no_token": "Не задан токен бота",
        "tg.no_chat": "Не задан ID чата",
        "tg.net": "Сеть недоступна: {msg}",
        "tg.bad_response": "Некорректный ответ Telegram (HTTP {code})",
        "tg.api_error": "Ошибка Telegram (HTTP {code})",
        "tg.test_text": "✅ Battery Monitor: проверка связи.\n"
                        "Уведомления о заряде батарей будут приходить в этот чат.",
        "tg.test_sent": "Сообщение отправлено ботом @{name}",
        "tg.bot": "бот",
        "tg.no_chats": "Чаты не найдены. Напишите боту любое сообщение (или добавьте его "
                       "в группу) и повторите.",
        "tg.chats_found": "Найдено чатов: {n}",

        # --- Тексты уведомлений ---
        "note.demo": "🧪 (демо) ",
        "note.offline": "⚠️ {name}: устройство недоступно\n{msg}",
        "note.online": "✅ {name}: связь восстановлена",
        "note.low_soc": "🪫 {name}: заряд {soc}% — ниже порога {limit}%",
        "note.soc_ok": "🔋 {name}: заряд восстановился до {soc}%",
        "note.low_eta": "⏳ {name}: до {limit}% осталось ~{eta} (порог {threshold} мин)",
        "note.soc_line": "Заряд {soc}%",
        "note.eta_ok": "✅ {name}: запас времени в норме",
        "note.eta_ok_tail": " (~{eta} до {limit}%)",

        # --- Режим работы и роли метрик (для строки показаний) ---
        "state.charging": "заряжается",
        "state.discharging": "разряжается",
        "state.idle": "ожидание",
        "state.unknown": "режим неизвестен",
        "role.voltage": "Напряжение",
        "role.current": "Ток",
        "role.power": "Мощность",

        # --- Длительность ---
        "dur.dash": "—",
        "dur.m": "{m} мин",
        "dur.hm": "{h} ч {m:02d} мин",
        "dur.dh": "{d} дн {h} ч",

        # --- Демо-устройства ---
        "demo.demo-garage": "Гараж — LiFePO4 100Ah",
        "demo.demo-home": "Дом — резервный АКБ 200Ah",
        "demo.demo-van": "Кемпер — 120Ah",
        "demo.demo-solar": "Солар-буфер 280Ah",
    },

    "uk": {
        "err.unknown_device": "Невідомий пристрій",
        "err.auth_required": "Потрібна авторизація",
        "err.generic": "Помилка: {msg}",
        "err.internal": "Внутрішня помилка: {msg}",

        "admin.wrong_password": "Невірний пароль",
        "admin.need_creds": "Вкажіть Access ID і Access Secret",
        "admin.conn_error": "Помилка з'єднання: {msg}",
        "admin.conn_ok": "Підключення успішне. Пристроїв в акаунті: {n}",
        "admin.conn_token_only": "Токен отримано, але список пристроїв недоступний: {msg}",
        "admin.save_creds_first": "Спершу вкажіть і збережіть реквізити Tuya",
        "admin.pw_too_short": "Пароль закороткий (мінімум 4 символи)",
        "admin.pw_wrong_current": "Невірний поточний пароль",

        "tg.need_token": "Вкажіть токен бота",
        "tg.need_chat": "Вкажіть ID чату",
        "tg.no_token": "Не задано токен бота",
        "tg.no_chat": "Не задано ID чату",
        "tg.net": "Мережа недоступна: {msg}",
        "tg.bad_response": "Некоректна відповідь Telegram (HTTP {code})",
        "tg.api_error": "Помилка Telegram (HTTP {code})",
        "tg.test_text": "✅ Battery Monitor: перевірка зв'язку.\n"
                        "Сповіщення про заряд батарей приходитимуть у цей чат.",
        "tg.test_sent": "Повідомлення надіслано ботом @{name}",
        "tg.bot": "бот",
        "tg.no_chats": "Чатів не знайдено. Напишіть боту будь-яке повідомлення (або додайте "
                       "його в групу) і повторіть.",
        "tg.chats_found": "Знайдено чатів: {n}",

        "note.demo": "🧪 (демо) ",
        "note.offline": "⚠️ {name}: пристрій недоступний\n{msg}",
        "note.online": "✅ {name}: зв'язок відновлено",
        "note.low_soc": "🪫 {name}: заряд {soc}% — нижче порога {limit}%",
        "note.soc_ok": "🔋 {name}: заряд відновився до {soc}%",
        "note.low_eta": "⏳ {name}: до {limit}% лишилося ~{eta} (поріг {threshold} хв)",
        "note.soc_line": "Заряд {soc}%",
        "note.eta_ok": "✅ {name}: запас часу в нормі",
        "note.eta_ok_tail": " (~{eta} до {limit}%)",

        "state.charging": "заряджається",
        "state.discharging": "розряджається",
        "state.idle": "очікування",
        "state.unknown": "режим невідомий",
        "role.voltage": "Напруга",
        "role.current": "Струм",
        "role.power": "Потужність",

        "dur.dash": "—",
        "dur.m": "{m} хв",
        "dur.hm": "{h} год {m:02d} хв",
        "dur.dh": "{d} дн {h} год",

        "demo.demo-garage": "Гараж — LiFePO4 100Ah",
        "demo.demo-home": "Дім — резервний АКБ 200Ah",
        "demo.demo-van": "Кемпер — 120Ah",
        "demo.demo-solar": "Солар-буфер 280Ah",
    },

    "en": {
        "err.unknown_device": "Unknown device",
        "err.auth_required": "Authorisation required",
        "err.generic": "Error: {msg}",
        "err.internal": "Internal error: {msg}",

        "admin.wrong_password": "Wrong password",
        "admin.need_creds": "Enter the Access ID and Access Secret",
        "admin.conn_error": "Connection error: {msg}",
        "admin.conn_ok": "Connected. Devices in the account: {n}",
        "admin.conn_token_only": "Token received, but the device list is unavailable: {msg}",
        "admin.save_creds_first": "Enter and save the Tuya credentials first",
        "admin.pw_too_short": "Password too short (4 characters minimum)",
        "admin.pw_wrong_current": "Wrong current password",

        "tg.need_token": "Enter the bot token",
        "tg.need_chat": "Enter the chat ID",
        "tg.no_token": "No bot token set",
        "tg.no_chat": "No chat ID set",
        "tg.net": "Network unavailable: {msg}",
        "tg.bad_response": "Malformed Telegram response (HTTP {code})",
        "tg.api_error": "Telegram error (HTTP {code})",
        "tg.test_text": "✅ Battery Monitor: connection check.\n"
                        "Battery charge notifications will arrive in this chat.",
        "tg.test_sent": "Message sent by bot @{name}",
        "tg.bot": "bot",
        "tg.no_chats": "No chats found. Send the bot any message (or add it to a group) "
                       "and try again.",
        "tg.chats_found": "Chats found: {n}",

        "note.demo": "🧪 (demo) ",
        "note.offline": "⚠️ {name}: device unreachable\n{msg}",
        "note.online": "✅ {name}: connection restored",
        "note.low_soc": "🪫 {name}: charge {soc}% — below the {limit}% threshold",
        "note.soc_ok": "🔋 {name}: charge recovered to {soc}%",
        "note.low_eta": "⏳ {name}: ~{eta} left to {limit}% (threshold {threshold} min)",
        "note.soc_line": "Charge {soc}%",
        "note.eta_ok": "✅ {name}: time margin back to normal",
        "note.eta_ok_tail": " (~{eta} to {limit}%)",

        "state.charging": "charging",
        "state.discharging": "discharging",
        "state.idle": "idle",
        "state.unknown": "mode unknown",
        "role.voltage": "Voltage",
        "role.current": "Current",
        "role.power": "Power",

        "dur.dash": "—",
        "dur.m": "{m} min",
        "dur.hm": "{h} h {m:02d} min",
        "dur.dh": "{d} d {h} h",

        "demo.demo-garage": "Garage — LiFePO4 100Ah",
        "demo.demo-home": "Home — backup pack 200Ah",
        "demo.demo-van": "Camper — 120Ah",
        "demo.demo-solar": "Solar buffer 280Ah",
    },
}


def normalize(value) -> str | None:
    """Код языка из настроек или заголовка: 'uk-UA' → 'uk', мусор → None."""
    code = str(value or "").strip().lower().replace("_", "-").split("-")[0]
    return code if code in LANGS else None


def t(lang: str | None, key: str, **kwargs) -> str:
    """Перевод по ключу; неизвестный язык или ключ откатывается на русский."""
    table = MESSAGES.get(normalize(lang) or LANG_DEFAULT, MESSAGES[LANG_DEFAULT])
    text = table.get(key) or MESSAGES[LANG_DEFAULT].get(key, key)
    return text.format(**kwargs) if kwargs else text
