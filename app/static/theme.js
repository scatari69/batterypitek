/* ==========================================================================
   Выбор оформления.

   Наборов два — «Пиксель» (по умолчанию) и «Dracula»; у каждого светлый и
   тёмный вариант плюс «Авто» по настройке системы. Выбор хранится в
   localStorage и применяется до первой отрисовки: файл подключается в <head>
   после pixel.css, поэтому переключения «на глазах» не видно.

   Токены цветов лежат в pixel.css, здесь только выбор варианта: атрибут
   data-theme на <html> получает уже разрешённое значение (pixel-dark,
   pixel-light, dracula-dark, dracula-light).
   ========================================================================== */
(function () {
  "use strict";

  const KEY = "bm-theme";
  const DEFAULT = "pixel-auto";

  /* Значение → подпись в списке. Порядок задаёт порядок пунктов. */
  const CHOICES = [
    ["pixel-auto",    "Пиксель · авто"],
    ["pixel-dark",    "Пиксель · тёмная"],
    ["pixel-light",   "Пиксель · светлая"],
    ["dracula-auto",  "Dracula · авто"],
    ["dracula-dark",  "Dracula · тёмная"],
    ["dracula-light", "Dracula · светлая"],
  ];
  const VALID = new Set(CHOICES.map(c => c[0]));

  /* Логотип-батарея 8×8 для favicon — перекрашивается вместе с темой. */
  const FAVICON = "<rect x='0' y='1' width='6' height='1'/><rect x='0' y='6' width='6' height='1'/>" +
    "<rect x='0' y='2' width='1' height='4'/><rect x='5' y='2' width='1' height='4'/>" +
    "<rect x='6' y='3' width='1' height='2'/><rect x='1' y='3' width='3' height='2'/>";

  const darkQuery = window.matchMedia("(prefers-color-scheme: dark)");
  const pickers = [];
  let pref = read();

  function read() {
    let v = null;
    try { v = localStorage.getItem(KEY); } catch (e) { /* приватный режим */ }
    return VALID.has(v) ? v : DEFAULT;
  }

  function write(v) {
    try { localStorage.setItem(KEY, v); } catch (e) { /* приватный режим */ }
  }

  /* «Авто» разворачиваем в конкретный вариант — в CSS остаётся только он. */
  function resolve(value) {
    const sep = value.lastIndexOf("-");
    const set = value.slice(0, sep), mode = value.slice(sep + 1);
    return set + "-" + (mode === "auto" ? (darkQuery.matches ? "dark" : "light") : mode);
  }

  function paintFavicon() {
    const link = document.querySelector('link[rel="icon"]');
    if (!link) return;
    const teal = getComputedStyle(document.documentElement).getPropertyValue("--teal").trim();
    if (!teal) return;
    link.href = "data:image/svg+xml," + encodeURIComponent(
      "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8' shape-rendering='crispEdges'>" +
      "<g fill='" + teal + "'>" + FAVICON + "</g></svg>");
  }

  function apply() {
    document.documentElement.setAttribute("data-theme", resolve(pref));
    paintFavicon();
  }

  function select(value) {
    if (!VALID.has(value) || value === pref) return;
    pref = value;
    write(pref);
    apply();
    pickers.forEach(sel => { sel.value = pref; });
  }

  /* Списки выбора появляются там, где в разметке стоит [data-theme-picker]. */
  function mountPickers() {
    document.querySelectorAll("[data-theme-picker]").forEach(host => {
      const sel = document.createElement("select");
      sel.className = "theme-pick";
      sel.title = "Оформление";
      sel.setAttribute("aria-label", "Оформление");
      CHOICES.forEach(([value, label]) => sel.add(new Option(label, value)));
      sel.value = pref;
      sel.addEventListener("change", () => select(sel.value));
      host.replaceChildren(sel);
      pickers.push(sel);
    });
  }

  apply();

  /* Системная тема сменилась — «Авто» должно поехать следом. */
  darkQuery.addEventListener("change", () => { if (pref.endsWith("-auto")) apply(); });

  /* Соседняя вкладка переключила оформление. */
  window.addEventListener("storage", e => {
    if (e.key !== KEY || !VALID.has(e.newValue)) return;
    pref = e.newValue;
    apply();
    pickers.forEach(sel => { sel.value = pref; });
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountPickers);
  } else {
    mountPickers();
  }
})();
