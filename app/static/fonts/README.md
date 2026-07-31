# Meslo LG M

Гарнитура набора тем **Dracula**. Meslo LG — вариант Menlo от André Berg,
исходники: <https://github.com/andreberg/Meslo-Font>, дистрибутив взят из
npm-пакета [`meslo@1.0.0`](https://www.npmjs.com/package/meslo).

Файлы `MesloLGM-Regular.woff2` и `MesloLGM-Bold.woff2` — **изменённые**:
исходные TTF урезаны до нужного интерфейсу набора символов (базовая латиница,
Latin-1, кириллица, типографские знаки и стрелки) и пересобраны в WOFF2
через `pyftsubset` из [fontTools](https://github.com/fonttools/fonttools):

```
pyftsubset MesloLGM-<Regular|Bold>.ttf \
  --unicodes="U+0020-007E,U+00A0-00FF,U+0131,U+0152-0153,U+02C6,U+02DA,U+02DC,\
U+0400-045F,U+0490-0491,U+2010-2015,U+2018-201A,U+201C-201E,U+2020-2022,U+2026,\
U+2030,U+2039-203A,U+2044,U+2070-2079,U+2116,U+2122,U+2190-2193,U+2212,U+2248,\
U+2260,U+2264-2265,U+25A0-25AA,U+2713" \
  --layout-features="kern,mark,mkmk,ccmp,locl" \
  --name-IDs='*' --notdef-outline \
  --flavor=woff2 --output-file=MesloLGM-<Regular|Bold>.woff2
```

Итог — около 22 КБ на начертание. Курсивные начертания интерфейс не использует,
поэтому в комплект не входят.

Лицензия — Apache License 2.0, © 2009, 2010, 2013 André Berg; полный текст в
[`LICENSE.txt`](LICENSE.txt).
