"""Entrypoint for the SVN MCP server using fastmcp.

This script initializes and starts the server,
registering all core SVN MCP tools via fastmcp decorators.
"""

from fastmcp import FastMCP

from .tools.status import svn_status
from .tools.diff import svn_diff
from .tools.commit import svn_commit
from .tools.update import svn_update
from .tools.log import svn_log
from .tools.add import svn_add
from .tools.checkout import svn_checkout
from .tools.switch import svn_switch
from .tools.list_branches import svn_list_branches
from .tools.create_branch import svn_create_branch
from .tools.delete_branch import svn_delete_branch
from .tools.svn_cleanup import svn_cleanup
from .tools.svn_revert import svn_revert
from .tools.svn_merge import svn_merge
from .tools.svn_resolve import svn_resolve
from .tools.svn_whoami import svn_whoami
from .tools.svn_version import svn_version

server = FastMCP("svn")

@server.tool(
    name="svn_status",
    description="Shows the SVN working copy or remote repository status."
)
def mcp_svn_status(repo_path):
    return svn_status(repo_path)

@server.tool(
    name="svn_diff",
    description="Shows SVN differences for the working copy or specific revisions.",
)
def mcp_svn_diff(repo_path, revision=None):
    return svn_diff(
        repo_path,
        revision
    )

@server.tool(
    name="svn_commit",
    description="Commits changes to the SVN repository with a message."
)
def mcp_svn_commit(repo_path, message):
    return svn_commit(repo_path, message)

@server.tool(
    name="svn_update",
    description="Updates the SVN working copy to the latest revision."
)
def mcp_svn_update(repo_path):
    return svn_update(repo_path)

@server.tool(
    name="svn_log",
    description="Shows revision log entries for the SVN repository."
)
def mcp_svn_log(repo_path, limit=None):
    return svn_log(repo_path, limit)

@server.tool(
    name="svn_add",
    description="Adds files or directories to the SVN repository."
)
def mcp_svn_add(repo_path, target):
    return svn_add(repo_path, target)

@server.tool(
    name="svn_checkout",
    description="Checks out an SVN repository to a local directory."
)
def mcp_svn_checkout(url, target_path=None):
    return svn_checkout(url, target_path)

@server.tool(
    name="svn_switch",
    description="Switch the working copy at repo_path to the branch/tag at url."
)
def mcp_svn_switch(repo_path, url):
    return svn_switch(repo_path, url)

@server.tool(
    name="svn_list_branches",
    description="List all branches and tags in the remote SVN repository."
)
def mcp_svn_list_branches(repo_url):
    return svn_list_branches(repo_url)

@server.tool(
    name="svn_create_branch",
    description="Create a branch or tag from a source path to a new URL with a commit message."
)
def mcp_svn_create_branch(source_path, dest_url, message):
    return svn_create_branch(source_path, dest_url, message)

@server.tool(
    name="svn_delete_branch",
    description="Delete a branch or tag in the remote SVN repository."
)
def mcp_svn_delete_branch(target_url, message):
    return svn_delete_branch(target_url, message)

@server.tool(
    name="svn_cleanup",
    description="Removes locks and cleans up the working copy at the given path."
)
def mcp_svn_cleanup(repo_path):
    return svn_cleanup(repo_path)

@server.tool(
    name="svn_revert",
    description="Reverts changes to the specified files or directories. Set recursive=True for directories."
)
def mcp_svn_revert(targets, recursive=False):
    return svn_revert(targets, recursive)

@server.tool(
    name="svn_merge",
    description="Merges changes from a source into the working copy at repo_path."
)
def mcp_svn_merge(source, repo_path, revision=None):
    return svn_merge(source, repo_path, revision)

@server.tool(
    name="svn_resolve",
    description="Marks specified SVN conflicts as resolved with the given strategy."
)
def mcp_svn_resolve(targets, accept=None):
    return svn_resolve(targets, accept)

@server.tool(
    name="svn_whoami",
    description="Attempts to determine the current SVN username from auth cache."
)
def mcp_svn_whoami():
    return svn_whoami()

@server.tool(
    name="svn_version",
    description="Returns the installed SVN client version."
)
def mcp_svn_version():
    return svn_version()

def main():
    try:
        server.run()
    except KeyboardInterrupt:
        print("Server stopped by user")

if __name__ == "__main__":
    main()
