"""FastAPI-приложение.

Публичная часть: список устройств, детальный дашборд, JSON API.
Админ-часть (/admin): интерактивная настройка Tuya, поиск устройств, параметры,
уведомления в Telegram. Актуальные настройки хранятся в store (DATA_DIR/settings.json).
"""

import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import demo, i18n, metrics, notifier
from .config import settings
from .store import store
from .tuya_client import TuyaError

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    watcher.start()
    try:
        yield
    finally:
        watcher.stop()


app = FastAPI(title="Battery Monitor", version="3.1.0", lifespan=lifespan)

# Общая пиксельная тема страниц: /static/pixel.css и /static/pixel.js,
# выбор оформления (Пиксель / Dracula) — /static/theme.js, гарнитуры — /static/fonts.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Кэш спецификаций по device_id.
_spec_cache: dict[str, dict] = {}
_SPEC_TTL = 3600


# ------------------------------------------------------------ Вспомогательное --
def req_lang(x_bm_lang: str | None = Header(default=None)) -> str:
    """Язык ответа: выбор браузера (заголовок от app/static/i18n.js), иначе общий."""
    return i18n.normalize(x_bm_lang) or store.language


def _default_device_id() -> str:
    devs = store.devices()
    return devs[0].id if devs else ""


def _require_device(device_id: str, lang: str | None = None) -> str:
    device_id = device_id or _default_device_id()
    if not device_id or device_id not in store.device_map():
        raise HTTPException(status_code=404, detail=i18n.t(lang, "err.unknown_device"))
    return device_id


def _get_specifications(device_id: str):
    """Спецификация DP: /v1.0 specifications + единицы/масштаб из Thing-модели (v2.0)."""
    if store.use_demo:
        return demo.demo_specifications(device_id)
    now = time.time()
    cached = _spec_cache.get(device_id)
    if cached is None or now - cached["ts"] > _SPEC_TTL:
        client = store.client()
        spec = client.get_specifications(device_id) or {}
        status_specs = list(spec.get("status") or [])
        # Дополняем современной Thing-моделью (кастомные DP: заряд, ёмкость и т.п.).
        try:
            status_specs += metrics.thing_model_to_spec(client.get_thing_model(device_id)).get("status", [])
        except Exception:  # noqa: BLE001 — best-effort, старый спек уже есть
            pass
        combined = {"status": status_specs, "category": spec.get("category")}
        cached = {"data": combined, "ts": now}
        _spec_cache[device_id] = cached
    return cached["data"]


def _fetch_normalized(device_id: str, lang: str | None = None) -> dict:
    if store.use_demo:
        status = demo.demo_status(device_id)
        spec = demo.demo_specifications(device_id)
    else:
        client = store.client()
        status = client.get_status(device_id)
        spec = _get_specifications(device_id)
        # Сливаем кастомные DP из Thing-модели (их часто нет в /v1.0 status).
        try:
            props = client.get_thing_properties(device_id)
            if props:
                status = metrics.merge_status(status, props)
        except Exception:  # noqa: BLE001 — best-effort, обычный статус уже получен
            pass

    data = metrics.normalize(status, spec)
    data["target_soc"] = store.target_soc
    data["eta"] = metrics.estimate_eta(data, data["target_soc"])
    data["id"] = device_id
    dev = store.device_map(lang).get(device_id)
    data["name"] = dev.name if dev else device_id
    data["online"] = True
    data["timestamp"] = int(time.time() * 1000)
    data["demo"] = store.use_demo
    return data


# Фоновый наблюдатель порогов для уведомлений (стартует в lifespan).
watcher = notifier.Watcher(store=store, fetch=_fetch_normalized)


def require_admin(authorization: str | None = Header(default=None),
                  lang: str = Depends(req_lang)) -> bool:
    """Гейт для админ-эндпоинтов. Если пароль не задан — доступ открыт (с предупреждением в UI)."""
    if not store.auth_enabled:
        return True
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not store.verify_token(token):
        raise HTTPException(status_code=401, detail=i18n.t(lang, "err.auth_required"))
    return True


# --------------------------------------------------------------------- Страницы --
@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/device/{device_id}")
def device_page(device_id: str, lang: str = Depends(req_lang)):
    _require_device(device_id, lang)
    return FileResponse(STATIC_DIR / "device.html")


@app.get("/admin")
def admin_page():
    return FileResponse(STATIC_DIR / "admin.html")


# ---------------------------------------------------------------- Публичный API --
@app.get("/api/config")
def api_config(lang: str = Depends(req_lang)):
    return {
        "poll_interval": store.poll_interval,
        "demo_mode": store.use_demo,
        "endpoint": store.endpoint,
        "theme": store.theme,
        "language": store.language,
        "target_soc": store.target_soc,
        # Ссылка на исходники для футера (AGPL-3.0 §13), задаётся SOURCE_URL.
        "source_url": settings.source_url,
        "devices": [{"id": d.id, "name": d.name} for d in store.devices(lang)],
    }


