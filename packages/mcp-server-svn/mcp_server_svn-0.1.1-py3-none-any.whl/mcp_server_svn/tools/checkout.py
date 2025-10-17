"""SVN checkout tool implementation for MCP server."""

import subprocess


def svn_checkout(url, target_path=None):
    """
    Run 'svn checkout' for the given repository URL, optionally to a target path.

    Args:
        url (str): SVN repository URL ("file://", "svn://", or "http(s)://").
        target_path (str, optional): Target directory to checkout to.

    Returns:
        dict: Dictionary with 'output' (str) and 'error' (str, optional).
    """
    cmd = ["svn", "checkout", url]
    if target_path:
        cmd.append(target_path)
    try:
        result = subprocess.run(
            cmd,
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
