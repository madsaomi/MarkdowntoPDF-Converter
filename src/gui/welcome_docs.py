# -*- coding: utf-8 -*-

WELCOME_RU = """# Добро пожаловать в Markdown → PDF Converter Pro! 🚀

Это профессиональный инструмент для создания превосходно оформленных документов, отчетов и книг из обычного Markdown.

Ниже приведена интерактивная демонстрация всех продвинутых возможностей, которые вы можете использовать прямо сейчас. Попробуйте отредактировать этот текст слева и посмотрите на результат в превью справа!

---

## 🎨 Продвинутое форматирование

### 1. Блоки внимания (Admonitions)
Используйте информационные блоки для выделения ключевых моментов:

!!! note "Интересный факт"
    Вы можете быстро сохранять все настройки в **Пресеты** в левой панели, чтобы переключаться между ними в один клик! 💾

!!! warning "Внимание"
    Не забудьте настроить **Поля страницы (Margins)**, если вам нужны нестандартные отступы при печати.

!!! danger "Критически важно"
    При экспорте конфиденциальных отчетов вы можете задать **Пароль для PDF** в настройках для защиты ваших данных. 🔒

---

### 2. Сворачиваемые блоки (Details)
Скрывайте большие объемы информации под спойлерами:

???+ note "Показать технические подробности"
    Это приложение использует связку **PyQt6**, **WeasyPrint** (для великолепного HTML/CSS рендеринга PDF) и **python-docx** (для идеального экспорта в Word).

---

### 3. Сноски и микро-оформление
- Поддерживаются автоматические сноски[^1].
- Вы можете выделять текст ==маркером== для привлечения внимания.
- Используйте ^надстрочный индекс^ для математических обозначений или сокращений (например, 1-й^ класс).
- Отображайте клавиши клавиатуры в красивом виде: ++ctrl+shift+p++ или ++alt+f4++.

[^1]: Это текст сноски, который автоматически переместится в самый низ страницы при экспорте в PDF!

---

## 📊 Таблицы и Списки задач

| Компонент | Поддержка PDF | Поддержка DOCX | Интерактивный Live-режим |
| :--- | :---: | :---: | :---: |
| **Markdown Парсинг** | ✅ Да | ✅ Да | ✅ Да |
| **Кастомные Стили** | ✅ CSS | ✅ Шаблоны | ✅ Да |
| **Защита паролем** | ✅ Да | ❌ Нет | — |

- [x] Реализовать живой редактор с автообновлением
- [x] Добавить менеджер пресетов
- [x] Подготовить мультиязычный интерфейс
- [ ] Экспортировать свой первый документ!

---

## 💻 Подсветка исходного кода

Приложение автоматически подсвечивает синтаксис более 300 языков программирования с поддержкой светлых и темных тем:

```python
def generate_pdf(input_md, output_pdf, password=None):
    # Pro-level PDF generation script
    parser = MarkdownParser()
    html, meta = parser.parse(input_md)
    
    renderer = PDFRenderer()
    renderer.render(html, meta, output_pdf)
    
    if password:
        encrypt_pdf(output_pdf, password)
    print("Успешно сконвертировано! 🎉")
```

---

## ⚡ Что делать дальше?
1. Настройте параметры в левой панели (например, измените размер бумаги на **A5** или введите **Водяной знак**).
2. Нажмите кнопку **⚡ Конвертировать в PDF** внизу.
3. Сохраните и откройте готовый файл — вы будете поражены профессиональным качеством верстки!
"""

WELCOME_EN = """# Welcome to Markdown → PDF Converter Pro! 🚀

This is a professional desktop application for creating stunningly formatted documents, reports, and books from plain Markdown.

Below is an interactive showcase of the advanced formatting capabilities supported by our parsing engine. Feel free to edit the text on the left and see the real-time preview update on the right!

---

## 🎨 Advanced Formatting Showcase

### 1. Admonitions (Callout Blocks)
Highlight key points, tips, or warnings with stylized note blocks:

!!! note "Pro Tip"
    You can easily save all your custom settings into **Presets** on the left panel to load them later with a single click! 💾

!!! warning "Page Setup"
    Adjust the **PDF Margins** field if you need custom spacing for headers, footers, or book binding.

!!! danger "Data Security"
    Exporting sensitive information? Set a **PDF Password** in the settings panel to secure your file. 🔒

---

### 2. Collapsible Details Blocks
Hide large technical specifications or secondary data under an interactive spoiler:

???+ note "Show Technical Details"
    This application utilizes **PyQt6** for GUI, **WeasyPrint** for beautiful, CSS-compliant HTML-to-PDF rendering, and **python-docx** for structured Word export.

---

### 3. Footnotes & Micro-formatting
- Add automated document footnotes easily[^1].
- Highlight ==important text== with an inline yellow marker.
- Write ^superscripts^ for formulas or indices (e.g., E = mc^2^).
- Show beautiful keyboard shortcuts like ++ctrl+shift+p++ or ++cmd+option+esc++.

[^1]: This is the footnote text. It will be automatically placed at the very bottom of the page when exported to PDF!

---

## 📊 Tables & Task Lists

| Component | PDF Support | DOCX Support | Live Editor Sync |
| :--- | :---: | :---: | :---: |
| **Markdown Parsing** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Custom Styling** | ✅ CSS | ✅ Templates | ✅ Yes |
| **Password Security** | ✅ Yes | ❌ No | — |

- [x] Build live splitter preview editor
- [x] Add dynamic settings presets manager
- [x] Implement multi-language dynamic i18n support
- [ ] Export your very first pro document!

---

## 💻 Code Syntax Highlighting

The app automatically styles code for 300+ programming languages with light and dark theme alternatives:

```python
def generate_pdf(input_md, output_pdf, password=None):
    # Pro-level PDF generation script
    parser = MarkdownParser()
    html, meta = parser.parse(input_md)
    
    renderer = PDFRenderer()
    renderer.render(html, meta, output_pdf)
    
    if password:
        encrypt_pdf(output_pdf, password)
    print("Successfully converted! 🎉")
```

---

## ⚡ What to do next?
1. Fine-tune your document settings on the left (e.g. choose paper size **A5** or add a **Watermark**).
2. Click the **⚡ Convert to PDF** button below.
3. Save and open the generated file — enjoy the publishing-grade typography!
"""
