"""SVN revert tool implementation for MCP server."""

import subprocess

def svn_revert(targets, recursive=False):
    """
    Run 'svn revert' on one or more targets.

    Args:
        targets (list of str): Files or directories to revert.
        recursive (bool): Whether to recurse into subdirectories (default: False).

    Returns:
        dict: Dictionary with 'output' (str) and 'error' (str, optional).
    """
    if not targets:
        return {"output": "", "error": "No targets specified for revert."}

    cmd = ["svn", "revert"]
    if recursive:
        cmd.append("--recursive")
    cmd.extend(targets)

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
