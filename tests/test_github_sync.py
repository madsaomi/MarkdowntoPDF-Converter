"""Тесты github_sync (PLAN-005/TASK-005).

Только операции ЧТЕНИЯ — ничего не коммитится и не пушится.
Проверяются happy-path на реальном репозитории проекта и graceful-деградация
на несуществующем пути.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import github_sync as gs

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_is_git_repo_true():
    """Каталог проекта распознаётся как git-репозиторий."""
    assert gs.is_git_repo(REPO) is True
    print("[PASS] test_is_git_repo_true")


def test_is_git_repo_false():
    """Несуществующий путь не является репозиторием и не бросает исключение."""
    assert gs.is_git_repo(os.path.join(REPO, "no_such_dir", "deeper")) is False
    print("[PASS] test_is_git_repo_false")


def test_git_status_shape():
    """git_status возвращает словарь с ожидаемыми ключами."""
    status = gs.git_status(REPO)
    for key in ("staged", "modified", "untracked", "raw"):
        assert key in status, f"Нет ключа {key}"
        assert isinstance(status[key], list)
    print("[PASS] test_git_status_shape")


def test_git_status_on_bad_path_is_safe():
    """На не-git пути возвращается безопасный словарь (с error либо пустыми списками)."""
    status = gs.git_status(os.path.join(REPO, "definitely_missing"))
    assert status["staged"] == []
    assert status["modified"] == []
    assert status["untracked"] == []
    print("[PASS] test_git_status_on_bad_path_is_safe")


def test_git_log_returns_commits():
    """git_log отдаёт разобранные коммиты (hash/message/date/author)."""
    commits = gs.git_log(REPO, count=3)
    assert len(commits) >= 1, "Ожидался хотя бы один коммит"
    c = commits[0]
    assert set(("hash", "message", "date", "author")).issubset(c.keys())
    assert len(c["hash"]) == 8, f"hash должен быть укорочен до 8 символов: {c['hash']}"
    print(f"[PASS] test_git_log_returns_commits: {len(commits)} коммитов")


def test_git_branch_list():
    """git_branch_list возвращает список веток и текущую."""
    info = gs.git_branch_list(REPO)
    assert info["success"] is True
    assert isinstance(info["branches"], list) and info["branches"]
    assert info["current"], "Текущая ветка не определена"
    print(f"[PASS] test_git_branch_list: current={info['current']}")


def test_git_file_history_readme():
    """История файла у README непуста, если README отслеживается."""
    readme = "README.md"
    if not os.path.exists(os.path.join(REPO, readme)):
        print("[SKIP] README.md отсутствует")
        return
    history = gs.git_file_history(REPO, readme, count=5)
    for entry in history:
        assert len(entry["hash"]) == 8
    print(f"[PASS] test_git_file_history_readme: {len(history)} записей")


def test_git_tags_returns_list():
    """git_tags всегда возвращает список (возможно пустой)."""
    tags = gs.git_tags(REPO)
    assert isinstance(tags, list)
    print(f"[PASS] test_git_tags_returns_list: {len(tags)} тегов")


def test_git_diff_between_commits():
    """git_diff_commits между HEAD и HEAD~0 не падает."""
    commits = gs.git_log(REPO, count=1)
    if not commits:
        print("[SKIP] нет коммитов")
        return
    h = commits[0]["hash"]
    result = gs.git_diff_commits(REPO, h, h)
    assert result["success"] is True
    print("[PASS] test_git_diff_between_commits")


def main():
    tests = [
        test_is_git_repo_true,
        test_is_git_repo_false,
        test_git_status_shape,
        test_git_status_on_bad_path_is_safe,
        test_git_log_returns_commits,
        test_git_branch_list,
        test_git_file_history_readme,
        test_git_tags_returns_list,
        test_git_diff_between_commits,
    ]
    for t in tests:
        t()
    print("\nAll github sync tests passed!")


if __name__ == "__main__":
    main()
