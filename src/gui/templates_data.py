"""Built-in document templates for Markdown to PDF Converter."""

TEMPLATES = {
    "resume": {
        "name": "📄 Резюме / Resume",
        "content": """---
title: "{{name}}"
author: "{{email}}"
---

# {{name}}

**{{email}}** | **{{phone}}** | **{{city}}**

## Опыт работы

### Frontend Developer — Яндекс
*2022 — настоящее время*

- Разработка SPA на React/TypeScript
- Оптимизация производительности (LCP < 2.5s)
- Менторство junior-разработчиков

### Junior Developer — Mail.ru
*2020 — 2022*

- Поддержка и развитие почтового клиента
- Написание unit-тестов (покрытие > 80%)

## Образование

### МГУ им. Ломоносова
*Факультет ВМК, 2016 — 2020*

## Навыки

- **Языки:** Python, JavaScript/TypeScript, Go
- **Фреймворки:** React, Vue, Django, FastAPI
- **Инструменты:** Git, Docker, PostgreSQL, Redis
- **Языки:** Русский (native), English (B2)

## Проекты

- **MarkdownToPDF** — конвертер Markdown в PDF с поддержкой тем и шаблонов
- **WebSight** — платформа для A/B тестирования
""",
    },
    "report": {
        "name": "📊 Отчёт / Report",
        "content": """---
title: "Технический отчёт: Анализ системы"
author: "Отдел разки"
date: "2025"
---

# Технический отчёт: Анализ системы

## Резюме

Настоящий отчёт описывает результаты анализа текущего технического стека и рекомендации по оптимизации.

## Введение

### Цели анализа

1. Оценить производительность текущей системы
2. Выявить узкие места
3. Предложить план оптимизации

### Методология

Анализ проведён с использованием следующих инструментов:
- Profiling (cProfile, py-spy)
- Load testing (Locust)
- Database analysis (pgBadger)

## Результаты

### Производительность API

| Метрика | Значение | Цель |
|:--------|:--------:|:----:|
| Среднее время ответа | 120ms | < 200ms |
| P95 время ответа | 450ms | < 500ms |
| P99 время ответа | 1200ms | < 1000ms |
| RPS | 850 | > 500 |

### Использование ресурсов

```
CPU: 45% (среднее), 78% (пик)
RAM: 2.1 GB / 8 GB
Disk I/O: 120 MB/s
Network: 50 MB/s
```

## Рекомендации

### Краткосрочные (1-2 недели)

- [ ] Оптимизировать N+1 запросы в модуле пользователей
- [ ] Добавить кэширование频繁 используемых запросов
- [ ] Настроить connection pooling

### Среднесрочные (1-3 месяца)

- [ ] Внедрить Redis для кэширования сессий
- [ ] Разделить read/write реплики
- [ ] Оптимизировать индексы в PostgreSQL

## Заключение

Система работает стабильно, но требует оптимизации для масштабирования. Предложенные меры позволят увеличить пропускную способность в 2-3 раза.

---

*Отчёт подготовлен: {{date}}*
""",
    },
    "presentation_notes": {
        "name": "🎯 Заметки к презентации",
        "content": """---
title: "Презентация: Обзор проекта"
author: "Команда разработки"
---

# Обзор проекта MarkdownToPDF

## Слайд 1: Что это?

MarkdownToPDF — это десктопное приложение для конвертации Markdown в PDF, DOCX, EPUB и другие форматы.

**Ключевые возможности:**
- Подсветка синтаксиса кода
- Поддержка диаграмм (Kroki.io)
- Множество тем оформления
- Шифрование PDF

## Слайд 2: Технологии

- **Frontend:** PyQt6
- **Backend:** Python 3.10+
- **PDF:** WeasyPrint
- **MD Parser:** Python-Markdown + pymdown-extensions

## Слайд 3: Архитектура

```
[MD Parser] → [HTML Renderer] → [WeasyPrint] → [PDF/DOCX/EPUB]
     ↓                                    ↓
[Highlighter]                    [Image Export]
     ↓                                    ↓
[Preview Widget]               [PNG/JPG Files]
```

## Слайд 4: Roadmap

1. ✅ Базовая конвертация MD → PDF
2. ✅ Темы и шаблоны
3. ✅ Экспорт в DOCX/EPUB
4. 🔄 Сравнение документов
5. 📋 PPTX экспорт
""",
    },
    "letter": {
        "name": "✉️ Деловое письмо",
        "content": """---
title: "Деловое письмо"
author: "ООО «Компания»"
date: "{{date}}"
---

# Деловое письмо

**От:** ООО «Компания»  
**Кому:** [Получатель]  
**Дата:** {{date}}  
**Тема:** [Тема письма]

---

Уважаемый(-ая) [Имя],

Настоящим письмом сообщаем Вам, что [содержание письма].

### Основные положения

1. [Пункт первый]
2. [Пункт второй]
3. [Пункт третий]

Просим подтвердить получение данного письма в течение **3 рабочих дней**.

С уважением,  
[ФИО]  
Должность  
ООО «Компания»

---

*Контакты: +7 (XXX) XXX-XX-XX | email@company.ru*
""",
    },
    "notes": {
        "name": "📝 Заметки / Notes",
        "content": """---
title: "Мои заметки"
date: "{{date}}"
---

# Заметки

## Встреча команды — {{date}}

### Обсуждаемое

- Sprint planning на следующую неделю
- Ревью PR #247
- Обновление зависимостей

### Решения

- [ ] Согласовать дедлайн по фиче X
- [ ] Назначить ответственного за Y
- [ ] Запланировать code review

---

## Идеи

- Добавить dark mode для PDF
- Интеграция с Notion API
- Автоматические бэкапы

---

## Полезные ссылки

- [Python Docs](https://docs.python.org/3/)
- [PyQt6 Docs](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [WeasyPrint Docs](https://doc.courtbouillon.org/weasyprint/stable/)
""",
    },
}



