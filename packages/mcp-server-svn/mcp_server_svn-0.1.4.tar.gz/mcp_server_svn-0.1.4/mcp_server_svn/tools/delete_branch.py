"""SVN delete branch/tag tool for MCP server."""

import subprocess


def svn_delete_branch(target_url: str, message: str) -> dict:
    """
    Delete a branch or tag in the remote repository.

    Args:
        target_url (str): Full URL to the branch or tag to delete.
        message (str): Commit message for the delete operation.

    Returns:
        dict: {"output": str, "error": str}
    """
    try:
        result = subprocess.run(
            ["svn", "delete", target_url, "-m", message],
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
