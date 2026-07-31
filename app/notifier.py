"""Уведомления в Telegram.

Фоновый поток периодически опрашивает устройства и сравнивает показания с
порогами из админ-панели: уровень заряда (SOC) и оценка времени до достижения
этого уровня. При пересечении порога уходит сообщение в чат Telegram.

Антиспам: повторное сообщение по тому же поводу не отправляется, пока
показатель не вернётся в норму (либо пока не истечёт интервал повтора, если он
задан в настройках). При возврате в норму можно получить сообщение «отбой».

Язык сообщений — общий язык панели (settings.json), браузера у них нет.
"""

import threading
import time
from collections import deque

import requests

from . import i18n, metrics

API_BASE = "https://api.telegram.org"
TIMEOUT = 15

SOC_HYSTERESIS = 2.0    # % сверх порога — чтобы «отбой» не дёргался у границы
ETA_HYSTERESIS = 1.25   # во сколько раз ETA должна превысить порог для «отбоя»
MIN_INTERVAL = 15       # с — нижняя граница интервала проверки


class TelegramError(Exception):
    """Ошибка обращения к Bot API (сеть, токен, права, неверный chat_id)."""


# ------------------------------------------------------------------ Bot API --
def _call(token: str, method: str, payload: dict | None = None, lang: str | None = None):
    token = (token or "").strip()
    if not token:
        raise TelegramError(i18n.t(lang, "tg.no_token"))
    try:
        resp = requests.post(f"{API_BASE}/bot{token}/{method}", json=payload or {}, timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise TelegramError(i18n.t(lang, "tg.net", msg=exc)) from exc
    try:
        data = resp.json()
    except ValueError as exc:
        raise TelegramError(i18n.t(lang, "tg.bad_response", code=resp.status_code)) from exc
    if not data.get("ok"):
        raise TelegramError(data.get("description")
                            or i18n.t(lang, "tg.api_error", code=resp.status_code))
    return data.get("result")


def get_me(token: str, lang: str | None = None) -> dict:
    return _call(token, "getMe", lang=lang) or {}


def send_message(token: str, chat_id, text: str, lang: str | None = None):
    chat_id = str(chat_id or "").strip()
    if not chat_id:
        raise TelegramError(i18n.t(lang, "tg.no_chat"))
    return _call(token, "sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }, lang=lang)


def discover_chats(token: str, lang: str | None = None) -> list[dict]:
    """Чаты из недавних апдейтов бота — чтобы подставить chat_id в админке.

    Работает, если боту недавно писали и апдейты ещё не забраны вебхуком.
    """
    updates = _call(token, "getUpdates", {"limit": 100, "timeout": 0}, lang=lang) or []
    chats: dict = {}
    for upd in updates:
        for key in ("message", "edited_message", "channel_post", "my_chat_member"):
            chat = (upd.get(key) or {}).get("chat")
            if not chat or chat.get("id") is None:
                continue
            title = (chat.get("title")
                     or " ".join(x for x in (chat.get("first_name"), chat.get("last_name")) if x)
                     or chat.get("username") or str(chat["id"]))
            chats[chat["id"]] = {"id": chat["id"], "title": title, "type": chat.get("type")}
    return list(chats.values())


# ------------------------------------------------------------ Форматирование --
def fmt_minutes(minutes, lang: str | None = None) -> str:
    if minutes is None:
        return i18n.t(lang, "dur.dash")
    total = int(round(minutes))
    if total < 60:
        return i18n.t(lang, "dur.m", m=total)
    hours, mins = divmod(total, 60)
    if hours >= 24:
        days, hours = divmod(hours, 24)
        return i18n.t(lang, "dur.dh", d=days, h=hours)
    return i18n.t(lang, "dur.hm", h=hours, m=mins)


def _num(value) -> str:
    if not isinstance(value, (int, float)):
        return str(value)
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text if text not in ("", "-") else "0"


def _details(data: dict, lang: str | None = None) -> str:
    """Строка с ключевыми показаниями: напряжение · ток · мощность."""
    primary = data.get("primary") or {}
    parts = []
    for role in ("voltage", "current", "power"):
        m = primary.get(role)
        if m and isinstance(m.get("value"), (int, float)):
            label = i18n.t(lang, f"role.{role}")
            parts.append(f"{label}: {_num(m['value'])} {m.get('unit') or ''}".strip())
    return " · ".join(parts)


def _state_label(state, lang: str | None = None) -> str:
    key = f"state.{state}"
    text = i18n.t(lang, key)
    return "" if text == key else text


# ---------------------------------------------------------------- Наблюдатель --
class Watcher(threading.Thread):
    """Фоновый цикл проверки порогов.

    store — хранилище настроек (нужны .telegram и .devices()),
    fetch — функция device_id -> нормализованные данные (как в /api/status).
    """

    def __init__(self, store, fetch):
        super().__init__(name="tg-watcher", daemon=True)
        self._store = store
        self._fetch = fetch
        self._wake = threading.Event()
        self._stopping = threading.Event()
        # (device_id, kind) -> {"active": bool, "last_sent": float}
        self._states: dict[tuple[str, str], dict] = {}
        self.log: deque = deque(maxlen=30)

    # --- управление потоком ---
    def wake(self):
        """Применить новые настройки, не дожидаясь конца паузы."""
        self._wake.set()

    def stop(self):
        self._stopping.set()
        self._wake.set()

    def run(self):
        self._wake.wait(5)  # дать приложению подняться
        while not self._stopping.is_set():
            interval = 60
            try:
                cfg = self._store.telegram
                interval = max(MIN_INTERVAL, int(cfg.get("check_interval") or 60))
                if cfg.get("enabled") and cfg.get("bot_token") and cfg.get("chat_id"):
                    self._cycle(cfg)
                else:
                    self._states.clear()
            except Exception as exc:  # noqa: BLE001 — цикл не должен умирать
                print(f"[notifier] сбой цикла проверки: {exc}", flush=True)
            self._wake.clear()
            self._wake.wait(interval)

    # --- проверка порогов ---
    def _cycle(self, cfg: dict):
        soc_limit = float(cfg.get("soc_threshold") or 0)
        eta_limit = float(cfg.get("eta_threshold") or 0)
        lang = getattr(self._store, "language", i18n.LANG_DEFAULT)
        known: set[str] = set()

        for dev in self._store.devices():
            known.add(dev.id)
            online_text = i18n.t(lang, "note.online", name=dev.name)
            try:
                data = self._fetch(dev.id)
            except Exception as exc:  # noqa: BLE001 — устройство недоступно
                self._rule(cfg, dev.id, "offline", bool(cfg.get("notify_offline")), True,
                           i18n.t(lang, "note.offline", name=dev.name, msg=exc), online_text)
                # Пока данных нет — пороги не оцениваем, состояния не трогаем.
                continue

            self._rule(cfg, dev.id, "offline", bool(cfg.get("notify_offline")), False,
                       "", online_text)

            prefix = i18n.t(lang, "note.demo") if data.get("demo") else ""
            soc_m = (data.get("primary") or {}).get("soc")
            soc = soc_m.get("value") if soc_m and isinstance(soc_m.get("value"), (int, float)) else None
            details = _details(data, lang)
            state = _state_label(data.get("state"), lang)

            # --- порог заряда ---
            low_soc = soc is not None and soc <= soc_limit
            if soc is not None:
                # Гистерезис: «отбой» только когда заряд заметно выше порога.
                st = self._states.get((dev.id, "soc"))
                if st and st.get("active") and soc < soc_limit + SOC_HYSTERESIS:
                    low_soc = True
            self._rule(
                cfg, dev.id, "soc", bool(cfg.get("notify_low_soc")), low_soc,
                prefix + i18n.t(lang, "note.low_soc", name=dev.name,
                                soc=_num(soc), limit=_num(soc_limit))
                + (f"\n{state}" if state else "") + (f"\n{details}" if details else ""),
                prefix + i18n.t(lang, "note.soc_ok", name=dev.name, soc=_num(soc)),
            )

            # --- время до достижения порога ---
            eta = metrics.estimate_time_to_pct(data, soc_limit) or {}
            minutes = eta.get("minutes")
            eta_ok = eta.get("note") == "ok" and isinstance(minutes, (int, float))
            if soc is not None and soc <= soc_limit:
                # Заряд уже ниже порога — об этом сообщает правило «soc», не дублируем.
                self._states.pop((dev.id, "eta"), None)
                continue

            low_eta = eta_ok and minutes <= eta_limit
            if eta_ok and not low_eta:
                st = self._states.get((dev.id, "eta"))
                if st and st.get("active") and minutes <= eta_limit * ETA_HYSTERESIS:
                    low_eta = True
            self._rule(
                cfg, dev.id, "eta", bool(cfg.get("notify_low_eta")), low_eta,
                prefix + i18n.t(lang, "note.low_eta", name=dev.name, limit=_num(soc_limit),
                                eta=fmt_minutes(minutes, lang), threshold=_num(eta_limit))
                + ("\n" + i18n.t(lang, "note.soc_line", soc=_num(soc)) if soc is not None else "")
                + (f" · {details}" if details else ""),
                prefix + i18n.t(lang, "note.eta_ok", name=dev.name)
                + (i18n.t(lang, "note.eta_ok_tail", eta=fmt_minutes(minutes, lang),
                          limit=_num(soc_limit)) if eta_ok else ""),
            )

        # Забываем состояния устройств, которых больше нет в списке.
        for key in [k for k in self._states if k[0] not in known]:
            self._states.pop(key, None)

    def _rule(self, cfg: dict, dev_id: str, kind: str, enabled: bool, breached: bool,
              alert_text: str, recovery_text: str):
        key = (dev_id, kind)
        if not enabled:
            self._states.pop(key, None)
            return

        st = self._states.setdefault(key, {"active": False, "last_sent": 0.0})
        now = time.time()

        if breached:
            repeat = int(cfg.get("repeat_minutes") or 0)
            due = st["active"] and repeat > 0 and now - st["last_sent"] >= repeat * 60
            if not st["active"] or due:
                # Если отправить не удалось — состояние не «взводим», попробуем ещё раз.
                if self._send(cfg, alert_text):
                    st["active"] = True
                    st["last_sent"] = now
        elif st["active"]:
            st["active"] = False
            st["last_sent"] = 0.0
            if cfg.get("notify_recovery") and recovery_text:
                self._send(cfg, recovery_text)

    # --- отправка + журнал ---
    def _send(self, cfg: dict, text: str) -> bool:
        lang = getattr(self._store, "language", i18n.LANG_DEFAULT)
        try:
            send_message(cfg.get("bot_token", ""), cfg.get("chat_id", ""), text, lang=lang)
        except TelegramError as exc:
            self._note(text, False, str(exc))
            print(f"[notifier] не отправлено: {exc}", flush=True)
            return False
        self._note(text, True, "")
        return True

    def _note(self, text: str, ok: bool, error: str):
        self.log.appendleft({"ts": int(time.time() * 1000), "text": text, "ok": ok, "error": error})

    def recent(self) -> list[dict]:
        return list(self.log)
