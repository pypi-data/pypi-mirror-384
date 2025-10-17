"""SVN cleanup tool implementation for MCP server."""

import subprocess

def svn_cleanup(repo_path):
    """
    Run 'svn cleanup' on the given repository path.

    Args:
        repo_path (str): Path to the SVN working copy.

    Returns:
        dict: Dictionary with 'output' (str) and 'error' (str, optional).
    """
    cmd = ["svn", "cleanup", repo_path]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        output = result.stdout.strip()
        error = result.stderr.strip() if result.stderr else ""

        return {
            "output": output,
            "error": error
        }
    except Exception as e:
        return {"output": "", "error": str(e)}
