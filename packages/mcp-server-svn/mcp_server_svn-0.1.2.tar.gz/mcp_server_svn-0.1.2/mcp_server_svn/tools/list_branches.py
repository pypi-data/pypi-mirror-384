"""SVN list branches and tags tool for MCP server."""

import subprocess


def svn_list_branches(repo_url: str) -> dict:
    """
    List all branches and tags in the remote repository.

    Args:
        repo_url (str): Base URL of repository (e.g. ends with '/myrepo').

    Returns:
        dict: {"branches": [...], "tags": [...], "error": str}
    """
    branches_url = repo_url.rstrip("/") + "/branches"
    tags_url = repo_url.rstrip("/") + "/tags"
    try:
        branches_result = subprocess.run(
            ["svn", "list", branches_url],
            capture_output=True,
            text=True,
            check=False,
        )
        tags_result = subprocess.run(
            ["svn", "list", tags_url],
            capture_output=True,
            text=True,
            check=False,
        )

        branches = (
            [line.strip("/").strip() for line in branches_result.stdout.splitlines() if line.strip()]
            if branches_result.returncode == 0 else []
        )
        tags = (
            [line.strip("/").strip() for line in tags_result.stdout.splitlines() if line.strip()]
            if tags_result.returncode == 0 else []
        )
        error = ""
        if branches_result.returncode != 0 or tags_result.returncode != 0:
            error = "Branches: " + (branches_result.stderr.strip() or "ok")
            error += " | Tags: " + (tags_result.stderr.strip() or "ok")
        return {"branches": branches, "tags": tags, "error": error}
    except Exception as e:
        return {"branches": [], "tags": [], "error": str(e)}
