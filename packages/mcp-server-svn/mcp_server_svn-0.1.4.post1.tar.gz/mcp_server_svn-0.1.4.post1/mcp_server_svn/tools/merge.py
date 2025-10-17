"""SVN merge tool implementation for MCP server."""

import subprocess

def svn_merge(source, repo_path, revision=None):
    """
    Run 'svn merge' from the source into the given repository path.

    Args:
        source (str): The source URL or local path to merge from.
        repo_path (str): Path to the target SVN working copy.
        revision (str, optional): Specific revision or revision range to merge.

    Returns:
        dict: Dictionary with 'output' (str) and 'error' (str, optional).
    """
    if not source or not repo_path:
        return {"output": "", "error": "Both source and repo_path are required for merge."}

    cmd = ["svn", "merge"]
    if revision:
        cmd.extend(["-r", revision])
    cmd.append(source)
    cmd.append(repo_path)

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
