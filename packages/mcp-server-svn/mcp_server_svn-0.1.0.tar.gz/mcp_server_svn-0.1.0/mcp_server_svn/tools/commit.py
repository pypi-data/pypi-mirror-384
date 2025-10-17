"""SVN commit tool implementation for MCP server."""

import subprocess


def svn_commit(repo_path, message):
    """
    Run 'svn commit' on the given repository path with the provided message.

    Args:
        repo_path (str): Path to the SVN working copy or repository.
        message (str): Commit message.

    Returns:
        dict: Dictionary with 'output' (str) and 'error' (str, optional).
    """
    try:
        result = subprocess.run(
            ["svn", "commit", repo_path, "-m", message],
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "output": result.stdout,
            "error": result.stderr.strip() if result.stderr else ""
        }
    except Exception as e:
        return {"output": "", "error": str(e)}
