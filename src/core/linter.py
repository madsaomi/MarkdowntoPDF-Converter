"""Markdown linter - checks for common style and syntax issues."""

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger("MarkdownToPDF.linter")


@dataclass
class LintIssue:
    line: int
    column: int
    severity: str  # 'error', 'warning', 'info'
    rule: str
    message: str


def lint_markdown(text: str, lang: str = 'ru') -> list:
    """
    Analyzes Markdown text and returns a list of LintIssue objects.
    Checks for common issues: style, formatting, readability.
    """
    issues = []
    lines = text.split('\n')

    in_code_block = False
    prev_line = ''
    prev_was_empty = False
    heading_count = 0

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()

        # Track code blocks
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # H1 should only be used once (title)
        if re.match(r'^# [^#]', line):
            heading_count += 1
            if heading_count > 1:
                issues.append(LintIssue(idx, 1, 'warning', 'multiple-h1',
                    'Используйте H2+ для подзаголовков (H1 только для заголовка)' if lang == 'ru'
                    else 'Use H2+ for subheadings (H1 only for title)'))

        # No empty line before heading
        if re.match(r'^#{1,6}\s', line) and prev_line and not prev_was_empty:
            issues.append(LintIssue(idx, 1, 'info', 'heading-blank-before',
                'Добавьте пустую строку перед заголовком' if lang == 'ru'
                else 'Add blank line before heading'))

        # Trailing whitespace
        if line.rstrip() != line and line.strip():
            issues.append(LintIssue(idx, len(line.rstrip()), 'warning', 'trailing-whitespace',
                'Лишние пробелы в конце строки' if lang == 'ru'
                else 'Trailing whitespace'))

        # Multiple blank lines
        if not stripped and prev_was_empty:
            issues.append(LintIssue(idx, 1, 'info', 'multiple-blanks',
                'Несколько пустых строк подряд' if lang == 'ru'
                else 'Multiple consecutive blank lines'))

        # Line length > 120
        if len(line) > 120:
            issues.append(LintIssue(idx, 120, 'info', 'line-length',
                f'Строка длиннее 120 символов ({len(line)})' if lang == 'ru'
                else f'Line longer than 120 chars ({len(line)})'))

        # Bold/italic spacing: *word* is OK, but ** word ** is not
        if re.search(r'\*\*\s+\S', line) or re.search(r'\S\s+\*\*', line):
            issues.append(LintIssue(idx, 1, 'warning', 'bold-spacing',
                'Пробелы вокруг ** некорректны' if lang == 'ru'
                else 'Incorrect spacing around **'))

        # Inconsistent list markers (- vs * vs +)
        if re.match(r'^[-*+]\s', stripped):
            marker = stripped[0]
            if marker != '-' and idx > 1:
                for prev in reversed(lines[:idx-1]):
                    prev_s = prev.strip()
                    if re.match(r'^[-*+]\s', prev_s) and prev_s[0] != marker:
                        issues.append(LintIssue(idx, 1, 'info', 'inconsistent-list-marker',
                            f'Непоследовательный маркер списка: "{marker}" (ожидается "-")' if lang == 'ru'
                            else f'Inconsistent list marker: "{marker}" (expected "-")'))
                        break

        # Empty link text [text]() but href is empty
        if re.search(r'\[([^\]]*)\]\(\s*\)', line):
            issues.append(LintIssue(idx, 1, 'warning', 'empty-link',
                'Пустая ссылка' if lang == 'ru'
                else 'Empty link href'))

        # TODO/FIXME/HACK comments
        todo_match = re.search(r'(TODO|FIXME|HACK|XXX)', line, re.IGNORECASE)
        if todo_match:
            issues.append(LintIssue(idx, line.index(todo_match.group()) + 1, 'info', 'todo-comment',
                f'Найден комментарий: {todo_match.group()}' if lang == 'ru'
                else f'Todo comment found: {todo_match.group()}'))

        # Image without alt text: ![](url)
        if re.search(r'!\[\]\(', line):
            issues.append(LintIssue(idx, 1, 'warning', 'image-no-alt',
                'У изображения нет alt-текста' if lang == 'ru'
                else 'Image has no alt text'))

        prev_was_empty = not stripped
        prev_line = line

    return issues