@app.get("/api/devices")
def api_devices(lang: str = Depends(req_lang)):
    out = []
    for dev in store.devices(lang):
        item = {"id": dev.id, "name": dev.name, "online": True, "error": None}
        try:
            data = _fetch_normalized(dev.id, lang)
            primary = data["primary"]
            soc, volt, cur = primary.get("soc"), primary.get("voltage"), primary.get("current")
            eta = data.get("eta") or {}
            item.update(
                soc=soc["value"] if soc else None,
                state=data["state"],
                eta_minutes=eta.get("minutes"),
                eta_note=eta.get("note"),
                eta_mode=eta.get("mode"),
                voltage=volt["value"] if volt else None,
                voltage_unit=volt["unit"] if volt else "",
                current=cur["value"] if cur else None,
                current_unit=cur["unit"] if cur else "",
            )
        except TuyaError as exc:
            item.update(online=False, error=str(exc))
        except Exception as exc:  # noqa: BLE001
            item.update(online=False, error=i18n.t(lang, "err.generic", msg=exc))
        out.append(item)
    return {"devices": out, "timestamp": int(time.time() * 1000), "demo": store.use_demo,
            "target_soc": store.target_soc}


@app.get("/api/status")
def api_status(device_id: str = Query(default=""), lang: str = Depends(req_lang)):
    did = _require_device(device_id, lang)
    try:
        return JSONResponse(_fetch_normalized(did, lang))
    except TuyaError as exc:
        return JSONResponse({"error": str(exc), "online": False, "id": did,
                             "timestamp": int(time.time() * 1000)}, status_code=502)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"error": i18n.t(lang, "err.internal", msg=exc), "online": False,
                             "id": did, "timestamp": int(time.time() * 1000)}, status_code=500)


@app.get("/api/raw")
def api_raw(device_id: str = Query(default=""), lang: str = Depends(req_lang)):
    """Все источники DP для диагностики: /v1.0 status и specifications,
    а также Thing-модель (v2.0), где обычно и лежат заряд/ёмкость."""
    did = _require_device(device_id, lang)
    if store.use_demo:
        return {"status": demo.demo_status(did),
                "specifications": demo.demo_specifications(did)}

    client = store.client()

    def _safe(fn):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — показываем ошибку по каждому источнику
            return {"error": str(exc)}

    return {
        "status_v1": _safe(lambda: client.get_status(did)),
        "specifications_v1": _safe(lambda: client.get_specifications(did)),
        "thing_properties_v2": _safe(lambda: client.get_thing_properties(did)),
        "thing_model_v2": _safe(lambda: client.get_thing_model(did)),
        "device": _safe(lambda: client.get_device(did)),
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok", "devices": len(store.devices())}


# ------------------------------------------------------------------- Админ API --
@app.post("/api/admin/login")
def admin_login(payload: dict = Body(...), lang: str = Depends(req_lang)):
    if not store.auth_enabled:
        return {"ok": True, "token": "", "auth_enabled": False}
    if store.verify_password(str(payload.get("password", ""))):
        return {"ok": True, "token": store.make_token(), "auth_enabled": True}
    raise HTTPException(status_code=401, detail=i18n.t(lang, "admin.wrong_password"))


@app.get("/api/admin/settings")
def admin_get_settings(_: bool = Depends(require_admin)):
    return store.public_settings()


@app.post("/api/admin/settings")
def admin_save_settings(payload: dict = Body(...), _: bool = Depends(require_admin)):
    patch: dict = {}
    for key in ("access_id", "endpoint", "demo_mode", "poll_interval", "devices", "telegram",
                "theme", "language", "target_soc"):
        if key in payload:
            patch[key] = payload[key]
    if payload.get("access_key"):
        patch["access_key"] = str(payload["access_key"]).strip()

    if "devices" in patch:
        clean = []
        for d in patch["devices"] or []:
            did = str(d.get("id", "")).strip()
            if not did:
                continue
            clean.append({"id": did, "name": str(d.get("name") or did).strip()})
        patch["devices"] = clean
    if "poll_interval" in patch:
        try:
            patch["poll_interval"] = max(3, int(patch["poll_interval"]))
        except (TypeError, ValueError):
            patch.pop("poll_interval")
    if "demo_mode" in patch:
        patch["demo_mode"] = bool(patch["demo_mode"])

    store.update(patch)
    _spec_cache.clear()
    watcher.wake()  # применить новые пороги/интервал сразу
    return {"ok": True, "settings": store.public_settings()}


@app.post("/api/admin/test-connection")
def admin_test_connection(payload: dict = Body(default={}), _: bool = Depends(require_admin),
                          lang: str = Depends(req_lang)):
    access_id = str(payload.get("access_id") or store.access_id).strip()
    access_key = str(payload.get("access_key") or "").strip() or store.access_key
    endpoint = str(payload.get("endpoint") or store.endpoint).strip()
    if not access_id or not access_key:
        return {"ok": False, "message": i18n.t(lang, "admin.need_creds")}
    try:
        client = store.build_client(access_id, access_key, endpoint)
        client._get_token(force=True)
    except TuyaError as exc:
        return {"ok": False, "message": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "message": i18n.t(lang, "admin.conn_error", msg=exc)}
    try:
        devs = client.get_associated_devices()
        return {"ok": True, "message": i18n.t(lang, "admin.conn_ok", n=len(devs)),
                "device_count": len(devs)}
    except TuyaError as exc:
        return {"ok": True, "message": i18n.t(lang, "admin.conn_token_only", msg=exc)}


@app.get("/api/admin/discover")
def admin_discover(_: bool = Depends(require_admin), lang: str = Depends(req_lang)):
    if not store.has_credentials():
        raise HTTPException(status_code=400, detail=i18n.t(lang, "admin.save_creds_first"))
    client = store.build_client(store.access_id, store.access_key, store.endpoint)
    try:
        devs = client.get_associated_devices()
    except TuyaError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"devices": [
        {"id": d.get("id"), "name": d.get("name") or d.get("id"),
         "category": d.get("category"), "product_name": d.get("product_name"),
         "online": d.get("online")}
        for d in devs]}