# ──────────────────────── Pro Templates ────────────────────────

PRO_TEMPLATES = {
    "business_proposal": {
        "name": "💼 Business Proposal",
        "category": "business",
        "content": """---
title: "Business Proposal: {{project_name}}"
author: "{{company}}"
date: "{{date}}"
---

# {{project_name}}

## Executive Summary

{{executive_summary}}

## Problem Statement

{{problem_statement}}

## Proposed Solution

{{proposed_solution}}

## Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Discovery | 2 weeks | Requirements doc |
| Design | 3 weeks | Mockups, prototypes |
| Development | 8 weeks | MVP |
| Testing | 2 weeks | QA report |
| Launch | 1 week | Production deploy |

## Budget

| Item | Cost |
|------|------|
| Development | ${{dev_cost}} |
| Design | ${{design_cost}} |
| Infrastructure | ${{infra_cost}} |
| **Total** | **${{total_cost}}** |

## Team

- **Project Manager:** {{pm_name}}
- **Lead Developer:** {{dev_lead}}
- **Designer:** {{designer_name}}

## Next Steps

1. Review and approve proposal
2. Sign contract
3. Kick-off meeting
""",
    },
    "technical_spec": {
        "name": "🔧 Technical Specification",
        "category": "technical",
        "content": """---
title: "Technical Specification: {{feature_name}}"
version: "1.0"
status: "Draft"
---

# Technical Specification: {{feature_name}}

## Overview

{{overview}}

## Requirements

### Functional Requirements

1. {{fr_1}}
2. {{fr_2}}
3. {{fr_3}}

### Non-Functional Requirements

- **Performance:** {{nfr_performance}}
- **Scalability:** {{nfr_scalability}}
- **Security:** {{nfr_security}}

## Architecture

### Components

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend   │────▶│    API      │────▶│  Database   │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Data Model

```sql
CREATE TABLE {{table_name}} (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## API Design

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/{{resource}} | List all |
| POST | /api/v1/{{resource}} | Create new |
| PUT | /api/v1/{{resource}}/:id | Update |
| DELETE | /api/v1/{{resource}}/:id | Delete |

## Testing Strategy

- Unit tests: 80% coverage
- Integration tests: All API endpoints
- E2E tests: Critical user flows

## Deployment

- CI/CD: GitHub Actions
- Staging: AWS ECS
- Production: AWS ECS with auto-scaling
""",
    },
    "meeting_notes": {
        "name": "📋 Meeting Notes",
        "category": "notes",
        "content": """---
title: "Meeting Notes: {{meeting_title}}"
date: "{{date}}"
time: "{{time}}"
attendees: "{{attendees}}"
---

# {{meeting_title}}

**Date:** {{date}}
**Time:** {{time}}
**Attendees:** {{attendees}}

## Agenda

1. {{agenda_1}}
2. {{agenda_2}}
3. {{agenda_3}}

## Discussion Points

### {{topic_1}}

{{discussion_1}}

### {{topic_2}}

{{discussion_2}}

## Action Items

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| {{action_1}} | {{owner_1}} | {{due_1}} | ⏳ |
| {{action_2}} | {{owner_2}} | {{due_2}} | ⏳ |
| {{action_3}} | {{owner_3}} | {{due_3}} | ⏳ |

## Decisions Made

- {{decision_1}}
- {{decision_2}}

## Next Meeting

**Date:** {{next_meeting_date}}
**Agenda:** {{next_agenda}}
""",
    },
    "blog_post": {
        "name": "✍️ Blog Post",
        "category": "content",
        "content": """---
title: "{{title}}"
author: "{{author}}"
date: "{{date}}"
tags: [{{tags}}]
---

# {{title}}

*Published on {{date}} by {{author}}*

{{introduction}}

## {{section_1_title}}

{{section_1_content}}

## {{section_2_title}}

{{section_2_content}}

## {{section_3_title}}

{{section_3_content}}

## Conclusion

{{conclusion}}

---

**Tags:** {{tags}}

**Share this post:**
- [Twitter](https://twitter.com/intent/tweet?text={{title}})
- [LinkedIn](https://linkedin.com/shareArticle?url={{url}}&title={{title}})
""",
    },
    "api_documentation": {
        "name": "📚 API Documentation",
        "category": "technical",
        "content": """---
title: "API Documentation: {{api_name}}"
version: "v1"
base_url: "{{base_url}}"
---

# {{api_name}} API Documentation

## Base URL

```
{{base_url}}
```

## Authentication

All API requests require authentication via Bearer token:

```
Authorization: Bearer {{api_key}}
```

## Endpoints

### {{endpoint_1_name}}

**{{endpoint_1_method}}** `{{endpoint_1_path}}`

{{endpoint_1_description}}

#### Request

```json
{
    "field1": "value1",
    "field2": "value2"
}
```

#### Response

```json
{
    "status": "success",
    "data": {
        "id": 1,
        "field1": "value1",
        "field2": "value2"
    }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad request |
| 401 | Unauthorized |
| 404 | Not found |
| 500 | Server error |

## Rate Limiting

- **Free tier:** 100 requests/hour
- **Pro tier:** 1000 requests/hour
- **Enterprise:** Unlimited

## Changelog

### v1.0.0 ({{date}})
- Initial release
- Basic CRUD operations
""",
    },
}


def get_pro_template_list():
    """Returns list of (key, name, category) tuples for Pro templates."""
    return [(key, tmpl["name"], tmpl["category"]) for key, tmpl in PRO_TEMPLATES.items()]


def get_pro_template_content(key):
    """Returns Pro template content for the given key."""
    tmpl = PRO_TEMPLATES.get(key)
    return tmpl["content"] if tmpl else None


def get_template_list():
    """Returns list of (key, name) tuples for template selection."""
    return [(key, tmpl["name"]) for key, tmpl in TEMPLATES.items()]


def get_template_content(key):
    """Returns template content for the given key."""
    tmpl = TEMPLATES.get(key)
    return tmpl["content"] if tmpl else None
