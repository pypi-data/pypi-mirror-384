"""SVN version tool implementation for MCP server."""

import subprocess

def svn_version():
    """
    Return the installed SVN client version.

    Returns:
        dict: Dictionary with 'version' (str) and 'error' (str, optional).
    """
    cmd = ["svn", "--version", "--quiet"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        version = result.stdout.strip()
        error = result.stderr.strip() if result.stderr else ""
        return {
            "version": version,
            "error": error
        }
    except Exception as e:
        return {"version": "", "error": str(e)}
