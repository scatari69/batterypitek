/* ==========================================================================
   Локализация интерфейса.

   Три языка: русский, украинский, английский. Словари лежат прямо здесь и
   грузятся вместе со страницей — переключение мгновенное, без запросов к
   серверу и без «мигания» непереведённым текстом.

   Источников выбора два (как и у оформления, см. theme.js):
   • язык по умолчанию — общая настройка из админ-панели (settings.json),
     приезжает в /api/config и кэшируется в localStorage;
   • локальный выбор — переключатель в футере страницы. Он важнее общей
     настройки и живёт только в этом браузере.

   Файл подключается в <head> первым: theme.js берёт отсюда подписи тем.

   Разметка переводится по атрибутам:
     data-i18n="ключ"        — textContent
     data-i18n-html="ключ"   — innerHTML (для строк с разметкой)
     data-i18n-ph="ключ"     — placeholder
     data-i18n-title="ключ"  — title
   Динамические куски страницы перерисовываются по BMI18n.onChange().
   ========================================================================== */
(function () {
  "use strict";

  /* ------------------------------------------------------------ Словари -- */
  const DICT = {

    /* ======================================================== Русский == */
    ru: {
      langName: "Русский",
      locale: "ru-RU",

      theme: {
        pick: "Оформление",
        pickTitle: "Оформление в этом браузере",
        "dracula-auto": "Dracula · авто",
        "dracula-dark": "Dracula · тёмная",
        "dracula-light": "Dracula · светлая",
        "pixel-auto": "Пиксель · авто",
        "pixel-dark": "Пиксель · тёмная",
        "pixel-light": "Пиксель · светлая",
      },

      lang: { pick: "Язык", pickTitle: "Язык в этом браузере" },

      state: { charging: "Заряд", discharging: "Разряд", idle: "Ожидание", unknown: "—" },

      dur: { lessMin: "< 1 мин", dh: "{d} дн {h} ч", hm: "{h} ч {m} мин", m: "{m} мин" },

      plural: { devices: { one: "устройство", few: "устройства", many: "устройств" } },

      common: {
        demo: "Демо",
        settings: "Настройки",
        init: "инициализация…",
        polling: "опрос…",
        updated: "обновлено {time}",
        noServer: "сервер не отвечает",
        noAnswer: "нет ответа от сервера",
        generated: "данные сгенерированы",
        yes: "да",
        no: "нет",
        dash: "—",
        error: "Ошибка: {msg}",
      },

      index: {
        title: "Battery Monitor · устройства",
        thDevice: "Устройство",
        thSoc: "Заряд",
        thState: "Режим",
        thEta: "До {pct} %",
        thReads: "Напряжение · ток",
        offline: "нет связи",
        etaCharging: "идёт заряд",
        etaAtOrBelow: "уже ≤ {pct} %",
        etaNotDischarging: "разряд не идёт",
        etaNoData: "нет ёмкости",
        emptyTitle: "Батарей пока нет",
        emptyText: "Добавьте устройства в настройках — или включите демо-режим, чтобы<br>посмотреть, как это выглядит с данными.",
        emptyBtn: "Открыть настройки",
      },

      device: {
        title: "Battery Monitor · устройство",
        back: "← Все устройства",
        heading: "Устройство",
        online: "На связи",
        offline: "Нет связи",
        conn: "Опрос…",
        charge: "Заряд батареи",
        history: "История",
        etaAtOrBelow: "Заряд уже ≤ {pct} %",
        etaNotDischarging: "Разряд не идёт",
        etaNoData: "Нет данных о ёмкости",
        eta: "До {pct} %: <b>≈ {dur}</b>",
        capRemain: "Остаток",
        capTotal: "Всего",
        capRes: "Сопротивление",
        chartCurrent: "Ток · заряд и разряд",
        chartPower: "Мощность",
        chartVoltage: "Напряжение",
        unreachable: "Сервер недоступен: {msg}",
      },

      admin: {
        title: "Battery Monitor · настройки",
        back: "← К дашборду",
        heading: "Настройки",
        logout: "Выйти",
        noPassword: "Панель не защищена паролем — задайте его в разделе «Безопасность».",

        tuya: "Подключение Tuya",
        tuyaDesc: 'Реквизиты из проекта на <a href="https://iot.tuya.com" target="_blank" rel="noopener">iot.tuya.com</a> (Cloud → ваш проект → Overview). Общие для всех устройств аккаунта.',
        accessKey: "Access Secret",
        accessKeyPh: "введите секрет",
        accessKeySaved: "сохранён ({hint}) — оставьте пустым",
        accessKeyHint: "Оставьте поле пустым, чтобы не менять сохранённый секрет.",
        accessIdPh: "например, 3x8k...",
        region: "Регион дата-центра",
        regionEu: "Центральная Европа (tuyaeu)",
        regionUs: "Западная Америка (tuyaus)",
        regionUeaz: "Восточная Америка (ueaz)",
        regionCn: "Китай (tuyacn)",
        regionIn: "Индия (tuyain)",
        regionHint: "Должен совпадать с регионом аккаунта в приложении Smart Life / Tuya.",
        testBtn: "Проверить подключение",
        testing: "Проверка…",

        devices: "Устройства",
        devicesDesc: "Список батарей: имя (произвольное) и Device ID. Можно добавить вручную или найти автоматически в аккаунте.",
        colName: "Имя",
        colId: "Device ID",
        addManual: "+ Добавить вручную",
        discoverBtn: "Найти в аккаунте",
        searching: "Поиск…",
        namePh: "Имя (напр. Гараж)",
        remove: "Удалить",
        notFound: "Устройства в аккаунте не найдены.",
        found: "Найдено: {n}",
        addAll: "Добавить все",
        add: "Добавить",
        added: "добавлено",
        already: "уже добавлено",
        devOnline: "онлайн",
        devOffline: "офлайн",
        addedToast: "Устройства добавлены в список — не забудьте сохранить.",

        general: "Общие параметры",
        poll: "Интервал опроса, секунд",
        demoMode: "Демо-режим (сгенерированные данные без обращения к Tuya)",

        appearance: "Оформление",
        appearanceDesc: "Тема по умолчанию — её видят все браузеры, где оформление не меняли вручную.",
        themeLabel: "Тема по умолчанию",
        themeHint: "Наборов два: «Dracula» — палитра Dracula и светлая Alucard, гарнитура Meslo, ровная панель; «Пиксель» — приборный VFD-дисплей и монохромный LCD с построчной развёрткой. «Авто» переключает светлый и тёмный вариант по настройке системы.",
        themeOwn: "Сейчас в этом браузере выбрана своя тема: {name}. Тема по умолчанию на неё не влияет.",
        themeDefault: "В этом браузере действует тема по умолчанию. Переключатель в шапке страницы меняет оформление только здесь.",
        themeReset: "Вернуть тему по умолчанию",

        language: "Язык",
        languageDesc: "Язык по умолчанию — его видят все браузеры, где язык не меняли вручную.",
        languageLabel: "Язык по умолчанию",
        languageHint: "На этом языке приходят и уведомления в Telegram.",
        langOwn: "Сейчас в этом браузере выбран свой язык: {name}. Язык по умолчанию на него не влияет.",
        langDefault: "В этом браузере действует язык по умолчанию. Переключатель в футере страницы меняет язык только здесь.",
        langReset: "Вернуть язык по умолчанию",

        tg: "Уведомления в Telegram",
        tgDesc: 'Бот пишет в чат, когда заряд батареи падает ниже порога или когда до этого порога остаётся мало времени. Создайте бота у <a href="https://t.me/BotFather" target="_blank" rel="noopener">@BotFather</a>, напишите ему (или добавьте в группу) и определите ID чата.',
        tgEnable: "Включить уведомления",
        tgToken: "Токен бота",
        tgTokenSaved: "сохранён ({hint}) — оставьте пустым",
        tgTokenHint: "Оставьте поле пустым, чтобы не менять сохранённый токен.",
        tgChat: "ID чата",
        tgChatPh: "например, 123456789 или -1001234567890",
        tgChatBtn: "Определить",
        tgChatHint: "Личный чат — положительное число, группа/канал — начинается с «−100».",
        tgChatPick: "Выбрать",
        tgChatPicked: "ID чата подставлен — не забудьте сохранить.",
        tgSoc: "Порог заряда, %",
        tgSocHint: "Общий порог: и для уведомления о низком заряде, и как цель для оценки времени.",
        tgLowSoc: "Заряд опустился ниже порога",
        tgLowEta: "До порога осталось меньше, минут:",
        tgRecovery: "Сообщать о возврате в норму («отбой»)",
        tgOffline: "Устройство недоступно (ошибка опроса)",
        tgCheck: "Интервал проверки, секунд",
        tgRepeat: "Повторять напоминание, минут",
        tgRepeatHint: "0 — не повторять: пока показатель не вернётся в норму, новых сообщений не будет.",
        tgTestBtn: "Отправить тестовое сообщение",
        tgSending: "Отправка…",
        tgLogBtn: "Обновить журнал",
        tgLogTitle: "Последние уведомления",
        tgLogFailed: " · не отправлено: {msg}",

        security: "Безопасность",
        securityDesc: "Пароль защищает админ-панель. Дашборд остаётся открытым.",
        securitySet: "Пароль установлен. Чтобы сменить — введите текущий и новый.",
        securityNone: "Пароль не задан. Панель открыта всем в сети — рекомендуем задать пароль.",
        pwCurrent: "Текущий пароль",
        pwNew: "Новый пароль",
        pwNewPh: "минимум 4 символа",
        pwSave: "Сохранить пароль",
        pwChange: "Сменить пароль",
        pwSet: "Установить пароль",
        pwSaved: "Пароль сохранён.",

        save: "Сохранить настройки",
        saved: "Сохранено",
        loadError: "Ошибка загрузки: {msg}",

        login: "Вход",
        loginDesc: "Введите пароль администратора.",
        password: "Пароль",
        loginBtn: "Войти",
        loginError: "Ошибка входа",
      },

      role: {
        voltage: "Напряжение", current: "Ток", power: "Мощность", soc: "Заряд",
        capacity: "Ёмкость", energy: "Энергия", temperature: "Температура",
        time: "Время", status: "Состояние", other: "",
      },

      group: {
        counter: "Счётчики и накопление", protection: "Защиты и пороги",
        config: "Настройки устройства", control: "Управление и состояние", other: "Прочее",
      },

      val: {
        actual_cap: "фактическая", rated_cap: "номинальная", on: "вкл", off: "выкл",
        english: "English", front: "передняя", back: "задняя",
      },

      dp: {
        cur_voltage: "Напряжение", cur_current: "Ток", cur_power: "Мощность",
        battery_percentage: "Заряд батареи", residual_electricity: "Остаточный заряд",
        electric_quantity: "Остаточная ёмкость", cap: "Остаточная ёмкость",
        remain_capacity: "Остаточная ёмкость", residual_capacity: "Остаточная ёмкость",
        ntc_temp: "Температура (датчик)", cpu_temp: "Температура платы",
        temp_current: "Температура", resistance: "Внутр. сопротивление",
        charging_capacity: "Заряжено", discharge_capacity: "Разряжено",
        accumulated_capacity: "Накоплено (ёмкость)", cumulative_charge: "Накоплено заряда",
        cumulative_discharge: "Накоплено разряда", accumulated_electricity: "Накоплено энергии",
        ele: "Энергия",
        ovp: "Защита: перенапряжение", lvp: "Защита: низкое напряжение",
        otp: "Защита: перегрев", opp: "Защита: превышение мощности",
        discharge_current: "Защита: ток разряда", discharge_power: "Защита: мощность разряда",
        mini_current: "Мин. ток (отсечка)",
        percent_100_bat_voltage: "Напряжение 100% заряда",
        percent_0_bat_voltage: "Напряжение 0% заряда",
        capacity_mode: "Режим расчёта ёмкости", diverter_size: "Шунт (номинал)",
        reporting_interval: "Интервал отчётов", standby_value: "Порог ожидания",
        work_value: "Рабочий порог", standby_time: "Время до ожидания",
        language: "Язык", menu: "Экран / меню",
        relay_switch: "Реле (нагрузка)", warning: "Предупреждение",
        current_zero: "Обнулить ток", real_time_swith_1s_60s: "Отчёты в реальном времени",
        data_reset: "Сброс данных", wifi_reset: "Сброс Wi-Fi", factor_reset: "Заводской сброс",
        charge_state: "Режим", work_state: "Режим работы",
      },
    },

    /* ==================================================== Українська == */
    uk: {
      langName: "Українська",
      locale: "uk-UA",

      theme: {
        pick: "Оформлення",
        pickTitle: "Оформлення в цьому браузері",
        "dracula-auto": "Dracula · авто",
        "dracula-dark": "Dracula · темна",
        "dracula-light": "Dracula · світла",
        "pixel-auto": "Піксель · авто",
        "pixel-dark": "Піксель · темна",
        "pixel-light": "Піксель · світла",
      },

      lang: { pick: "Мова", pickTitle: "Мова в цьому браузері" },

      state: { charging: "Заряд", discharging: "Розряд", idle: "Очікування", unknown: "—" },

      dur: { lessMin: "< 1 хв", dh: "{d} дн {h} год", hm: "{h} год {m} хв", m: "{m} хв" },

      plural: { devices: { one: "пристрій", few: "пристрої", many: "пристроїв" } },

      common: {
        demo: "Демо",
        settings: "Налаштування",
        init: "ініціалізація…",
        polling: "опитування…",
        updated: "оновлено {time}",
        noServer: "сервер не відповідає",
        noAnswer: "немає відповіді від сервера",
        generated: "дані згенеровано",
        yes: "так",
        no: "ні",
        dash: "—",
        error: "Помилка: {msg}",
      },

      index: {
        title: "Battery Monitor · пристрої",
        thDevice: "Пристрій",
        thSoc: "Заряд",
        thState: "Режим",
        thEta: "До {pct} %",
        thReads: "Напруга · струм",
        offline: "немає зв'язку",
        etaCharging: "триває заряд",
        etaAtOrBelow: "вже ≤ {pct} %",
        etaNotDischarging: "розряд не триває",
        etaNoData: "немає ємності",
        emptyTitle: "Батарей поки немає",
        emptyText: "Додайте пристрої в налаштуваннях — або увімкніть демо-режим, щоб<br>побачити, як це виглядає з даними.",
        emptyBtn: "Відкрити налаштування",
      },

      device: {
        title: "Battery Monitor · пристрій",
        back: "← Усі пристрої",
        heading: "Пристрій",
        online: "На зв'язку",
        offline: "Немає зв'язку",
        conn: "Опитування…",
        charge: "Заряд батареї",
        history: "Історія",
        etaAtOrBelow: "Заряд уже ≤ {pct} %",
        etaNotDischarging: "Розряд не триває",
        etaNoData: "Немає даних про ємність",
        eta: "До {pct} %: <b>≈ {dur}</b>",
        capRemain: "Залишок",
        capTotal: "Усього",
        capRes: "Опір",
        chartCurrent: "Струм · заряд і розряд",
        chartPower: "Потужність",
        chartVoltage: "Напруга",
        unreachable: "Сервер недоступний: {msg}",
      },

      admin: {
        title: "Battery Monitor · налаштування",
        back: "← До дашборда",
        heading: "Налаштування",
        logout: "Вийти",
        noPassword: "Панель не захищена паролем — задайте його в розділі «Безпека».",

        tuya: "Підключення Tuya",
        tuyaDesc: 'Реквізити з проєкту на <a href="https://iot.tuya.com" target="_blank" rel="noopener">iot.tuya.com</a> (Cloud → ваш проєкт → Overview). Спільні для всіх пристроїв акаунта.',
        accessKey: "Access Secret",
        accessKeyPh: "введіть секрет",
        accessKeySaved: "збережено ({hint}) — залиште порожнім",
        accessKeyHint: "Залиште поле порожнім, щоб не міняти збережений секрет.",
        accessIdPh: "наприклад, 3x8k...",
        region: "Регіон дата-центру",
        regionEu: "Центральна Європа (tuyaeu)",
        regionUs: "Західна Америка (tuyaus)",
        regionUeaz: "Східна Америка (ueaz)",
        regionCn: "Китай (tuyacn)",
        regionIn: "Індія (tuyain)",
        regionHint: "Має збігатися з регіоном акаунта в застосунку Smart Life / Tuya.",
        testBtn: "Перевірити підключення",
        testing: "Перевірка…",

        devices: "Пристрої",
        devicesDesc: "Список батарей: ім'я (довільне) і Device ID. Можна додати вручну або знайти автоматично в акаунті.",
        colName: "Ім'я",
        colId: "Device ID",
        addManual: "+ Додати вручну",
        discoverBtn: "Знайти в акаунті",
        searching: "Пошук…",
        namePh: "Ім'я (напр. Гараж)",
        remove: "Видалити",
        notFound: "Пристроїв в акаунті не знайдено.",
        found: "Знайдено: {n}",
        addAll: "Додати всі",
        add: "Додати",
        added: "додано",
        already: "уже додано",
        devOnline: "онлайн",
        devOffline: "офлайн",
        addedToast: "Пристрої додано до списку — не забудьте зберегти.",

        general: "Загальні параметри",
        poll: "Інтервал опитування, секунд",
        demoMode: "Демо-режим (згенеровані дані без звернення до Tuya)",

        appearance: "Оформлення",
        appearanceDesc: "Тема за замовчуванням — її бачать усі браузери, де оформлення не міняли вручну.",
        themeLabel: "Тема за замовчуванням",
        themeHint: "Наборів два: «Dracula» — палітра Dracula і світла Alucard, гарнітура Meslo, рівна панель; «Піксель» — приладовий VFD-дисплей і монохромний LCD з рядковою розгорткою. «Авто» перемикає світлий і темний варіант за налаштуванням системи.",
        themeOwn: "Зараз у цьому браузері обрано власну тему: {name}. Тема за замовчуванням на неї не впливає.",
        themeDefault: "У цьому браузері діє тема за замовчуванням. Перемикач у шапці сторінки міняє оформлення тільки тут.",
        themeReset: "Повернути тему за замовчуванням",

        language: "Мова",
        languageDesc: "Мова за замовчуванням — її бачать усі браузери, де мову не міняли вручну.",
        languageLabel: "Мова за замовчуванням",
        languageHint: "Цією мовою приходять і сповіщення в Telegram.",
        langOwn: "Зараз у цьому браузері обрано власну мову: {name}. Мова за замовчуванням на неї не впливає.",
        langDefault: "У цьому браузері діє мова за замовчуванням. Перемикач у футері сторінки міняє мову тільки тут.",
        langReset: "Повернути мову за замовчуванням",

        tg: "Сповіщення в Telegram",
        tgDesc: 'Бот пише в чат, коли заряд батареї падає нижче порога або коли до цього порога лишається мало часу. Створіть бота в <a href="https://t.me/BotFather" target="_blank" rel="noopener">@BotFather</a>, напишіть йому (або додайте в групу) і визначте ID чату.',
        tgEnable: "Увімкнути сповіщення",
        tgToken: "Токен бота",
        tgTokenSaved: "збережено ({hint}) — залиште порожнім",
        tgTokenHint: "Залиште поле порожнім, щоб не міняти збережений токен.",
        tgChat: "ID чату",
        tgChatPh: "наприклад, 123456789 або -1001234567890",
        tgChatBtn: "Визначити",
        tgChatHint: "Особистий чат — додатне число, група/канал — починається з «−100».",
        tgChatPick: "Обрати",
        tgChatPicked: "ID чату підставлено — не забудьте зберегти.",
        tgSoc: "Поріг заряду, %",
        tgSocHint: "Спільний поріг: і для сповіщення про низький заряд, і як ціль для оцінки часу.",
        tgLowSoc: "Заряд опустився нижче порога",
        tgLowEta: "До порога лишилося менше, хвилин:",
        tgRecovery: "Повідомляти про повернення в норму («відбій»)",
        tgOffline: "Пристрій недоступний (помилка опитування)",
        tgCheck: "Інтервал перевірки, секунд",
        tgRepeat: "Повторювати нагадування, хвилин",
        tgRepeatHint: "0 — не повторювати: доки показник не повернеться в норму, нових повідомлень не буде.",
        tgTestBtn: "Надіслати тестове повідомлення",
        tgSending: "Надсилання…",
        tgLogBtn: "Оновити журнал",
        tgLogTitle: "Останні сповіщення",
        tgLogFailed: " · не надіслано: {msg}",

        security: "Безпека",
        securityDesc: "Пароль захищає адмін-панель. Дашборд лишається відкритим.",
        securitySet: "Пароль встановлено. Щоб змінити — введіть поточний і новий.",
        securityNone: "Пароль не задано. Панель відкрита всім у мережі — радимо задати пароль.",
        pwCurrent: "Поточний пароль",
        pwNew: "Новий пароль",
        pwNewPh: "мінімум 4 символи",
        pwSave: "Зберегти пароль",
        pwChange: "Змінити пароль",
        pwSet: "Встановити пароль",
        pwSaved: "Пароль збережено.",

        save: "Зберегти налаштування",
        saved: "Збережено",
        loadError: "Помилка завантаження: {msg}",

        login: "Вхід",
        loginDesc: "Введіть пароль адміністратора.",
        password: "Пароль",
        loginBtn: "Увійти",
        loginError: "Помилка входу",
      },

      role: {
        voltage: "Напруга", current: "Струм", power: "Потужність", soc: "Заряд",
        capacity: "Ємність", energy: "Енергія", temperature: "Температура",
        time: "Час", status: "Стан", other: "",
      },

      group: {
        counter: "Лічильники та накопичення", protection: "Захисти та пороги",
        config: "Налаштування пристрою", control: "Керування та стан", other: "Інше",
      },

      val: {
        actual_cap: "фактична", rated_cap: "номінальна", on: "увімк", off: "вимк",
        english: "English", front: "передня", back: "задня",
      },

      dp: {
        cur_voltage: "Напруга", cur_current: "Струм", cur_power: "Потужність",
        battery_percentage: "Заряд батареї", residual_electricity: "Залишковий заряд",
        electric_quantity: "Залишкова ємність", cap: "Залишкова ємність",
        remain_capacity: "Залишкова ємність", residual_capacity: "Залишкова ємність",
        ntc_temp: "Температура (датчик)", cpu_temp: "Температура плати",
        temp_current: "Температура", resistance: "Внутр. опір",
        charging_capacity: "Заряджено", discharge_capacity: "Розряджено",
        accumulated_capacity: "Накопичено (ємність)", cumulative_charge: "Накопичено заряду",
        cumulative_discharge: "Накопичено розряду", accumulated_electricity: "Накопичено енергії",
        ele: "Енергія",
        ovp: "Захист: перенапруга", lvp: "Захист: низька напруга",
        otp: "Захист: перегрів", opp: "Захист: перевищення потужності",
        discharge_current: "Захист: струм розряду", discharge_power: "Захист: потужність розряду",
        mini_current: "Мін. струм (відсічка)",
        percent_100_bat_voltage: "Напруга 100% заряду",
        percent_0_bat_voltage: "Напруга 0% заряду",
        capacity_mode: "Режим розрахунку ємності", diverter_size: "Шунт (номінал)",
        reporting_interval: "Інтервал звітів", standby_value: "Поріг очікування",
        work_value: "Робочий поріг", standby_time: "Час до очікування",
        language: "Мова", menu: "Екран / меню",
        relay_switch: "Реле (навантаження)", warning: "Попередження",
        current_zero: "Обнулити струм", real_time_swith_1s_60s: "Звіти в реальному часі",
        data_reset: "Скидання даних", wifi_reset: "Скидання Wi-Fi", factor_reset: "Заводське скидання",
        charge_state: "Режим", work_state: "Режим роботи",
      },
    },

    /* ======================================================== English == */
    en: {
      langName: "English",
      locale: "en-GB",

      theme: {
        pick: "Theme",
        pickTitle: "Theme in this browser",
        "dracula-auto": "Dracula · auto",
        "dracula-dark": "Dracula · dark",
        "dracula-light": "Dracula · light",
        "pixel-auto": "Pixel · auto",
        "pixel-dark": "Pixel · dark",
        "pixel-light": "Pixel · light",
      },

      lang: { pick: "Language", pickTitle: "Language in this browser" },

      state: { charging: "Charging", discharging: "Discharging", idle: "Idle", unknown: "—" },

      dur: { lessMin: "< 1 min", dh: "{d} d {h} h", hm: "{h} h {m} min", m: "{m} min" },

      plural: { devices: { one: "device", other: "devices" } },

      common: {
        demo: "Demo",
        settings: "Settings",
        init: "initialising…",
        polling: "polling…",
        updated: "updated {time}",
        noServer: "server not responding",
        noAnswer: "no answer from server",
        generated: "generated data",
        yes: "yes",
        no: "no",
        dash: "—",
        error: "Error: {msg}",
      },

      index: {
        title: "Battery Monitor · devices",
        thDevice: "Device",
        thSoc: "Charge",
        thState: "Mode",
        thEta: "To {pct} %",
        thReads: "Voltage · current",
        offline: "no connection",
        etaCharging: "charging",
        etaAtOrBelow: "already ≤ {pct} %",
        etaNotDischarging: "not discharging",
        etaNoData: "no capacity",
        emptyTitle: "No batteries yet",
        emptyText: "Add devices in the settings — or turn on demo mode to see<br>what this looks like with data.",
        emptyBtn: "Open settings",
      },

      device: {
        title: "Battery Monitor · device",
        back: "← All devices",
        heading: "Device",
        online: "Online",
        offline: "Offline",
        conn: "Polling…",
        charge: "Battery charge",
        history: "History",
        etaAtOrBelow: "Charge already ≤ {pct} %",
        etaNotDischarging: "Not discharging",
        etaNoData: "No capacity data",
        eta: "To {pct} %: <b>≈ {dur}</b>",
        capRemain: "Remaining",
        capTotal: "Total",
        capRes: "Resistance",
        chartCurrent: "Current · charge and discharge",
        chartPower: "Power",
        chartVoltage: "Voltage",
        unreachable: "Server unreachable: {msg}",
      },

      admin: {
        title: "Battery Monitor · settings",
        back: "← To dashboard",
        heading: "Settings",
        logout: "Log out",
        noPassword: "The panel is not password-protected — set one in the “Security” section.",

        tuya: "Tuya connection",
        tuyaDesc: 'Credentials from your project at <a href="https://iot.tuya.com" target="_blank" rel="noopener">iot.tuya.com</a> (Cloud → your project → Overview). Shared by every device in the account.',
        accessKey: "Access Secret",
        accessKeyPh: "enter the secret",
        accessKeySaved: "saved ({hint}) — leave empty",
        accessKeyHint: "Leave the field empty to keep the saved secret.",
        accessIdPh: "e.g. 3x8k...",
        region: "Data centre region",
        regionEu: "Central Europe (tuyaeu)",
        regionUs: "Western America (tuyaus)",
        regionUeaz: "Eastern America (ueaz)",
        regionCn: "China (tuyacn)",
        regionIn: "India (tuyain)",
        regionHint: "Must match your account region in the Smart Life / Tuya app.",
        testBtn: "Test connection",
        testing: "Testing…",

        devices: "Devices",
        devicesDesc: "The list of batteries: a name (any) and a Device ID. Add them by hand or discover them in the account.",
        colName: "Name",
        colId: "Device ID",
        addManual: "+ Add manually",
        discoverBtn: "Discover in account",
        searching: "Searching…",
        namePh: "Name (e.g. Garage)",
        remove: "Remove",
        notFound: "No devices found in the account.",
        found: "Found: {n}",
        addAll: "Add all",
        add: "Add",
        added: "added",
        already: "already added",
        devOnline: "online",
        devOffline: "offline",
        addedToast: "Devices added to the list — don't forget to save.",

        general: "General",
        poll: "Poll interval, seconds",
        demoMode: "Demo mode (generated data, no calls to Tuya)",

        appearance: "Appearance",
        appearanceDesc: "The default theme — seen by every browser where the theme was not changed by hand.",
        themeLabel: "Default theme",
        themeHint: "Two sets: “Dracula” — the Dracula palette and its light Alucard variant, Meslo typeface, flat panel; “Pixel” — an instrument VFD display and a monochrome LCD with scanlines. “Auto” follows the system light/dark setting.",
        themeOwn: "This browser currently uses its own theme: {name}. The default theme does not affect it.",
        themeDefault: "This browser follows the default theme. The switch in the page header changes the theme here only.",
        themeReset: "Back to the default theme",

        language: "Language",
        languageDesc: "The default language — seen by every browser where the language was not changed by hand.",
        languageLabel: "Default language",
        languageHint: "Telegram notifications are sent in this language too.",
        langOwn: "This browser currently uses its own language: {name}. The default language does not affect it.",
        langDefault: "This browser follows the default language. The switch in the page footer changes the language here only.",
        langReset: "Back to the default language",

        tg: "Telegram notifications",
        tgDesc: 'The bot writes to a chat when the battery charge drops below the threshold, or when little time is left before it. Create a bot with <a href="https://t.me/BotFather" target="_blank" rel="noopener">@BotFather</a>, message it (or add it to a group) and detect the chat ID.',
        tgEnable: "Enable notifications",
        tgToken: "Bot token",
        tgTokenSaved: "saved ({hint}) — leave empty",
        tgTokenHint: "Leave the field empty to keep the saved token.",
        tgChat: "Chat ID",
        tgChatPh: "e.g. 123456789 or -1001234567890",
        tgChatBtn: "Detect",
        tgChatHint: "A private chat is a positive number; a group or channel starts with “−100”.",
        tgChatPick: "Pick",
        tgChatPicked: "Chat ID filled in — don't forget to save.",
        tgSoc: "Charge threshold, %",
        tgSocHint: "One threshold: both for the low-charge alert and as the target for the time estimate.",
        tgLowSoc: "Charge dropped below the threshold",
        tgLowEta: "Less time left to the threshold, minutes:",
        tgRecovery: "Report the return to normal (all clear)",
        tgOffline: "Device unreachable (poll error)",
        tgCheck: "Check interval, seconds",
        tgRepeat: "Repeat the reminder, minutes",
        tgRepeatHint: "0 — no repeats: no new messages until the reading is back to normal.",
        tgTestBtn: "Send a test message",
        tgSending: "Sending…",
        tgLogBtn: "Refresh the log",
        tgLogTitle: "Recent notifications",
        tgLogFailed: " · not sent: {msg}",

        security: "Security",
        securityDesc: "The password protects the admin panel. The dashboard stays open.",
        securitySet: "A password is set. To change it, enter the current one and a new one.",
        securityNone: "No password is set. The panel is open to everyone on the network — setting one is recommended.",
        pwCurrent: "Current password",
        pwNew: "New password",
        pwNewPh: "at least 4 characters",
        pwSave: "Save password",
        pwChange: "Change password",
        pwSet: "Set password",
        pwSaved: "Password saved.",

        save: "Save settings",
        saved: "Saved",
        loadError: "Load error: {msg}",

        login: "Sign in",
        loginDesc: "Enter the administrator password.",
        password: "Password",
        loginBtn: "Sign in",
        loginError: "Sign-in error",
      },

      role: {
        voltage: "Voltage", current: "Current", power: "Power", soc: "Charge",
        capacity: "Capacity", energy: "Energy", temperature: "Temperature",
        time: "Time", status: "State", other: "",
      },

      group: {
        counter: "Counters and accumulation", protection: "Protections and thresholds",
        config: "Device settings", control: "Control and state", other: "Other",
      },

      val: {
        actual_cap: "actual", rated_cap: "rated", on: "on", off: "off",
        english: "English", front: "front", back: "back",
      },

      dp: {
        cur_voltage: "Voltage", cur_current: "Current", cur_power: "Power",
        battery_percentage: "Battery charge", residual_electricity: "Residual charge",
        electric_quantity: "Remaining capacity", cap: "Remaining capacity",
        remain_capacity: "Remaining capacity", residual_capacity: "Remaining capacity",
        ntc_temp: "Temperature (sensor)", cpu_temp: "Board temperature",
        temp_current: "Temperature", resistance: "Internal resistance",
        charging_capacity: "Charged", discharge_capacity: "Discharged",
        accumulated_capacity: "Accumulated (capacity)", cumulative_charge: "Cumulative charge",
        cumulative_discharge: "Cumulative discharge", accumulated_electricity: "Accumulated energy",
        ele: "Energy",
        ovp: "Protection: overvoltage", lvp: "Protection: undervoltage",
        otp: "Protection: overheating", opp: "Protection: overpower",
        discharge_current: "Protection: discharge current", discharge_power: "Protection: discharge power",
        mini_current: "Min. current (cutoff)",
        percent_100_bat_voltage: "Voltage at 100% charge",
        percent_0_bat_voltage: "Voltage at 0% charge",
        capacity_mode: "Capacity calculation mode", diverter_size: "Shunt (rating)",
        reporting_interval: "Reporting interval", standby_value: "Standby threshold",
        work_value: "Working threshold", standby_time: "Time to standby",
        language: "Language", menu: "Screen / menu",
        relay_switch: "Relay (load)", warning: "Warning",
        current_zero: "Zero the current", real_time_swith_1s_60s: "Real-time reporting",
        data_reset: "Data reset", wifi_reset: "Wi-Fi reset", factor_reset: "Factory reset",
        charge_state: "Mode", work_state: "Operating mode",
      },
    },
  };

  /* ------------------------------------------------------------ Рантайм -- */
  const KEY = "bm-lang";                 /* локальный выбор в этом браузере */
  const KEY_DEFAULT = "bm-lang-default"; /* кэш общей настройки с сервера */
  const SHIPPED = "ru";                  /* пока сервер не ответил и выбора нет */

  const CHOICES = Object.keys(DICT).map(code => [code, DICT[code].langName]);
  const known = code => Object.prototype.hasOwnProperty.call(DICT, code);

  const pickers = [];
  const listeners = [];

  function read(key) {
    let v = null;
    try { v = localStorage.getItem(key); } catch (e) { /* приватный режим */ }
    return known(v) ? v : null;
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

  /* Поиск по точечному пути: сначала в текущем языке, потом в русском. */
  function lookup(dict, path) {
    let node = dict;
    for (const part of path.split(".")) {
      if (node == null || typeof node !== "object") return undefined;
      node = node[part];
    }
    return typeof node === "string" ? node : undefined;
  }

  function fill(text, vars) {
    if (!vars) return text;
    return text.replace(/\{(\w+)\}/g, (m, name) => (name in vars ? String(vars[name]) : m));
  }

  /* Перевод по ключу вида "admin.tgChat"; неизвестный ключ возвращается как есть. */
  function t(path, vars) {
    const text = lookup(DICT[current()], path);
    return fill(text !== undefined ? text : (lookup(DICT.ru, path) ?? path), vars);
  }

  /* Коды точек данных приходят от Tuya — берём только собственные ключи словаря,
     чтобы «constructor» и подобные имена не вытащили что-нибудь из прототипа. */
  const own = (obj, key) => (Object.prototype.hasOwnProperty.call(obj, key) ? obj[key] : undefined);

  /* Подпись точки данных: свой перевод кода, иначе роль, иначе сам код. */
  function dp(code, role) {
    const d = DICT[current()], ru = DICT.ru;
    return (own(d.dp, code) || own(ru.dp, code)
            || (role && (own(d.role, role) || own(ru.role, role))) || code || "—");
  }

  /* Множественное число: у ru/uk три формы, у английского две. */
  function plural(n, key) {
    const forms = own(DICT[current()].plural, key) || own(DICT.ru.plural, key) || {};
    if (forms.few === undefined) return n === 1 ? forms.one : forms.other;
    const m10 = n % 10, m100 = n % 100;
    if (m10 === 1 && m100 !== 11) return forms.one;
    if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return forms.few;
    return forms.many;
  }

  const MARKED = "[data-i18n],[data-i18n-html],[data-i18n-ph],[data-i18n-title]";

  function applyTo(el) {
    const d = el.dataset;
    if (d.i18n !== undefined) el.textContent = t(d.i18n);
    if (d.i18nHtml !== undefined) el.innerHTML = t(d.i18nHtml);
    if (d.i18nPh !== undefined) el.placeholder = t(d.i18nPh);
    if (d.i18nTitle !== undefined) el.title = t(d.i18nTitle);
  }

  /* Проставляем переводы в разметку с data-i18n-атрибутами (корень включительно). */
  function apply(root) {
    const scope = root || document;
    if (scope.nodeType === 1 && scope.matches(MARKED)) applyTo(scope);
    scope.querySelectorAll(MARKED).forEach(applyTo);
  }

  function refresh() {
    document.documentElement.setAttribute("lang", current());
    pickers.forEach(sel => { sel.value = current(); });
    apply(document);
    listeners.forEach(fn => fn());
  }

  /* Выбор в футере: только для этого браузера. null — вернуться к общему языку. */
  function select(value) {
    const next = known(value) ? value : null;
    if (next === local) return;
    local = next;
    write(KEY, local);
    refresh();
  }

  /* Общий язык из /api/config: применяем, если локального выбора нет. */
  function setDefault(value) {
    if (!known(value)) return;
    const changed = value !== fallback;
    fallback = value;
    write(KEY_DEFAULT, fallback);   /* пишем всегда: кэш должен пережить смену SHIPPED */
    if (changed && !local) refresh();
  }

  /* Списки выбора появляются там, где в разметке стоит [data-lang-picker]. */
  function mountPickers() {
    document.querySelectorAll("[data-lang-picker]").forEach(host => {
      const sel = document.createElement("select");
      sel.className = "theme-pick lang-pick";
      CHOICES.forEach(([value, label]) => sel.add(new Option(label, value)));
      sel.value = current();
      sel.title = t("lang.pickTitle");
      sel.setAttribute("aria-label", t("lang.pick"));
      sel.addEventListener("change", () => select(sel.value));
      host.replaceChildren(sel);
      pickers.push(sel);
    });
  }

  /* Обёртка над fetch: сообщает серверу выбранный язык, чтобы сообщения об
     ошибках и имена демо-устройств приезжали на нём же. */
  window.bmFetch = function (url, opts) {
    const o = Object.assign({}, opts);
    o.headers = Object.assign({}, o.headers, { "X-BM-Lang": current() });
    return fetch(url, o);
  };

  window.BMI18n = {
    CHOICES: CHOICES,
    langName: code => (DICT[code] || {}).langName || code,
    current: current,                 /* какой язык показывается сейчас */
    override: () => local,            /* локальный выбор или null */
    defaultLang: () => fallback,      /* общий язык (кэш серверной настройки) */
    locale: () => DICT[current()].locale,
    select: select,
    reset: () => select(null),
    setDefault: setDefault,
    t: t,
    dp: dp,
    plural: plural,
    apply: apply,
    onChange: fn => { listeners.push(fn); },
  };

  document.documentElement.setAttribute("lang", current());

  /* Соседняя вкладка переключила язык. */
  window.addEventListener("storage", e => {
    if (e.key === KEY) { local = read(KEY); refresh(); }
    else if (e.key === KEY_DEFAULT) { fallback = read(KEY_DEFAULT) || SHIPPED; refresh(); }
  });

  if (document.readyState === "loading") {
    /* Переводим узлы прямо по ходу разбора документа: иначе исходный русский
       текст разметки успевает мелькнуть до DOMContentLoaded. */
    const obs = new MutationObserver(records => {
      records.forEach(rec => rec.addedNodes.forEach(node => {
        if (node.nodeType === 1) apply(node);
      }));
    });
    obs.observe(document.documentElement, { childList: true, subtree: true });
    document.addEventListener("DOMContentLoaded", () => {
      obs.disconnect();
      apply(document);
      mountPickers();
    });
  } else {
    apply(document);
    mountPickers();
  }
})();
