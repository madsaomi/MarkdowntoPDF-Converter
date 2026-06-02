import logging
import os
import subprocess

logger = logging.getLogger("MarkdownToPDF.github_sync")


def is_git_repo(path: str) -> bool:
    """Check if path is inside a git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=path, capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def git_status(repo_path: str) -> dict:
    """Return git status as dict with staged, modified, untracked lists."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip().splitlines() if result.stdout.strip() else []
        staged, modified, untracked = [], [], []
        for line in lines:
            status = line[:2].strip()
            filepath = line[3:]
            if status == "??":
                untracked.append(filepath)
            elif status[0] in ("A", "M", "D"):
                staged.append(filepath)
            else:
                modified.append(filepath)
        return {"staged": staged, "modified": modified, "untracked": untracked, "raw": lines}
    except Exception as e:
        logger.error("git status failed: %s", e)
        return {"staged": [], "modified": [], "untracked": [], "raw": [], "error": str(e)}


def git_commit(repo_path: str, message: str, files: list[str] = None) -> dict:
    """Stage files and commit. If files is None, stages all."""
    try:
        if files:
            for f in files:
                subprocess.run(["git", "add", f], cwd=repo_path, capture_output=True, timeout=10)
        else:
            subprocess.run(["git", "add", "-A"], cwd=repo_path, capture_output=True, timeout=10)

        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        return {"success": result.returncode == 0, "output": result.stdout.strip(), "error": result.stderr.strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def git_push(repo_path: str, remote: str = "origin", branch: str = None) -> dict:
    """Push to remote. Auto-detects current branch if not specified."""
    try:
        if not branch:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=repo_path, capture_output=True, text=True, timeout=5
            )
            branch = result.stdout.strip() or "main"

        result = subprocess.run(
            ["git", "push", remote, branch],
            cwd=repo_path, capture_output=True, text=True, timeout=30
        )
        return {"success": result.returncode == 0, "output": result.stdout.strip(), "error": result.stderr.strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def git_pull(repo_path: str, remote: str = "origin", branch: str = None) -> dict:
    """Pull from remote."""
    try:
        if not branch:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=repo_path, capture_output=True, text=True, timeout=5
            )
            branch = result.stdout.strip() or "main"

        result = subprocess.run(
            ["git", "pull", remote, branch],
            cwd=repo_path, capture_output=True, text=True, timeout=30
        )
        return {"success": result.returncode == 0, "output": result.stdout.strip(), "error": result.stderr.strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def git_log(repo_path: str, count: int = 10) -> list[dict]:
    """Return last N commits as list of dicts."""
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={count}", "--pretty=format:%H|%s|%ai|%an"],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        commits = []
        for line in result.stdout.strip().splitlines():
            parts = line.split("|", 3)
            if len(parts) >= 4:
                commits.append({
                    "hash": parts[0][:8],
                    "message": parts[1],
                    "date": parts[2],
                    "author": parts[3],
                })
        return commits
    except Exception:
        return []


def git_init(repo_path: str) -> dict:
    """Initialize a new git repository."""
    try:
        result = subprocess.run(
            ["git", "init"], cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        return {"success": result.returncode == 0, "output": result.stdout.strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ──────────────────────── Advanced Git Operations ────────────────────────

def git_diff(repo_path: str, file_path: str = None, staged: bool = False) -> dict:
    """Get diff of changes."""
    try:
        cmd = ["git", "diff"]
        if staged:
            cmd.append("--staged")
        if file_path:
            cmd.append(file_path)
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=10)
        return {"success": True, "diff": result.stdout, "error": result.stderr}
    except Exception as e:
        return {"success": False, "diff": "", "error": str(e)}


def git_diff_commits(repo_path: str, commit1: str, commit2: str) -> dict:
    """Get diff between two commits."""
    try:
        result = subprocess.run(
            ["git", "diff", commit1, commit2],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        return {"success": True, "diff": result.stdout, "error": result.stderr}
    except Exception as e:
        return {"success": False, "diff": "", "error": str(e)}


def git_branch_list(repo_path: str) -> dict:
    """List all branches."""
    try:
        result = subprocess.run(
            ["git", "branch", "-a"],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        branches = []
        current = ""
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if line.startswith("* "):
                current = line[2:]
                branches.append(current)
            elif line:
                branches.append(line.replace("remotes/", ""))
        return {"success": True, "branches": branches, "current": current}
    except Exception as e:
        return {"success": False, "branches": [], "current": "", "error": str(e)}


def git_branch_create(repo_path: str, branch_name: str) -> dict:
    """Create a new branch."""
    try:
        result = subprocess.run(
            ["git", "branch", branch_name],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        return {"success": result.returncode == 0, "output": result.stdout.strip(), "error": result.stderr.strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def git_branch_switch(repo_path: str, branch_name: str) -> dict:
    """Switch to a branch."""
    try:
        result = subprocess.run(
            ["git", "checkout", branch_name],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        return {"success": result.returncode == 0, "output": result.stdout.strip(), "error": result.stderr.strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def git_stash(repo_path: str) -> dict:
    """Stash current changes."""
    try:
        result = subprocess.run(
            ["git", "stash"],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        return {"success": result.returncode == 0, "output": result.stdout.strip(), "error": result.stderr.strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def git_stash_pop(repo_path: str) -> dict:
    """Pop the latest stash."""
    try:
        result = subprocess.run(
            ["git", "stash", "pop"],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        return {"success": result.returncode == 0, "output": result.stdout.strip(), "error": result.stderr.strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def git_blame(repo_path: str, file_path: str) -> dict:
    """Get blame info for a file."""
    try:
        result = subprocess.run(
            ["git", "blame", "--porcelain", file_path],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        return {"success": True, "blame": result.stdout, "error": result.stderr}
    except Exception as e:
        return {"success": False, "blame": "", "error": str(e)}


def git_tag(repo_path: str, tag_name: str, message: str = "") -> dict:
    """Create a tag."""
    try:
        cmd = ["git", "tag", "-a", tag_name]
        if message:
            cmd.extend(["-m", message])
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=10)
        return {"success": result.returncode == 0, "output": result.stdout.strip(), "error": result.stderr.strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def git_tags(repo_path: str) -> list[str]:
    """List all tags."""
    try:
        result = subprocess.run(
            ["git", "tag", "-l"],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip().splitlines() if result.stdout.strip() else []
    except Exception:
        return []


def git_file_history(repo_path: str, file_path: str, count: int = 10) -> list[dict]:
    """Get commit history for a specific file."""
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={count}", "--pretty=format:%H|%s|%ai|%an", "--", file_path],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        commits = []
        for line in result.stdout.strip().splitlines():
            parts = line.split("|", 3)
            if len(parts) >= 4:
                commits.append({
                    "hash": parts[0][:8],
                    "message": parts[1],
                    "date": parts[2],
                    "author": parts[3],
                })
        return commits
    except Exception:
        return []
