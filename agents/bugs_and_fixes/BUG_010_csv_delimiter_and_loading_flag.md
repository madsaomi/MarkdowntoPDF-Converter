# 🐛 Баг: выбор разделителя ломал импорт CSV (и «залипал» флаг загрузки)

**Дата:** 2026-10-21  
**Статус:** ✅ FIXED  
**Затронутые модули:** `src/gui/csv_editor.py` (`CSVEditorDialog._detect_delimiter`, `_load_rows`)

---

## Симптом → Причина

### 1. Любой явный разделитель, кроме «Auto», роняет импорт

- **Симптом:** в диалоге «CSV Table Editor» пользователь выбирает в списке
  `Comma (,)`, `Tab`, `Semicolon (;)` или `Pipe (|)`, жмёт «Import CSV/TSV» —
  и вместо таблицы получает окно **Error**:

  ```
  "delimiter" must be a unicode character, not a string of length 9
  ```

  Работал только режим `Auto`.

- **Причина:** `_detect_delimiter` должен вернуть **символ**-разделитель, а
  возвращал **подпись пункта комбобокса**:

  ```python
  mapping = {"Comma (,)": ",", "\t": "Tab", ";": "Semicolon (;)", "|": "Pipe (|)"}
  return delim          # delim == "Comma (,)", а не ","
  ```

  `mapping` был построен «наоборот» (ключи — символы, значения — подписи) и
  вообще не использовался. Дальше `csv.reader(lines, delimiter="Comma (,)")`
  законно падал с `TypeError`, который ловился общим `except` и показывался
  пользователю как ошибка импорта.

- **Как обнаружено:** при написании поведенческих тестов на импорт
  (PLAN-013, рост покрытия). Проверка «после импорта в таблице 2 колонки»
  упала, потому что вместо данных показывалось сообщение об ошибке.

### 2. Флаг `_loading` оставался взведённым после пустого импорта

- **Симптом:** внешне незаметен (обработчик `_on_cell_changed` сейчас пустой),
  но состояние объекта становилось некорректным: после импорта пустого файла
  или CSV без строк `_loading` навсегда оставался `True`.

- **Причина:** `_load_rows` ставил `self._loading = True`, затем при пустом
  списке делал `return` **до** строки `self._loading = False`.

## Исправление

```python
-        mapping = {"Comma (,)": ",", "\t": "Tab", ";": "Semicolon (;)", "|": "Pipe (|)"}
-        return delim
+        mapping = {
+            "Comma (,)": ",",
+            "Tab": "\t",
+            "Semicolon (;)": ";",
+            "Pipe (|)": "|",
+        }
+        return mapping.get(delim, ",")
```

```python
     def _load_rows(self, rows: list[list[str]]):
         self._loading = True
-        self.table.clearContents()
-        if not rows:
-            return
-        ...
-        self._loading = False
+        try:
+            self.table.clearContents()
+            if not rows:
+                return
+            ...
+        finally:
+            self._loading = False
```

`mapping.get(delim, ",")` сохраняет прежнее поведение для неизвестной подписи
(раньше в этом случае пришёл бы `TypeError`) — теперь используется запятая,
как и в режиме `Auto` по умолчанию.

## Проверка

- `tests/test_coverage_csv_editor.py` (28 проверок), в том числе:
  - `test_detect_delimiter_explicit_returns_single_character` — для всех
    четырёх подписей результат ровно один символ, и `csv.reader` его
    принимает;
  - `test_import_csv_explicit_delimiters_do_not_break` — полный цикл импорта
    файла для каждого разделителя (регрессия на исходный `TypeError`);
  - `test_load_rows_empty_clears_and_resets_flag` — `_loading is False`
    после пустого ввода;
  - остальные тесты: авто-определение, BOM, отмена/ошибка диалога, экспорт
    в Markdown и CSV.
- Покрытие `src/gui/csv_editor.py`: 11 % → **100 %**.

## Правило предотвращения

- **Если функция переводит текст из UI в техническое значение (символ,
  enum, число) — тест обязан проверять тип и длину результата, а не только
  «не упало».** Для разделителя CSV достаточно `len(result) == 1` и реального
  вызова потребителя (`csv.reader`).
- **Ранний `return` внутри блока, который меняет состояние объекта, должен
  быть обёрнут в `try/finally`.** Иначе флаг/счётчик остаётся в промежуточном
  состоянии, и следующий обработчик молча пропускает работу.
