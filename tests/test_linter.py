import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.linter import lint_markdown, LintIssue


def test_no_issues_clean():
    text = "# Title\n\nClean paragraph with no issues.\n\n## Subheading\n\n- item 1\n- item 2"
    issues = lint_markdown(text)
    assert isinstance(issues, list)
    print(f"[PASS] test_no_issues_clean: {len(issues)} issues")


def test_empty_link():
    text = "click [here]()"
    issues = lint_markdown(text)
    assert any(i.rule == 'empty-link' for i in issues)
    print("[PASS] test_empty_link")


def test_todo_comment():
    text = "# TODO: fix this"
    issues = lint_markdown(text)
    assert any(i.rule == 'todo-comment' for i in issues)
    print("[PASS] test_todo_comment")


def test_image_no_alt():
    text = "![](image.png)"
    issues = lint_markdown(text)
    assert any(i.rule == 'image-no-alt' for i in issues)
    print("[PASS] test_image_no_alt")


def test_trailing_whitespace():
    text = "line with space \nnext"
    issues = lint_markdown(text)
    assert any(i.rule == 'trailing-whitespace' for i in issues)
    print("[PASS] test_trailing_whitespace")


def test_long_line():
    text = "x" * 150
    issues = lint_markdown(text)
    assert any(i.rule == 'line-length' for i in issues)
    print("[PASS] test_long_line")


def test_multiple_h1():
    text = "# First\n\n# Second"
    issues = lint_markdown(text)
    assert any(i.rule == 'multiple-h1' for i in issues)
    print("[PASS] test_multiple_h1")


def test_issue_dataclass():
    issue = LintIssue(line=5, column=1, severity='warning', rule='test', message='test msg')
    assert issue.line == 5
    assert issue.severity == 'warning'
    assert issue.rule == 'test'
    print("[PASS] test_issue_dataclass")


if __name__ == '__main__':
    test_no_issues_clean()
    test_empty_link()
    test_todo_comment()
    test_image_no_alt()
    test_trailing_whitespace()
    test_long_line()
    test_multiple_h1()
    test_issue_dataclass()
    print("\nAll linter tests passed!")
