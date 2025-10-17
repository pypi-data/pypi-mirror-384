"""SVN add tool implementation for MCP server."""

import subprocess
import os


def svn_add(repo_path, target):
    """
    Run 'svn add' for a target inside the given repository path.

    Args:
        repo_path (str): Path to the SVN working copy.
        target (str): Path (file or directory, relative or absolute).

    Returns:
        dict: Dictionary with 'output' (str) and 'error' (str, optional).
    """
    full_target = os.path.join(repo_path, target)
    try:
        result = subprocess.run(
            ["svn", "add", full_target],
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
