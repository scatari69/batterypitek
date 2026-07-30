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

# Реестр известных кодов DP: code -> (подпись, группа, иконка).
# Группы: live — живые показания; counter — счётчики/накопление;
# protection — пороги защит; config — настройки; control — управление/состояние.
CODE_META = {
    # --- живые показания ---
    "cur_voltage": ("Напряжение", "live", "⚡"),
    "cur_current": ("Ток", "live", "🔀"),
    "cur_power": ("Мощность", "live", "💡"),
    "battery_percentage": ("Заряд батареи", "live", "🔋"),
    "residual_electricity": ("Остаточный заряд", "live", "🔋"),
    "electric_quantity": ("Остаточная ёмкость", "live", "🔋"),
    "cap": ("Остаточная ёмкость", "live", "🔋"),
    "remain_capacity": ("Остаточная ёмкость", "live", "🔋"),
    "residual_capacity": ("Остаточная ёмкость", "live", "🔋"),
    "ntc_temp": ("Температура (датчик)", "live", "🌡️"),
    "cpu_temp": ("Температура платы", "live", "🌡️"),
    "temp_current": ("Температура", "live", "🌡️"),
    "resistance": ("Внутр. сопротивление", "live", "🧭"),
    # --- счётчики / накопление ---
    "charging_capacity": ("Заряжено", "counter", "🔼"),
    "discharge_capacity": ("Разряжено", "counter", "🔽"),
    "accumulated_capacity": ("Накоплено (ёмкость)", "counter", "🧮"),
    "cumulative_charge": ("Накоплено заряда", "counter", "🔼"),
    "cumulative_discharge": ("Накоплено разряда", "counter", "🔽"),
    "accumulated_electricity": ("Накоплено энергии", "counter", "📊"),
    "ele": ("Энергия", "counter", "📊"),
    # --- пороги защит ---
    "ovp": ("Защита: перенапряжение", "protection", "🛡️"),
    "lvp": ("Защита: низкое напряжение", "protection", "🛡️"),
    "otp": ("Защита: перегрев", "protection", "🛡️"),
    "opp": ("Защита: превышение мощности", "protection", "🛡️"),
    "discharge_current": ("Защита: ток разряда", "protection", "🛡️"),
    "discharge_power": ("Защита: мощность разряда", "protection", "🛡️"),
    "mini_current": ("Мин. ток (отсечка)", "protection", "🛡️"),
    # --- настройки ---
    "percent_100_bat_voltage": ("Напряжение 100% заряда", "config", "⚙️"),
    "percent_0_bat_voltage": ("Напряжение 0% заряда", "config", "⚙️"),
    "capacity_mode": ("Режим расчёта ёмкости", "config", "⚙️"),
    "diverter_size": ("Шунт (номинал)", "config", "⚙️"),
    "reporting_interval": ("Интервал отчётов", "config", "⚙️"),
    "standby_value": ("Порог ожидания", "config", "⚙️"),
    "work_value": ("Рабочий порог", "config", "⚙️"),
    "standby_time": ("Время до ожидания", "config", "⚙️"),
    "language": ("Язык", "config", "⚙️"),
    "menu": ("Экран / меню", "config", "⚙️"),
    # --- управление / состояние ---
    "relay_switch": ("Реле (нагрузка)", "control", "🔌"),
    "warning": ("Предупреждение", "control", "⚠️"),
    "current_zero": ("Обнулить ток", "control", "🎚️"),
    "real_time_swith_1s_60s": ("Отчёты в реальном времени", "control", "🎚️"),
    "data_reset": ("Сброс данных", "control", "🎚️"),
    "wifi_reset": ("Сброс Wi-Fi", "control", "🎚️"),
    "factor_reset": ("Заводской сброс", "control", "🎚️"),
    "charge_state": ("Режим", "live", "ℹ️"),
    "work_state": ("Режим работы", "live", "ℹ️"),
}

