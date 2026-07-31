/* ==========================================================================
   Пиксельные примитивы Battery Monitor.

   Крупные числа рисуются растровым шрифтом 5×7 прямо в SVG: никакой внешней
   гарнитуры не нужно, а цифры остаются идеально «пиксельными» на любом экране.
   Здесь же — спрайты состояния и общее форматирование значений.
   ========================================================================== */

/* Растровый шрифт 5×7 — только то, что встречается в показаниях. */
const PX_GLYPHS = {
  "0": ["01110","10001","10011","10101","11001","10001","01110"],
  "1": ["00100","01100","00100","00100","00100","00100","01110"],
  "2": ["01110","10001","00001","00010","00100","01000","11111"],
  "3": ["11111","00010","00100","00010","00001","10001","01110"],
  "4": ["00010","00110","01010","10010","11111","00010","00010"],
  "5": ["11111","10000","11110","00001","00001","10001","01110"],
  "6": ["00110","01000","10000","11110","10001","10001","01110"],
  "7": ["11111","00001","00010","00100","01000","01000","01000"],
  "8": ["01110","10001","10001","01110","10001","10001","01110"],
  "9": ["01110","10001","10001","01111","00001","00010","01100"],
  "%": ["11001","11010","00010","00100","01000","01011","10011"],
  ".": ["00000","00000","00000","00000","00000","01100","01100"],
  "-": ["00000","00000","00000","11111","00000","00000","00000"],
  "+": ["00000","00100","00100","11111","00100","00100","00000"],
  " ": ["00000","00000","00000","00000","00000","00000","00000"],
  "?": ["01110","10001","00001","00110","00100","00000","00100"],
};

/* Спрайты 7×7: режим работы и связь. */
const PX_SPRITES = {
  up:      ["0001000","0011100","0111110","1111111","0011100","0011100","0011100"],
  down:    ["0011100","0011100","0011100","1111111","0111110","0011100","0001000"],
  idle:    ["0000000","0110110","0110110","0110110","0110110","0110110","0000000"],
  offline: ["1000001","1100011","0110110","0011100","0110110","1100011","1000001"],
  alert:   ["0011000","0011000","0011000","0011000","0011000","0000000","0011000"],
};

/* Логотип: батарея с клеммой. */
const PX_BATTERY = ["111111111111100","100000000000100","101111111110101",
                    "101111111110101","101111111110101","100000000000100","111111111111100"];

function pxRects(rows, ox = 0) {
  let out = "";
  rows.forEach((row, y) => {
    let x = 0;
    while (x < row.length) {
      if (row[x] === "1") {
        let run = 0;
        while (x + run < row.length && row[x + run] === "1") run++;
        out += `<rect x="${ox + x}" y="${y}" width="${run}" height="1"/>`;
        x += run;
      } else x++;
    }
  });
  return out;
}

/* Число (или короткая строка) растровым шрифтом. */
function pixelText(text, opts = {}) {
  const scale = opts.scale || 3, chars = [...String(text)];
  const w = chars.length ? chars.length * 6 - 1 : 1;
  let body = "";
  chars.forEach((ch, i) => { body += pxRects(PX_GLYPHS[ch] || PX_GLYPHS["?"], i * 6); });
  return `<svg class="pxnum" role="img" aria-label="${escapeHtml(text)}" width="${w * scale}"
    height="${7 * scale}" viewBox="0 0 ${w} 7" fill="currentColor"
    shape-rendering="crispEdges">${body}</svg>`;
}

/* Спрайт по имени из PX_SPRITES. */
function pixelSprite(name, opts = {}) {
  const rows = PX_SPRITES[name];
  if (!rows) return "";
  const scale = opts.scale || 2, w = rows[0].length, h = rows.length;
  return `<svg class="pxicon" aria-hidden="true" width="${w * scale}" height="${h * scale}"
    viewBox="0 0 ${w} ${h}" fill="currentColor" shape-rendering="crispEdges">${pxRects(rows)}</svg>`;
}

function pixelBattery(scale = 2) {
  const w = PX_BATTERY[0].length, h = PX_BATTERY.length;
  return `<svg class="pxicon" aria-hidden="true" width="${w * scale}" height="${h * scale}"
    viewBox="0 0 ${w} ${h}" fill="currentColor" shape-rendering="crispEdges">${pxRects(PX_BATTERY)}</svg>`;
}

/* ------------------------------------------------------------ Значения -- */
function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"]/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;" }[c]));
}

function fmtNum(v, unit) {
  if (typeof v !== "number" || !isFinite(v)) return "—";
  const abs = Math.abs(v);
  const s = Number.isInteger(v) ? String(v)
          : abs >= 100 ? v.toFixed(0) : abs >= 10 ? v.toFixed(1) : v.toFixed(2);
  return unit ? `${s} ${unit}` : s;
}

function fmtDuration(min) {
  if (min == null || !isFinite(min)) return null;
  if (min < 1) return BMI18n.t("dur.lessMin");
  const d = Math.floor(min / 1440), h = Math.floor((min % 1440) / 60), m = Math.round(min % 60);
  if (d > 0) return BMI18n.t("dur.dh", { d, h });
  if (h > 0) return BMI18n.t("dur.hm", { h, m });
  return BMI18n.t("dur.m", { m });
}

/* Время суток в формате текущего языка. */
function fmtTime(ts) {
  return new Date(ts || Date.now()).toLocaleTimeString(BMI18n.locale());
}

/* Уровень заряда -> класс цвета (ok / warn / low). */
function socLevel(p) { return p < 20 ? "low" : p < 50 ? "warn" : "ok"; }

/* Режим работы: спрайт и цвет; подпись — pxState(). */
const PX_STATE = {
  charging:    { sprite:"up",   cls:"t-charge" },
  discharging: { sprite:"down", cls:"t-ok" },
  idle:        { sprite:"idle", cls:"t-dim" },
  unknown:     { sprite:"idle", cls:"t-dim" },
};

function pxState(state) {
  const key = PX_STATE[state] ? state : "unknown";
  return { ...PX_STATE[key], label: BMI18n.t("state." + key) };
}