@app.post("/api/admin/password")
def admin_password(payload: dict = Body(...), _: bool = Depends(require_admin),
                   lang: str = Depends(req_lang)):
    new = str(payload.get("new", "")).strip()
    if len(new) < 4:
        raise HTTPException(status_code=400, detail=i18n.t(lang, "admin.pw_too_short"))
    if store.auth_enabled and not store.verify_password(str(payload.get("current", ""))):
        raise HTTPException(status_code=403, detail=i18n.t(lang, "admin.pw_wrong_current"))
    store.set_password(new)
    return {"ok": True, "token": store.make_token()}


# ------------------------------------------------------------ Уведомления TG --
def _tg_creds(payload: dict) -> tuple[str, str]:
    """Реквизиты для разовой операции: из формы, иначе сохранённые."""
    cfg = store.telegram
    token = str(payload.get("bot_token") or "").strip() or cfg["bot_token"]
    chat_id = str(payload.get("chat_id") or "").strip() or cfg["chat_id"]
    return token, chat_id


@app.post("/api/admin/telegram/test")
def admin_telegram_test(payload: dict = Body(default={}), _: bool = Depends(require_admin),
                        lang: str = Depends(req_lang)):
    """Отправляет тестовое сообщение — можно проверить ещё до сохранения настроек.

    Само сообщение уходит на общем языке панели: так же, как настоящие уведомления.
    """
    token, chat_id = _tg_creds(payload)
    if not token:
        return {"ok": False, "message": i18n.t(lang, "tg.need_token")}
    if not chat_id:
        return {"ok": False, "message": i18n.t(lang, "tg.need_chat")}
    try:
        bot = notifier.get_me(token, lang=lang)
        notifier.send_message(token, chat_id, i18n.t(store.language, "tg.test_text"), lang=lang)
    except notifier.TelegramError as exc:
        return {"ok": False, "message": str(exc)}
    name = bot.get("username") or bot.get("first_name") or i18n.t(lang, "tg.bot")
    return {"ok": True, "message": i18n.t(lang, "tg.test_sent", name=name)}


@app.post("/api/admin/telegram/chats")
def admin_telegram_chats(payload: dict = Body(default={}), _: bool = Depends(require_admin),
                         lang: str = Depends(req_lang)):
    """Подсказка по chat_id: чаты, из которых боту недавно писали."""
    token, _chat = _tg_creds(payload)
    if not token:
        return {"ok": False, "message": i18n.t(lang, "tg.need_token"), "chats": []}
    try:
        chats = notifier.discover_chats(token, lang=lang)
    except notifier.TelegramError as exc:
        return {"ok": False, "message": str(exc), "chats": []}
    if not chats:
        return {"ok": False, "chats": [], "message": i18n.t(lang, "tg.no_chats")}
    return {"ok": True, "chats": chats, "message": i18n.t(lang, "tg.chats_found", n=len(chats))}


@app.get("/api/admin/telegram/log")
def admin_telegram_log(_: bool = Depends(require_admin)):
    """Последние отправленные (и неудавшиеся) уведомления — для диагностики."""
    return {"events": watcher.recent(), "running": watcher.is_alive()}
