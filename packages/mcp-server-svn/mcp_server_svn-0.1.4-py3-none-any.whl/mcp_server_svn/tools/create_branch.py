"""SVN create branch/tag tool for MCP server."""

import subprocess


def svn_create_branch(source_path: str, dest_url: str, message: str) -> dict:
    """
    Create a branch or tag by SVN copying source_path to dest_url.

    Args:
        source_path (str): Source working copy or repo URL (e.g. trunk or another branch).
        dest_url (str): Full URL of the new branch/tag (under /branches or /tags).
        message (str): Commit message for the copy operation.

    Returns:
        dict: {"output": str, "error": str}
    """
    try:
        result = subprocess.run(
            ["svn", "copy", source_path, dest_url, "-m", message],
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
