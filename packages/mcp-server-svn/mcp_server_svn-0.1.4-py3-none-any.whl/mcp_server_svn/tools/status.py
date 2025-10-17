"""SVN status tool implementation for MCP server."""

import subprocess


def svn_status(repo_path):
    """
    Run 'svn status' and expose current branch/tag on the given repository path.

    Args:
        repo_path (str): Path to the SVN working copy or repository.

    Returns:
        dict: Dictionary with 'status' (str), 'error' (str), and 'branch_or_tag' (str, optional).
    """
    try:
        result = subprocess.run(
            ["svn", "status", repo_path],
            capture_output=True,
            text=True,
            check=False,
        )

        info_result = subprocess.run(
            ["svn", "info", repo_path],
            capture_output=True,
            text=True,
            check=False,
        )
        branch_or_tag = ""
        if info_result.returncode == 0:
            for line in info_result.stdout.splitlines():
                if line.startswith("Relative URL:"):
                    branch_or_tag = line.replace("Relative URL:", "").strip()
                    break

        return {
            "status": result.stdout,
            "error": result.stderr.strip() if result.stderr else "",
            "branch_or_tag": branch_or_tag
        }
    except Exception as e:
        return {"status": "", "error": str(e), "branch_or_tag": ""}
