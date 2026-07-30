"""Нормализация «сырых» точек данных Tuya в понятные метрики.

Устройства Tuya отдают числа как целые с масштабом (например, значение 1256 при
scale=2 означает 12.56 В). Единицы измерения и масштаб берём из спецификации
устройства, поэтому маппинг не привязан к конкретным кодам DP и работает даже
для незнакомых точек данных.
"""

import json

# Человекочитаемые названия и иконки по «роли» метрики.
ROLE_LABELS = {
    "voltage": ("Напряжение", "⚡"),
    "current": ("Ток", "🔀"),
    "power": ("Мощность", "💡"),
    "soc": ("Заряд", "🔋"),
    "capacity": ("Ёмкость", "🪫"),
    "energy": ("Энергия", "📊"),
    "temperature": ("Температура", "🌡️"),
    "time": ("Время", "⏱️"),
    "status": ("Состояние", "ℹ️"),
    "other": ("", "•"),
}

# Точечные подписи для часто встречающихся кодов DT20W / кулоновских счётчиков.
CODE_LABELS = {
    "cur_voltage": "Напряжение",
    "cur_current": "Ток",
    "cur_power": "Мощность",
    "battery_percentage": "Заряд батареи",
    "residual_electricity": "Остаточный заряд",
    "electric_quantity": "Остаточная ёмкость",
    "remain_capacity": "Остаточная ёмкость",
    "residual_capacity": "Остаточная ёмкость",
    "total_capacity": "Полная ёмкость",
    "design_capacity": "Проектная ёмкость",
    "temp_current": "Температура",
    "cumulative_charge": "Накоплено заряда",
    "cumulative_discharge": "Накоплено разряда",
    "remaining_time": "Оставшееся время",
    "charge_state": "Режим",
    "work_state": "Режим работы",
}


def _parse_spec(specifications):
    """code -> {type, unit, scale, min, max, range} из спецификации устройства."""
    spec_map = {}
    if not specifications:
        return spec_map
    for item in specifications.get("status", []) or []:
        code = item.get("code")
        values = {}
        raw = item.get("values")
        if raw:
            try:
                values = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                values = {}
        spec_map[code] = {
            "type": item.get("type"),
            "unit": (values.get("unit") or "").strip(),
            "scale": values.get("scale", 0) or 0,
            "min": values.get("min"),
            "max": values.get("max"),
            "range": values.get("range"),
        }
    return spec_map


def detect_role(code: str, unit: str) -> str:
    """Определяем роль метрики: сначала по единице измерения, потом по коду."""
    c = (code or "").lower()
    u = (unit or "").strip().lower()

    if u:
        if u in ("v", "mv", "kv"):
            return "voltage"
        if u in ("a", "ma"):
            return "current"
        if u in ("w", "kw", "mw"):
            return "power"
        if u == "%":
            return "soc"
        if u in ("ah", "mah"):
            return "capacity"
        if u in ("wh", "kwh", "w·h"):
            return "energy"
        if u in ("℃", "°c", "c", "℉", "°f"):
            return "temperature"
        if u in ("min", "h", "s", "sec", "hour", "day"):
            return "time"

    if "voltage" in c or "volt" in c:
        return "voltage"
    if "current" in c:
        return "current"
    if "power" in c:
        return "power"
    if any(k in c for k in ("soc", "percent", "battery_per", "residual_electricity")):
        return "soc"
    if any(k in c for k in ("capacity", "coulomb", "quantity")):
        return "capacity"
    if any(k in c for k in ("energy", "electric")):
        return "energy"
    if "temp" in c:
        return "temperature"
    if "time" in c or "remain" in c:
        return "time"
    if any(k in c for k in ("state", "status", "mode")):
        return "status"
    return "other"


def _cap_kind(code: str):
    """Для метрик-ёмкостей: это «остаточная» или «полная» ёмкость?"""
    c = (code or "").lower()
    if any(k in c for k in ("total", "design", "full", "rated")):
        return "total"
    if any(k in c for k in ("remain", "residual", "surplus")) or c == "electric_quantity":
        return "remaining"
    return None


def _scaled(raw, scale):
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)) and scale:
        return raw / (10 ** scale)
    return raw


