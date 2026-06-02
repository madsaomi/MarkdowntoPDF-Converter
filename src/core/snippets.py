"""Code snippets library - save and reuse code blocks."""

import os
import json
import logging
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("MarkdownToPDF.snippets")

SNIPPETS_FILE = os.path.join(
    os.environ.get('APPDATA', os.path.expanduser('~')),
    'MarkdownToPDF_Pro', 'snippets.json'
)


@dataclass
class Snippet:
    name: str
    language: str
    code: str
    tags: list = field(default_factory=list)


class SnippetLibrary:
    def __init__(self):
        self.snippets: list = []
        self._load()

    def _load(self):
        if os.path.exists(SNIPPETS_FILE):
            try:
                with open(SNIPPETS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.snippets = [Snippet(**s) for s in data]
            except Exception as e:
                logger.warning("Failed to load snippets: %s", e)
                self.snippets = []
        else:
            self._add_defaults()

    def _save(self):
        os.makedirs(os.path.dirname(SNIPPETS_FILE), exist_ok=True)
        with open(SNIPPETS_FILE, 'w', encoding='utf-8') as f:
            json.dump([asdict(s) for s in self.snippets], f, ensure_ascii=False, indent=2)

    def _add_defaults(self):
        self.snippets = [
            Snippet("Python function", "python", "def function_name(param):\n    \"\"\"Docstring.\"\"\"\n    pass"),
            Snippet("Python class", "python", "class ClassName:\n    def __init__(self):\n        pass"),
            Snippet("JavaScript function", "javascript", "function functionName(params) {\n    // body\n}"),
            Snippet("HTML template", "html", "<!DOCTYPE html>\n<html>\n<head>\n    <title></title>\n</head>\n<body>\n    \n</body>\n</html>"),
            Snippet("SQL SELECT", "sql", "SELECT column1, column2\nFROM table_name\nWHERE condition\nORDER BY column1;"),
            Snippet("Bash script", "bash", "#!/bin/bash\nset -e\n\necho \"Hello, World!\""),
            Snippet("Markdown table", "markdown", "| Column 1 | Column 2 | Column 3 |\n|:---------|:--------:|--------:|\n| Left     | Center   | Right   |"),
            Snippet("Callout / Admonition", "markdown", "!!! note \"Title\"\n    Content here"),
        ]
        self._save()

    def add(self, name: str, language: str, code: str, tags: list = None):
        self.snippets.append(Snippet(name, language, code, tags or []))
        self._save()

    def remove(self, index: int):
        if 0 <= index < len(self.snippets):
            self.snippets.pop(index)
            self._save()

    def get_all(self):
        return self.snippets
