/* ==========================================================================
   Выбор оформления.

   Наборов два — «Dracula» (по умолчанию) и «Пиксель»; у каждого светлый и
   тёмный вариант плюс «Авто» по настройке системы.

   Источников выбора тоже два:
   • тема по умолчанию — общая настройка из админ-панели (settings.json),
     приезжает в /api/config и кэшируется в localStorage, чтобы применяться
     сразу, до ответа сервера;
   • локальный выбор — переключатель в шапке страницы. Он важнее общей
     настройки и живёт только в этом браузере.

   Файл подключается в <head> после pixel.css, поэтому тема встаёт до первой
   отрисовки и переключения «на глазах» не видно. Токены цветов лежат в
   pixel.css, здесь только выбор варианта: атрибут data-theme на <html>
   получает уже разрешённое значение (pixel-dark, pixel-light, dracula-dark,
   dracula-light).

   Подписи вариантов приходят из i18n.js (он подключается раньше).
   ========================================================================== */
(function () {
  "use strict";

  const KEY = "bm-theme";            /* локальный выбор в этом браузере */
  const KEY_DEFAULT = "bm-theme-default";  /* кэш общей настройки с сервера */
  const SHIPPED = "dracula-auto";    /* пока сервер не ответил и выбора нет */

  /* Порядок задаёт порядок пунктов в списках выбора. */
  const CHOICES = ["dracula-auto", "dracula-dark", "dracula-light",
                   "pixel-auto", "pixel-dark", "pixel-light"];
  const KNOWN = new Set(CHOICES);

  const label = value => (window.BMI18n ? BMI18n.t("theme." + value) : value);

  /* Логотип-батарея 8×8 для favicon — перекрашивается вместе с темой. */
  const FAVICON = "<rect x='0' y='1' width='6' height='1'/><rect x='0' y='6' width='6' height='1'/>" +
    "<rect x='0' y='2' width='1' height='4'/><rect x='5' y='2' width='1' height='4'/>" +
    "<rect x='6' y='3' width='1' height='2'/><rect x='1' y='3' width='3' height='2'/>";

  const darkQuery = window.matchMedia("(prefers-color-scheme: dark)");
  const pickers = [];
  const listeners = [];

  function read(key) {
    let v = null;
    try { v = localStorage.getItem(key); } catch (e) { /* приватный режим */ }
    return KNOWN.has(v) ? v : null;
  }

  function write(key, value) {
    try {
      if (value) localStorage.setItem(key, value);
      else localStorage.removeItem(key);
    } catch (e) { /* приватный режим */ }
  }

  let local = read(KEY);
  let fallback = read(KEY_DEFAULT) || SHIPPED;

  const current = () => local || fallback;

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
    document.documentElement.setAttribute("data-theme", resolve(current()));
    paintFavicon();
    pickers.forEach(sel => { sel.value = current(); });
    listeners.forEach(fn => fn());
  }

  /* Выбор в шапке: только для этого браузера. null — вернуться к общей теме. */
  function select(value) {
    const next = KNOWN.has(value) ? value : null;
    if (next === local) return;
    local = next;
    write(KEY, local);
    apply();
  }

  /* Общая тема из /api/config: применяем, если локального выбора нет. */
  function setDefault(value) {
    if (!KNOWN.has(value)) return;
    const changed = value !== fallback;
    fallback = value;
    write(KEY_DEFAULT, fallback);   /* пишем всегда: кэш должен пережить смену SHIPPED */
    if (changed) apply();
  }

  /* Списки выбора появляются там, где в разметке стоит [data-theme-picker]. */
  function mountPickers() {
    document.querySelectorAll("[data-theme-picker]").forEach(host => {
      const sel = document.createElement("select");
      sel.className = "theme-pick";
      CHOICES.forEach(value => sel.add(new Option(label(value), value)));
      sel.value = current();
      sel.addEventListener("change", () => select(sel.value));
      host.replaceChildren(sel);
      pickers.push(sel);
      relabel(sel);
    });
  }

  /* Сменился язык — переписываем подписи вариантов, выбор не трогаем. */
  function relabel(sel) {
    sel.title = window.BMI18n ? BMI18n.t("theme.pickTitle") : "";
    sel.setAttribute("aria-label", window.BMI18n ? BMI18n.t("theme.pick") : "");
    [...sel.options].forEach(opt => { opt.textContent = label(opt.value); });
  }

  window.BMTheme = {
    CHOICES: CHOICES,
    label: label,
    current: current,                 /* что показывается сейчас */
    override: () => local,            /* локальный выбор или null */
    defaultTheme: () => fallback,     /* общая тема (кэш серверной настройки) */
    select: select,
    reset: () => select(null),
    setDefault: setDefault,
    onChange: fn => { listeners.push(fn); },
  };

  apply();

  if (window.BMI18n) BMI18n.onChange(() => pickers.forEach(relabel));

  /* Системная тема сменилась — «Авто» должно поехать следом. */
  darkQuery.addEventListener("change", () => { if (current().endsWith("-auto")) apply(); });

  /* Соседняя вкладка переключила оформление. */
  window.addEventListener("storage", e => {
    if (e.key === KEY) { local = read(KEY); apply(); }
    else if (e.key === KEY_DEFAULT) { fallback = read(KEY_DEFAULT) || SHIPPED; apply(); }
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountPickers);
  } else {
    mountPickers();
  }
})();
