"""SVN diff tool implementation for MCP server."""

import subprocess
from pathlib import Path


def svn_diff(repo_path, revision=None, output_path=None):
    """
    Run 'svn diff' on the given repository path and optional revision.
    Optionally write the diff output to a file.

    Args:
        repo_path (str): Path to the SVN working copy or repository.
        revision (str, optional): Revision (e.g., "-r 100:101");
            if None, show local diff.
        output_path (str, optional): Filepath to write diff output, if desired.

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
        diff_output = result.stdout
        error = result.stderr.strip() if result.stderr else ""

        if output_path and diff_output:
            try:
                output_file = Path(output_path).expanduser()
                with output_file.open("w", encoding="utf-8") as f:
                    f.write(diff_output)
            except Exception as file_err:
                error += f"\n[File write error: {file_err}]"

        return {
            "diff": diff_output,
            "error": error
        }
    except Exception as e:
        return {"diff": "", "error": str(e)}
