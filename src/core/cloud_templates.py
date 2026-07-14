"""Cloud templates - download community templates from GitHub."""

import os
import json
import logging
import urllib.request

logger = logging.getLogger("MarkdownToPDF.cloud_templates")

# Community templates repository (GitHub raw URLs)
TEMPLATE_REPO = "https://raw.githubusercontent.com"
TEMPLATE_INDEX_URL = f"{TEMPLATE_REPO}/user-templates/md2pdf/main/templates.json"

LOCAL_TEMPLATES_DIR = os.path.join(
    os.environ.get('APPDATA', os.path.expanduser('~')),
    'MarkdownToPDF_Pro', 'cloud_templates'
)


def get_cloud_templates_index(lang='ru'):
    """
    Fetch available cloud templates index.
    Returns list of dicts: [{name, url, description, tags}]
    """
    # Built-in fallback templates
    fallback = [
        {
            "name": "📝 README Template",
            "url": "",
            "description": "Standard README.md template with badges, sections, and examples",
            "tags": ["readme", "documentation"],
            "builtin": True,
            "content": """# Project Name

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Description

A brief description of what this project does and its purpose.

## Installation

```bash
pip install project-name
```

## Usage

```python
from project_name import main
main.run()
```

## Features

- Feature 1
- Feature 2
- Feature 3

## Configuration

| Variable | Description | Default |
|:---------|:------------|:--------|
| `DEBUG`  | Debug mode  | `false` |
| `PORT`   | Server port | `8080`  |

## Contributing

1. Fork the repository
2. Create your feature branch
3. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.
"""
        },
        {
            "name": "📊 Technical Spec",
            "url": "",
            "description": "Technical specification document template",
            "tags": ["spec", "technical"],
            "builtin": True,
            "content": """---
title: "Technical Specification: [Feature Name]"
author: "[Team/Author]"
date: "[Date]"
---

# Technical Specification: [Feature Name]

## 1. Overview

### 1.1 Purpose
Describe the purpose of this feature.

### 1.2 Scope
Define what is in and out of scope.

## 2. Requirements

### 2.1 Functional Requirements
- [ ] Requirement 1
- [ ] Requirement 2

### 2.2 Non-Functional Requirements
- Performance: < 200ms response time
- Availability: 99.9% uptime
- Security: OWASP Top 10 compliance

## 3. Architecture

### 3.1 System Design
```
[Client] → [API Gateway] → [Service] → [Database]
```

### 3.2 Data Model
```sql
CREATE TABLE features (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 4. API Design

### Endpoints
| Method | Path | Description |
|:-------|:-----|:------------|
| GET | `/api/features` | List features |
| POST | `/api/features` | Create feature |

## 5. Testing Strategy

- Unit tests: > 80% coverage
- Integration tests: All API endpoints
- Load tests: 1000 concurrent users

## 6. Timeline

| Phase | Duration | Deliverable |
|:------|:---------|:------------|
| Design | 1 week | This document |
| Implementation | 2 weeks | Working feature |
| Testing | 1 week | Test report |
| Deployment | 1 day | Production release |
"""
        },
        {
            "name": "📋 Meeting Notes",
            "url": "",
            "description": "Meeting notes template with action items",
            "tags": ["meeting", "notes"],
            "builtin": True,
            "content": """---
title: "Meeting Notes: [Topic]"
date: "[Date]"
participants: "[Names]"
---

# Meeting Notes: [Topic]

**Date:** [Date]  
**Time:** [Start] - [End]  
**Participants:** [Names]

## Agenda

1. [Topic 1]
2. [Topic 2]
3. [Topic 3]

## Discussion

### [Topic 1]
- Key points discussed
- Decisions made

### [Topic 2]
- Key points discussed
- Decisions made

## Action Items

| # | Action | Owner | Due Date | Status |
|:-:|:-------|:------|:---------|:-------|
| 1 | [Action 1] | [Name] | [Date] | ⬜ |
| 2 | [Action 2] | [Name] | [Date] | ⬜ |

## Next Meeting

- **Date:** [Date]
- **Topics to discuss:** [Topics]
"""
        },
    ]

    try:
        req = urllib.request.Request(TEMPLATE_INDEX_URL, method='GET')
        req.add_header('User-Agent', 'MarkdownToPDF/1.0')
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return data.get('templates', fallback)
    except Exception as e:
        logger.info("Cloud templates unavailable, using built-in: %s", e)
        return fallback


def _is_safe_template_url(url: str) -> bool:
    """Allow only known template repositories (SSRF protection)."""
    allowed_prefixes = (
        "https://raw.githubusercontent.com/",
        "https://github.com/",
    )
    return url.startswith(allowed_prefixes)


def download_template(url):
    """Download template content from URL."""
    if not _is_safe_template_url(url):
        logger.error("Blocked unsafe template URL: %s", url)
        return None
    try:
        req = urllib.request.Request(url, method='GET')
        req.add_header('User-Agent', 'MarkdownToPDF/1.0')
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode('utf-8')
    except Exception as e:
        logger.error("Failed to download template: %s", e)
        return None


def save_local_template(name, content):
    """Save a template locally."""
    os.makedirs(LOCAL_TEMPLATES_DIR, exist_ok=True)
    safe_name = name.replace('/', '_').replace('\\', '_')[:50]
    path = os.path.join(LOCAL_TEMPLATES_DIR, f"{safe_name}.md")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return path


def get_local_templates():
    """Get list of locally saved templates."""
    if not os.path.exists(LOCAL_TEMPLATES_DIR):
        return []
    templates = []
    for f in os.listdir(LOCAL_TEMPLATES_DIR):
        if f.endswith('.md'):
            path = os.path.join(LOCAL_TEMPLATES_DIR, f)
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read()
            templates.append({'name': f[:-3], 'content': content, 'path': path})
    return templates
