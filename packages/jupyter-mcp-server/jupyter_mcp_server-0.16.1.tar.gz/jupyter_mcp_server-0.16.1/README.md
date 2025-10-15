<!--
  ~ Copyright (c) 2023-2024 Datalayer, Inc.
  ~
  ~ BSD 3-Clause License
-->

[![Datalayer](https://assets.datalayer.tech/datalayer-25.svg)](https://datalayer.io)

[![Become a Sponsor](https://img.shields.io/static/v1?label=Become%20a%20Sponsor&message=%E2%9D%A4&logo=GitHub&style=flat&color=1ABC9C)](https://github.com/sponsors/datalayer)


<div align="center">

<!-- omit in toc -->
# 🪐✨ Jupyter MCP Server

**An [MCP](https://modelcontextprotocol.io) server developed for AI to connect and manage Jupyter Notebooks in real-time**

*Developed by [Datalayer](https://github.com/datalayer)*

[![PyPI - Version](https://img.shields.io/pypi/v/jupyter-mcp-server?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/jupyter-mcp-server)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Docker Pulls](https://img.shields.io/docker/pulls/datalayer/jupyter-mcp-server?style=for-the-badge&logo=docker&logoColor=white&color=2496ED)](https://hub.docker.com/r/datalayer/jupyter-mcp-server)
[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue?style=for-the-badge&logo=open-source-initiative&logoColor=white)](https://opensource.org/licenses/BSD-3-Clause)


<a href="https://mseep.ai/app/datalayer-jupyter-mcp-server"><img src="https://mseep.net/pr/datalayer-jupyter-mcp-server-badge.png" alt="MseeP.ai Security Assessment Badge" width="100"></a>
<a href="https://archestra.ai/mcp-catalog/datalayer__jupyter-mcp-server"><img src="https://archestra.ai/mcp-catalog/api/badge/quality/datalayer/jupyter-mcp-server" alt="Trust Score" width="150"></a>


> 🚨 **Latest Release: v0.14.0**: **Multi-notebook support!** You can now seamlessly switch between multiple notebooks in a single session. [📋 Read more in the release notes](https://jupyter-mcp-server.datalayer.tech/releases)

![Jupyter MCP Server Demo](https://assets.datalayer.tech/jupyter-mcp/mcp-demo-multimodal.gif)

</div>

## 📖 Table of Contents
- [Key Features](#-key-features)
- [Tools Overview](#-tools-overview)
- [Getting Started](#-getting-started)
- [Best Practices](#-best-practices)
- [Contributing](#-contributing)
- [Resources](#-resources)


## 🚀 Key Features

- ⚡ **Real-time control:** Instantly view notebook changes as they happen.
- 🔁 **Smart execution:** Automatically adjusts when a cell run fails thanks to cell output feedback.
- 🧠 **Context-aware:** Understands the entire notebook context for more relevant interactions.
- 📊 **Multimodal support:** Support different output types, including images, plots, and text.
- 📚 **Multi-notebook support:** Seamlessly switch between multiple notebooks.
- 🤝 **MCP-compatible:** Works with any MCP client, such as Claude Desktop, Cursor, Windsurf, and more.

Compatible with any Jupyter deployment (local, JupyterHub, ...) and with [Datalayer](https://datalayer.ai/) hosted Notebooks.

## 🔧 Tools Overview

The server provides a rich set of tools for interacting with Jupyter notebooks, categorized as follows:

### Server Management

| Name | Description |
|:---|:---|
| `list_files` | Recursively list files and directories in the Jupyter server's file system. |
| `list_kernels` | List all available and running kernel sessions on the Jupyter server. |
| `assign_kernel_to_notebook` | Create a Jupyter session to connect a notebook file to a specific kernel. |

### Multi-Notebook Management

| Name | Description |
|:---|:---|
| `use_notebook` | Connect to a notebook file, create a new one, or switch between notebooks. |
| `list_notebooks` | List all notebooks available on the Jupyter server and their status  |
| `restart_notebook` | Restart the kernel for a specific managed notebook. |
| `unuse_notebook` | Disconnect from a specific notebook and release its resources. |

### Cell Operations and Execution

| Name | Description |
|:---|:---|
| `list_cells` | List basic information for all cells to provide a quick overview of notebook |
| `read_cell` | Read the full content (source and outputs) of a single cell. |
| `read_cells` | Read the full content of all cells in the notebook. |
| `insert_cell` | Insert a new code or markdown cell at a specified position. |
| `delete_cell` | Delete a cell at a specified index. |
| `overwrite_cell_source` | Overwrite the source code of an existing cell. |
| `execute_cell` | Execute a cell with timeout, it supports multimodal output including images. |
| `insert_execute_code_cell` | A convenient tool to insert a new code cell and execute it in one step. |
| `execute_ipython` | Execute IPython code directly in the kernel, including magic and shell commands. |

For more details on each tool, their parameters, and return values, please refer to the [official Tools documentation](https://jupyter-mcp-server.datalayer.tech/tools).

## 🏁 Getting Started

For comprehensive setup instructions—including `Streamable HTTP` transport, running as a Jupyter Server extension and advanced configuration—check out [our documentation](https://jupyter-mcp-server.datalayer.tech/). Or, get started quickly with `JupyterLab` and `STDIO` transport here below.

### 1. Set Up Your Environment

```bash
pip install jupyterlab==4.4.1 jupyter-collaboration==4.0.2 ipykernel
pip uninstall -y pycrdt datalayer_pycrdt
pip install datalayer_pycrdt==0.12.17
```

### 2. Start JupyterLab

```bash
# Start JupyterLab on port 8888, allowing access from any IP and setting a token
jupyter lab --port 8888 --IdentityProvider.token MY_TOKEN --ip 0.0.0.0
```

> [!NOTE]
> If you are running notebooks through JupyterHub instead of JupyterLab as above, you should:
>
> - Set the environment variable `JUPYTERHUB_ALLOW_TOKEN_IN_URL=1` in the single-user environment.
> - Ensure your API token (`MY_TOKEN`) is created with `access:servers` scope in the Hub.

### 3. Configure Your Preferred MCP Client

Next, configure your MCP client to connect to the server. We offer two primary methods—choose the one that best fits your needs:

- **📦 Using `uvx` (Recommended for Quick Start):** A lightweight and fast method using `uv`. Ideal for local development and first-time users.
- **🐳 Using `Docker` (Recommended for Production):** A containerized approach that ensures a consistent and isolated environment, perfect for production or complex setups.

<details>
<summary><b>📦 Using uvx (Quick Start)</b></summary>

First, install `uv`:
```bash
pip install uv
uv --version
# should be 0.6.14 or higher
```
See more details on [uv installation](https://docs.astral.sh/uv/getting-started/installation/).

Then, configure your client:
```json
{
  "mcpServers": {
    "jupyter": {
      "command": "uvx",
      "args": ["jupyter-mcp-server@latest"],
      "env": {
        "DOCUMENT_URL": "http://localhost:8888",
        "DOCUMENT_TOKEN": "MY_TOKEN",
        "DOCUMENT_ID": "notebook.ipynb",
        "RUNTIME_URL": "http://localhost:8888",
        "RUNTIME_TOKEN": "MY_TOKEN",
        "ALLOW_IMG_OUTPUT": "true"
      }
    }
  }
}
```

</details>

<details>
<summary><b>🐳 Using Docker (Production)</b></summary>

**On macOS and Windows:**
```json
{
  "mcpServers": {
    "jupyter": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "DOCUMENT_URL",
        "-e", "DOCUMENT_TOKEN",
        "-e", "DOCUMENT_ID",
        "-e", "RUNTIME_URL",
        "-e", "RUNTIME_TOKEN",
        "-e", "ALLOW_IMG_OUTPUT",
        "datalayer/jupyter-mcp-server:latest"
      ],
      "env": {
        "DOCUMENT_URL": "http://host.docker.internal:8888",
        "DOCUMENT_TOKEN": "MY_TOKEN",
        "DOCUMENT_ID": "notebook.ipynb",
        "RUNTIME_URL": "http://host.docker.internal:8888",
        "RUNTIME_TOKEN": "MY_TOKEN",
        "ALLOW_IMG_OUTPUT": "true"
      }
    }
  }
}
```

**On Linux:**
```json
{
  "mcpServers": {
    "jupyter": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "DOCUMENT_URL",
        "-e", "DOCUMENT_TOKEN",
        "-e", "DOCUMENT_ID",
        "-e", "RUNTIME_URL",
        "-e", "RUNTIME_TOKEN",
        "-e", "ALLOW_IMG_OUTPUT",
        "--network=host",
        "datalayer/jupyter-mcp-server:latest"
      ],
      "env": {
        "DOCUMENT_URL": "http://localhost:8888",
        "DOCUMENT_TOKEN": "MY_TOKEN",
        "DOCUMENT_ID": "notebook.ipynb",
        "RUNTIME_URL": "http://localhost:8888",
        "RUNTIME_TOKEN": "MY_TOKEN",
        "ALLOW_IMG_OUTPUT": "true"
      }
    }
  }
}
```

</details>

> [!TIP]
> 1. Ensure the `port` of the `DOCUMENT_URL` and `RUNTIME_URL` match those used in the `jupyter lab` command.
> 2. In a basic setup, `DOCUMENT_URL` and `RUNTIME_URL` are the same. `DOCUMENT_TOKEN`, and `RUNTIME_TOKEN` are also the same and is actually the Jupyter Token.
> 3. The `DOCUMENT_ID` parameter specifies the path to the notebook you want to connect to. It should be relative to the directory where JupyterLab was started.
>    - **Optional:** If you omit `DOCUMENT_ID`, the MCP client can automatically list all available notebooks on the Jupyter server, allowing you to select one interactively via your prompts.
>    - **Flexible:** Even if you set `DOCUMENT_ID`, the MCP client can still browse, list, switch to, or even create new notebooks at any time.

For detailed instructions on configuring various MCP clients—including [Claude Desktop](https://jupyter-mcp-server.datalayer.tech/clients/claude_desktop), [VS Code](https://jupyter-mcp-server.datalayer.tech/clients/vscode), [Cursor](https://jupyter-mcp-server.datalayer.tech/clients/cursor), [Cline](https://jupyter-mcp-server.datalayer.tech/clients/cline), and [Windsurf](https://jupyter-mcp-server.datalayer.tech/clients/windsurf) — see the [Clients documentation](https://jupyter-mcp-server.datalayer.tech/clients).

## ✅ Best Practices

- Interact with LLMs that supports multimodal input (like Gemini 2.5 Pro) to fully utilize advanced multimodal understanding capabilities.
- Use a MCP client that supports returning image data and can parse it (like Cursor, Gemini CLI, etc.), as some clients may not support this feature.
- Break down complex task (like the whole data science workflow) into multiple sub-tasks (like data cleaning, feature engineering, model training, model evaluation, etc.) and execute them step-by-step.

## 🤝 Contributing

We welcome contributions of all kinds! Here are some examples:

- 🐛 Bug fixes
- 📝 Improvements to existing features
- ✨ New feature development
- 📚 Documentation improvements

For detailed instructions on how to get started with development and submit your contributions, please see our [**Contributing Guide**](CONTRIBUTING.md).

### Our Contributors

<a href="https://github.com/datalayer/jupyter-mcp-server/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=datalayer/jupyter-mcp-server" />
</a>

## 📚 Resources

Looking for blog posts, videos, or other materials about Jupyter MCP Server?

👉 Visit the [**Resources section**](https://jupyter-mcp-server.datalayer.tech/resources) in our documentation for more!

<a href="https://star-history.com/#/repos/datalayer/jupyter-mcp-server&type=Date">
  <img src="https://api.star-history.com/svg?repos=datalayer/jupyter-mcp-server&type=Date" alt="Star History Chart">
</a>

---

<div align="center">

**If this project is helpful to you, please give us a ⭐️**

Made with ❤️ by [Datalayer](https://github.com/datalayer)

</div>