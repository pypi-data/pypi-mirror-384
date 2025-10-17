# mcp-server-svn

[![PyPI version](https://badge.fury.io/py/mcp-server-svn.svg)](https://badge.fury.io/py/mcp-server-svn)
[![Python Versions](https://img.shields.io/pypi/pyversions/mcp-server-svn.svg)](https://pypi.org/project/mcp-server-svn/)


A modern [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/mcp) server for [SVN (Subversion)](https://subversion.apache.org/). Exposes core SVN operations as automated MCP tools for agent-driven workflows, seamless automation, and version control integration.

---

## Features

- Automates SVN repositories through the MCP agent and tool system
- Exposes high-level SVN commands (status, diff, log, update, add, commit, checkout, branch ops) as callables
- Compatible with [fastmcp](https://github.com/modelcontextprotocol/fastmcp)
- Python 3.10+ and modern build/packaging standards

---

## Installation

```bash
pip install mcp-server-svn
```

- Requires SVN (`svn` CLI) in your PATH.
- [fastmcp](https://github.com/modelcontextprotocol/fastmcp) installed automatically as a dependency.

---

## Supported MCP Tools

| Tool            | Inputs                                                        | Outputs                    | Description                                                      |
|-----------------|---------------------------------------------------------------|----------------------------|------------------------------------------------------------------|
| `svn_status`        | `repo_path` (str)                                            | `status` (str), `error` (str)        | Show working copy/repo status                                    |
| `svn_diff`          | `repo_path` (str), `revision` (str, optional)                | `diff` (str), `error` (str)          | Show working copy or revision differences                        |
| `svn_commit`        | `repo_path` (str), `message` (str)                           | `output` (str), `error` (str)        | Commit changes with a message                                    |
| `svn_update`        | `repo_path` (str)                                            | `output` (str), `error` (str)        | Bring working copy up to date                                    |
| `svn_log`           | `repo_path` (str), `limit` (int, optional)                   | `log` (str), `error` (str)           | Show repository log entries                                      |
| `svn_add`           | `repo_path` (str), `target` (str)                            | `output` (str), `error` (str)        | Add files/directories to version control                         |
| `svn_checkout`      | `url` (str), `target_path` (str, optional)                   | `output` (str), `error` (str)        | Checkout a full SVN repo to disk                                 |
| `svn_switch`        | `repo_path` (str), `url` (str)                               | `output` (str), `error` (str)        | Switch working copy to branch/tag                                |
| `svn_list_branches` | `repo_url` (str)                                             | `branches` (list of str), `error` (str) | List branches/tags in the repo                                   |
| `svn_create_branch` | `source_path` (str), `dest_url` (str), `message` (str)       | `output` (str), `error` (str)        | Create branch/tag from trunk                                     |
| `svn_delete_branch` | `target_url` (str), `message` (str)                          | `output` (str), `error` (str)        | Delete branch/tag                                                |
| `svn_cleanup`       | `repo_path` (str)                                            | `output` (str), `error` (str) | Remove locks and clean up the working copy (fix interrupted ops) |
| `svn_revert`        | `targets` (list of str)<br>`recursive` (bool, optional)      | `output` (str), `error` (str) | Revert changes to files/dirs; supports recursive option          |
| `svn_merge`         | `source` (str), `repo_path` (str), `revision` (str, optional)| `output` (str), `error` (str) | Merge changes from a source URL/path into the working copy       |
| `svn_resolve`       | `targets` (list of str), `accept` (str, optional)            | `output` (str), `error` (str) | Mark files as resolved after conflict; supports resolution modes |
| `svn_whoami`        | *(none)*                                                    | `username` (str), `error` (str) | Return the cached SVN username, if available in your auth files  |
| `svn_version`       | *(none)*                                                    | `version` (str), `error` (str) | Report the installed SVN client version                          |

---

## Quickstart

Start the MCP server (after installation):

```bash
mcp-server-svn
```

Or using the Python module:

```bash
python -m mcp_server_svn
```



---

## Requirements

- Python 3.10+
- [fastmcp](https://github.com/modelcontextprotocol/fastmcp) (auto-installed)
- SVN command-line client (`svn`) installed and accessible from your PATH

---

## Usage with cline

To use `mcp-server-svn` as an MCP tool server in [cline](https://github.com/saoudrizwan/cline), add an entry to your cline configuration:

```json
"svn": {
  "autoApprove": [
    "svn_status",
    "svn_diff",
    "svn_update",
    "svn_log",
    "svn_add",
    "svn_checkout"
  ],
  "timeout": 30,
  "type": "stdio",
  "command": "/usr/bin/python3.11",
  "args": [
    "-m",
    "mcp_server_svn"
  ]
}
```

Adjust `"command"` as needed (e.g., `"python3"` or your virtualenv path). See the [cline documentation](https://github.com/saoudrizwan/cline) for details.

---

## Author

**Manav Desai**  
Email: [manav27202@gmail.com](mailto:manav27202@gmail.com)
