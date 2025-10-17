"""SVN switch tool implementation for MCP server."""

import subprocess


def svn_switch(repo_path: str, url: str) -> dict:
    """
    Switch the working copy at repo_path to the branch/tag at url.

    Args:
        repo_path (str): Path to the working copy.
        url (str): URL of the branch/tag.

    Returns:
        dict: Dictionary with 'output' (str) and 'error' (str).
    """
    try:
        result = subprocess.run(
            ["svn", "switch", url, repo_path],
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "output": result.stdout.strip(),
            "error": result.stderr.strip() if result.stderr else ""
        }
    except Exception as e:
        return {"output": "", "error": str(e)}