def normalize(status, specifications):
    """Из сырого статуса и спецификации собираем структуру для фронтенда."""
    spec_map = _parse_spec(specifications)
    metrics = []

    for item in status or []:
        code = item.get("code")
        raw = item.get("value")
        spec = spec_map.get(code, {})
        unit = spec.get("unit") or ""
        scale = spec.get("scale") or 0
        role = detect_role(code, unit)

        value = _scaled(raw, scale)
        role_label, icon = ROLE_LABELS.get(role, ROLE_LABELS["other"])
        label = CODE_LABELS.get(code) or role_label or code

        metrics.append(
            {
                "code": code,
                "label": label,
                "icon": icon,
                "role": role,
                "value": value,
                "raw": raw,
                "unit": unit,
                "type": spec.get("type"),
                "min": spec.get("min"),
                "max": spec.get("max"),
                "cap_kind": _cap_kind(code) if role == "capacity" else None,
            }
        )

    # Ключевые метрики для «крупных плиток».
    primary = {}
    for role in ("voltage", "current", "power", "soc"):
        for m in metrics:
            if m["role"] == role:
                primary[role] = m
                break

    return {"metrics": metrics, "primary": primary, "state": _infer_state(metrics, primary)}


def _infer_state(metrics, primary):
    """Определяем режим: зарядка / разрядка / ожидание.

    Приоритет — явная точка данных состояния; иначе смотрим на знак тока/мощности.
    Отрицательный ток обычно означает разряд, положительный — заряд.
    """
    for m in metrics:
        if m["role"] == "status" and isinstance(m["value"], str):
            v = m["value"].lower()
            if "charg" in v and "dis" not in v:
                return "charging"
            if "dischar" in v:
                return "discharging"
            if "stand" in v or "idle" in v or "full" in v:
                return "idle"

    signal = primary.get("current") or primary.get("power")
    if signal and isinstance(signal["value"], (int, float)):
        v = signal["value"]
        if v > 0.02:
            return "charging"
        if v < -0.02:
            return "discharging"
        return "idle"

    return "unknown"


def _capacities(data):
    """Возвращаем (остаточная_Ah, полная_Ah), достраивая недостающее по SOC."""
    metrics = data.get("metrics", [])
    soc_m = data.get("primary", {}).get("soc")
    soc = soc_m["value"] if soc_m and isinstance(soc_m["value"], (int, float)) else None

    remain_ah = total_ah = None
    for m in metrics:
        if m["role"] != "capacity" or not isinstance(m["value"], (int, float)):
            continue
        if m.get("cap_kind") == "remaining":
            remain_ah = m["value"]
        elif m.get("cap_kind") == "total":
            total_ah = m["value"]

    if total_ah is None and remain_ah is not None and soc:
        total_ah = remain_ah / (soc / 100.0)
    if remain_ah is None and total_ah is not None and soc is not None:
        remain_ah = total_ah * soc / 100.0
    return remain_ah, total_ah


def estimate_time_to_pct(data, target_pct: int = 30):
    """Оценка времени (в минутах) до разряда батареи до target_pct.

    Кулоновский метод: (остаточная_Ah − target·полная_Ah) / ток_разряда.
    Возвращает {"minutes": float, "note": str} либо None, если оценить нельзя.
    Note:
      ok            — оценка посчитана;
      at_or_below   — заряд уже на уровне target или ниже;
      not_discharging — устройство не разряжается (заряд/ожидание);
      no_data       — недостаточно данных (нет ёмкости/тока).
    """
    primary = data.get("primary", {})
    soc_m = primary.get("soc")
    if not soc_m or not isinstance(soc_m["value"], (int, float)):
        return None
    soc = soc_m["value"]
    if soc <= target_pct:
        return {"minutes": 0.0, "note": "at_or_below"}

    remain_ah, total_ah = _capacities(data)
    if remain_ah is None or total_ah is None or total_ah <= 0:
        return {"minutes": None, "note": "no_data"}

    # Ток разряда (A). Берём знак тока; иначе оцениваем как мощность/напряжение.
    rate = None
    cur = primary.get("current")
    if cur and isinstance(cur["value"], (int, float)) and cur["value"] < -0.02:
        rate = abs(cur["value"])
    elif data.get("state") == "discharging":
        p, v = primary.get("power"), primary.get("voltage")
        if (p and v and isinstance(p["value"], (int, float)) and isinstance(v["value"], (int, float))
                and v["value"] > 0 and p["value"] > 0):
            rate = p["value"] / v["value"]

    if not rate or rate <= 0:
        return {"minutes": None, "note": "not_discharging"}

    above = remain_ah - (target_pct / 100.0) * total_ah
    if above <= 0:
        return {"minutes": 0.0, "note": "at_or_below"}

    hours = above / rate  # Ah / A = ч
    return {"minutes": hours * 60.0, "note": "ok"}
