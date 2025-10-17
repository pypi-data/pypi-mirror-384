"""SVN log tool implementation for MCP server."""

import subprocess


def svn_log(repo_path, limit=None):
    """
    Run 'svn log' on the given repository path.

    Args:
        repo_path (str): Path to the SVN working copy or repository.
        limit (int, optional): Max number of log entries; if None, unlimited.

    Returns:
        dict: Dictionary with 'log' (str) and 'error' (str, optional).
    """
    cmd = ["svn", "log", repo_path]
    if limit:
        cmd += ["--limit", str(limit)]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        # Determine branch/tag via svn info
        branch_or_tag = ""
        try:
            info_result = subprocess.run(
                ["svn", "info", repo_path],
                capture_output=True,
                text=True,
                check=False,
            )
            if info_result.returncode == 0:
                for line in info_result.stdout.splitlines():
                    if line.startswith("Relative URL:"):
                        branch_or_tag = line.replace("Relative URL:", "").strip()
                        break
        except Exception:
            pass
        return {
            "log": result.stdout,
            "error": result.stderr.strip() if result.stderr else "",
            "branch_or_tag": branch_or_tag
        }
    except Exception as e:
        return {"log": "", "error": str(e), "branch_or_tag": ""}
