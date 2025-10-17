"""SVN whoami tool implementation for MCP server.

Extracts the SVN username from authentication cache files in ~/.subversion/auth/svn.simple/.
"""

import pathlib
import os

def svn_whoami():
    """
    Attempts to extract the current SVN username from the local auth cache.

    Returns:
        dict: {'username': str, 'error': str}
    """
    svn_auth_dir = pathlib.Path.home() / ".subversion" / "auth" / "svn.simple"
    if not svn_auth_dir.exists() or not svn_auth_dir.is_dir():
        return {
            "username": "",
            "error": "SVN authentication cache directory not found: {}".format(str(svn_auth_dir))
        }
    try:
        usernames = []
        # Iterate files in svn.simple directory
        for authfile in sorted(svn_auth_dir.iterdir()):
            try:
                with authfile.open("r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if line.strip() == "username":
                            # Usually, next (non-empty) line is username value
                            for next_line in lines[i+1:i+3]:
                                val = next_line.strip()
                                if val and val != "END":
                                    usernames.append(val)
                                    break
            except Exception:
                continue  # skip any unreadable/corrupt files
        if usernames:
            # Use the last username found (as tail -1 would)
            return {"username": usernames[-1], "error": ""}
        else:
            return {"username": "", "error": "No cached SVN username found in {}".format(str(svn_auth_dir))}
    except Exception as e:
        return {"username": "", "error": str(e)}
