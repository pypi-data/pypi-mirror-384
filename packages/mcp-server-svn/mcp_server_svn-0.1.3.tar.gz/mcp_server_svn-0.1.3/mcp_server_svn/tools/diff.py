"""SVN diff tool implementation for MCP server."""

import subprocess


def svn_diff(repo_path, revision=None):
    """
    Run 'svn diff' on the given repository path and optional revision.

    Args:
        repo_path (str): Path to the SVN working copy or repository.
        revision (str, optional): Revision (e.g., "-r 100:101"); 
            if None, show local diff.

    Returns:
        dict: Dictionary with 'diff' (str) and 'error' (str, optional).
    """
    cmd = ["svn", "diff", repo_path]
    if revision:
        cmd += ["-r", revision]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "diff": result.stdout,
            "error": result.stderr.strip() if result.stderr else ""
        }
    except Exception as e:
        return {"diff": "", "error": str(e)}