# Порядок и заголовки групп (для фронтенда).
GROUP_ORDER = ["counter", "protection", "config", "control", "other"]
GROUP_TITLES = {
    "counter": "Счётчики и накопление",
    "protection": "Защиты и пороги",
    "config": "Настройки устройства",
    "control": "Управление и состояние",
    "other": "Прочее",
}

# Предпочтительные коды для «крупных плиток» (чтобы порог ovp не попал в напряжение).
PRIMARY_CODES = {
    "voltage": ["cur_voltage"],
    "current": ["cur_current"],
    "power": ["cur_power"],
    "soc": ["battery_percentage", "residual_electricity", "electric_quantity"],
}


def _default_group(role: str) -> str:
    if role in ("voltage", "current", "power", "soc", "temperature"):
        return "live"
    if role in ("capacity", "energy"):
        return "counter"
    return "other"


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


def thing_model_to_spec(model):
    """Конвертирует «Thing»-модель (v2.0) в формат specifications (как у /v1.0),
    чтобы normalize() мог взять из неё единицы и масштаб кастомных DP."""
    status = []
    if not model:
        return {"status": status}
    for service in model.get("services", []) or []:
        for prop in service.get("properties", []) or []:
            ts = prop.get("typeSpec") or {}
            values = {k: ts[k] for k in ("unit", "scale", "min", "max", "step", "range") if k in ts}
            status.append({
                "code": prop.get("code"),
                "type": ts.get("type"),
                "values": json.dumps(values, ensure_ascii=False),
            })
    return {"status": status}


def merge_status(base_status, thing_properties):
    """Объединяет точки данных из /v1.0 status и Thing-свойств (последние дополняют)."""
    by_code = {}
    for item in base_status or []:
        by_code[item.get("code")] = item.get("value")
    for prop in thing_properties or []:
        by_code[prop.get("code")] = prop.get("value")
    return [{"code": code, "value": value} for code, value in by_code.items()]


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
    """Для метрик-ёмкостей: это «остаточная» или «полная» ёмкость (для расчёта ETA)?

    Счётчики (charging/discharge/accumulated) — не остаток и не полная, вернём None,
    чтобы они не участвовали в оценке времени до разряда.
    """
    c = (code or "").lower()
    if any(k in c for k in ("charging", "discharge", "accumulat", "cumulative")):
        return None
    if c in ("cap", "electric_quantity"):
        return "remaining"
    if any(k in c for k in ("total", "design", "full", "rated")):
        return "total"
    if any(k in c for k in ("remain", "residual", "surplus")):
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
        meta = CODE_META.get(code)
        if meta:
            label, group, icon = meta
        else:
            role_label, icon = ROLE_LABELS.get(role, ROLE_LABELS["other"])
            label = role_label or code
            group = _default_group(role)

        metrics.append(
            {
                "code": code,
                "label": label,
                "icon": icon,
                "role": role,
                "group": group,
                "value": value,
                "raw": raw,
                "unit": unit,
                "type": spec.get("type"),
                "min": spec.get("min"),
                "max": spec.get("max"),
                "cap_kind": _cap_kind(code) if role == "capacity" else None,
            }
        )

    primary = _pick_primary(metrics)
    return {"metrics": metrics, "primary": primary,
            "state": _infer_state(metrics, primary)}


def _pick_primary(metrics):
    """Ключевые метрики для крупных плиток: предпочитаем известные «живые» коды,
    чтобы пороги защит (ovp/opp/…) не попадали в основные показатели."""
    primary = {}
    for role in ("voltage", "current", "power", "soc"):
        chosen = None
        for code in PRIMARY_CODES.get(role, []):
            chosen = next((m for m in metrics if m["code"] == code), None)
            if chosen:
                break
        if not chosen:
            chosen = next((m for m in metrics if m["role"] == role and m.get("group") == "live"), None)
        if not chosen:
            chosen = next((m for m in metrics if m["role"] == role), None)
        if chosen:
            primary[role] = chosen
    return primary


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
