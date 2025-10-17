"""SVN update tool implementation for MCP server."""

import subprocess


def svn_update(repo_path):
    """
    Run 'svn update' on the given repository path.

    Args:
        repo_path (str): Path to the SVN working copy or repository.

    Returns:
        dict: Dictionary with 'output' (str) and 'error' (str, optional).
    """
    try:
        result = subprocess.run(
            ["svn", "update", repo_path],
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
