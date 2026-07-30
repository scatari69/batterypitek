"""FastAPI-приложение.

Публичная часть: список устройств, детальный дашборд, JSON API.
Админ-часть (/admin): интерактивная настройка Tuya, поиск устройств, параметры.
Актуальные настройки хранятся в store (DATA_DIR/settings.json).
"""

import time
from pathlib import Path

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from . import demo, metrics
from .store import store
from .tuya_client import TuyaError

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Battery Monitor", version="3.0.0")

# Кэш спецификаций по device_id.
_spec_cache: dict[str, dict] = {}
_SPEC_TTL = 3600


# ------------------------------------------------------------ Вспомогательное --
def _default_device_id() -> str:
    devs = store.devices()
    return devs[0].id if devs else ""


def _require_device(device_id: str) -> str:
    device_id = device_id or _default_device_id()
    if not device_id or device_id not in store.device_map():
        raise HTTPException(status_code=404, detail="Неизвестное устройство")
    return device_id


def _get_specifications(device_id: str):
    if store.use_demo:
        return demo.demo_specifications(device_id)
    now = time.time()
    cached = _spec_cache.get(device_id)
    if cached is None or now - cached["ts"] > _SPEC_TTL:
        cached = {"data": store.client().get_specifications(device_id), "ts": now}
        _spec_cache[device_id] = cached
    return cached["data"]


def _fetch_normalized(device_id: str) -> dict:
    if store.use_demo:
        status = demo.demo_status(device_id)
        spec = demo.demo_specifications(device_id)
    else:
        status = store.client().get_status(device_id)
        spec = _get_specifications(device_id)

    data = metrics.normalize(status, spec)
    data["eta_30"] = metrics.estimate_time_to_pct(data, 30)
    data["id"] = device_id
    dev = store.device_map().get(device_id)
    data["name"] = dev.name if dev else device_id
    data["online"] = True
    data["timestamp"] = int(time.time() * 1000)
    data["demo"] = store.use_demo
    return data


def require_admin(authorization: str | None = Header(default=None)) -> bool:
    """Гейт для админ-эндпоинтов. Если пароль не задан — доступ открыт (с предупреждением в UI)."""
    if not store.auth_enabled:
        return True
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not store.verify_token(token):
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    return True


# --------------------------------------------------------------------- Страницы --
@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/device/{device_id}")
def device_page(device_id: str):
    _require_device(device_id)
    return FileResponse(STATIC_DIR / "device.html")


@app.get("/admin")
def admin_page():
    return FileResponse(STATIC_DIR / "admin.html")


# ---------------------------------------------------------------- Публичный API --
@app.get("/api/config")
def api_config():
    return {
        "poll_interval": store.poll_interval,
        "demo_mode": store.use_demo,
        "endpoint": store.endpoint,
        "devices": [{"id": d.id, "name": d.name} for d in store.devices()],
    }


@app.get("/api/devices")
def api_devices():
    out = []
    for dev in store.devices():
        item = {"id": dev.id, "name": dev.name, "online": True, "error": None}
        try:
            data = _fetch_normalized(dev.id)
            primary = data["primary"]
            soc, volt, cur = primary.get("soc"), primary.get("voltage"), primary.get("current")
            eta = data.get("eta_30") or {}
            item.update(
                soc=soc["value"] if soc else None,
                state=data["state"],
                eta_minutes=eta.get("minutes"),
                eta_note=eta.get("note"),
                voltage=volt["value"] if volt else None,
                voltage_unit=volt["unit"] if volt else "",
                current=cur["value"] if cur else None,
                current_unit=cur["unit"] if cur else "",
            )
        except TuyaError as exc:
            item.update(online=False, error=str(exc))
        except Exception as exc:  # noqa: BLE001
            item.update(online=False, error=f"Ошибка: {exc}")
        out.append(item)
    return {"devices": out, "timestamp": int(time.time() * 1000), "demo": store.use_demo}


@app.get("/api/status")
def api_status(device_id: str = Query(default="")):
    did = _require_device(device_id)
    try:
        return JSONResponse(_fetch_normalized(did))
    except TuyaError as exc:
        return JSONResponse({"error": str(exc), "online": False, "id": did,
                             "timestamp": int(time.time() * 1000)}, status_code=502)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"error": f"Внутренняя ошибка: {exc}", "online": False, "id": did,
                             "timestamp": int(time.time() * 1000)}, status_code=500)


@app.get("/api/raw")
def api_raw(device_id: str = Query(default="")):
    did = _require_device(device_id)
    try:
        if store.use_demo:
            return {"status": demo.demo_status(did),
                    "specifications": demo.demo_specifications(did)}
        client = store.client()
        return {"status": client.get_status(did),
                "specifications": _get_specifications(did),
                "device": client.get_device(did)}
    except TuyaError as exc:
        return JSONResponse({"error": str(exc)}, status_code=502)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "devices": len(store.devices())}


# ------------------------------------------------------------------- Админ API --
@app.post("/api/admin/login")
def admin_login(payload: dict = Body(...)):
    if not store.auth_enabled:
        return {"ok": True, "token": "", "auth_enabled": False}
    if store.verify_password(str(payload.get("password", ""))):
        return {"ok": True, "token": store.make_token(), "auth_enabled": True}
    raise HTTPException(status_code=401, detail="Неверный пароль")


@app.get("/api/admin/settings")
def admin_get_settings(_: bool = Depends(require_admin)):
    return store.public_settings()


@app.post("/api/admin/settings")
def admin_save_settings(payload: dict = Body(...), _: bool = Depends(require_admin)):
    patch: dict = {}
    for key in ("access_id", "endpoint", "demo_mode", "poll_interval", "devices"):
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
    return {"ok": True, "settings": store.public_settings()}


@app.post("/api/admin/test-connection")
def admin_test_connection(payload: dict = Body(default={}), _: bool = Depends(require_admin)):
    access_id = str(payload.get("access_id") or store.access_id).strip()
    access_key = str(payload.get("access_key") or "").strip() or store.access_key
    endpoint = str(payload.get("endpoint") or store.endpoint).strip()
    if not access_id or not access_key:
        return {"ok": False, "message": "Укажите Access ID и Access Secret"}
    try:
        client = store.build_client(access_id, access_key, endpoint)
        client._get_token(force=True)
    except TuyaError as exc:
        return {"ok": False, "message": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "message": f"Ошибка соединения: {exc}"}
    try:
        devs = client.get_associated_devices()
        return {"ok": True, "message": f"Подключение успешно. Устройств в аккаунте: {len(devs)}",
                "device_count": len(devs)}
    except TuyaError as exc:
        return {"ok": True, "message": f"Токен получен, но список устройств недоступен: {exc}"}


@app.get("/api/admin/discover")
def admin_discover(_: bool = Depends(require_admin)):
    if not store.has_credentials():
        raise HTTPException(status_code=400, detail="Сначала укажите и сохраните реквизиты Tuya")
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
def admin_password(payload: dict = Body(...), _: bool = Depends(require_admin)):
    new = str(payload.get("new", "")).strip()
    if len(new) < 4:
        raise HTTPException(status_code=400, detail="Пароль слишком короткий (минимум 4 символа)")
    if store.auth_enabled and not store.verify_password(str(payload.get("current", ""))):
        raise HTTPException(status_code=403, detail="Неверный текущий пароль")
    store.set_password(new)
    return {"ok": True, "token": store.make_token()}
