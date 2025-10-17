"""SVN resolve tool implementation for MCP server."""

import subprocess

def svn_resolve(targets, accept=None):
    """
    Run 'svn resolve' on one or more targets.

    Args:
        targets (list of str): Files or directories to resolve.
        accept (str, optional): Conflict resolution mode ("working", "mine-full", "theirs-full", etc.).

    Returns:
        dict: Dictionary with 'output' (str) and 'error' (str, optional).
    """
    if not targets:
        return {"output": "", "error": "No targets specified for resolve."}

    cmd = ["svn", "resolve"]
    if accept:
        cmd.extend(["--accept", accept])
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
