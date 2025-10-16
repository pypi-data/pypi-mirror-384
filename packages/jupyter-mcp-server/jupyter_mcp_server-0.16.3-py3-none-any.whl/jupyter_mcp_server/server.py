# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""
Jupyter MCP Server Layer
"""

from typing import Annotated, Literal
from pydantic import Field
from fastapi import Request
from jupyter_kernel_client import KernelClient

from mcp.server import FastMCP
from mcp.types import ImageContent
from starlette.middleware.cors import CORSMiddleware
from starlette.applications import Starlette
from starlette.responses import JSONResponse

from jupyter_mcp_server.log import logger
from jupyter_mcp_server.models import DocumentRuntime
from jupyter_mcp_server.utils import (
    extract_output, 
    safe_extract_outputs, 
    create_kernel,
    start_kernel,
    ensure_kernel_alive,
    execute_cell_with_forced_sync,
    wait_for_kernel_idle,
    safe_notebook_operation,
    list_files_recursively,
)
from jupyter_mcp_server.config import get_config, set_config
from jupyter_mcp_server.notebook_manager import NotebookManager
from jupyter_mcp_server.server_context import ServerContext
from jupyter_mcp_server.enroll import auto_enroll_document
from jupyter_mcp_server.tools import (
    # Tool infrastructure
    ServerMode,
    # Notebook Management
    ListNotebooksTool,
    UseNotebookTool,
    RestartNotebookTool,
    UnuseNotebookTool,
    # Cell Reading
    ReadCellsTool,
    ListCellsTool,
    ReadCellTool,
    # Cell Writing
    InsertCellTool,
    InsertExecuteCodeCellTool,
    OverwriteCellSourceTool,
    DeleteCellTool,
    # Cell Execution
    ExecuteCellTool,
    # Other Tools
    AssignKernelToNotebookTool,
    ExecuteIpythonTool,
    ListFilesTool,
    ListKernelsTool,
)


###############################################################################
# Globals.

class FastMCPWithCORS(FastMCP):
    def streamable_http_app(self) -> Starlette:
        """Return StreamableHTTP server app with CORS middleware
        See: https://github.com/modelcontextprotocol/python-sdk/issues/187
        """
        # Get the original Starlette app
        app = super().streamable_http_app()
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, should set specific domains
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        return app

mcp = FastMCPWithCORS(name="Jupyter MCP Server", json_response=False, stateless_http=True)
notebook_manager = NotebookManager()
server_context = ServerContext.get_instance()

def __start_kernel():
    """Start the Jupyter kernel with error handling (for backward compatibility)."""
    config = get_config()
    start_kernel(notebook_manager, config, logger)

async def __auto_enroll_document():
    """Wrapper for auto_enroll_document that uses server context."""
    await auto_enroll_document(
        config=get_config(),
        notebook_manager=notebook_manager,
        use_notebook_tool=UseNotebookTool(),
        server_context=server_context,
    )


def __ensure_kernel_alive() -> KernelClient:
    """Ensure kernel is running, restart if needed."""
    def __create_kernel() -> KernelClient:
        """Create a new kernel instance using current configuration."""
        config = get_config()
        return create_kernel(config, logger)
    current_notebook = notebook_manager.get_current_notebook() or "default"
    return ensure_kernel_alive(notebook_manager, current_notebook, __create_kernel)


###############################################################################
# Custom Routes.


@mcp.custom_route("/api/connect", ["PUT"])
async def connect(request: Request):
    """Connect to a document and a runtime from the Jupyter MCP server."""

    data = await request.json()
    
    # Log the received data for diagnostics
    # Note: set_config() will automatically normalize string "None" values
    logger.info(
        f"Connect endpoint received - runtime_url: {repr(data.get('runtime_url'))}, "
        f"document_url: {repr(data.get('document_url'))}, "
        f"provider: {data.get('provider')}"
    )

    document_runtime = DocumentRuntime(**data)

    # Clean up existing default notebook if any
    if "default" in notebook_manager:
        try:
            notebook_manager.remove_notebook("default")
        except Exception as e:
            logger.warning(f"Error stopping existing notebook during connect: {e}")

    # Update configuration with new values
    # String "None" values will be automatically normalized by set_config()
    set_config(
        provider=document_runtime.provider,
        runtime_url=document_runtime.runtime_url,
        runtime_id=document_runtime.runtime_id,
        runtime_token=document_runtime.runtime_token,
        document_url=document_runtime.document_url,
        document_id=document_runtime.document_id,
        document_token=document_runtime.document_token
    )
    
    # Reset ServerContext to pick up new configuration
    ServerContext.reset()

    try:
        __start_kernel()
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@mcp.custom_route("/api/stop", ["DELETE"])
async def stop(request: Request):
    try:
        current_notebook = notebook_manager.get_current_notebook() or "default"
        if current_notebook in notebook_manager:
            notebook_manager.remove_notebook(current_notebook)
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Error stopping notebook: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@mcp.custom_route("/api/healthz", ["GET"])
async def health_check(request: Request):
    """Custom health check endpoint"""
    kernel_status = "unknown"
    try:
        current_notebook = notebook_manager.get_current_notebook() or "default"
        kernel = notebook_manager.get_kernel(current_notebook)
        if kernel:
            kernel_status = "alive" if hasattr(kernel, 'is_alive') and kernel.is_alive() else "dead"
        else:
            kernel_status = "not_initialized"
    except Exception:
        kernel_status = "error"
    return JSONResponse(
        {
            "success": True,
            "service": "jupyter-mcp-server",
            "message": "Jupyter MCP Server is running.",
            "status": "healthy",
            "kernel_status": kernel_status,
        }
    )


###############################################################################
# Tools.
###############################################################################

###############################################################################
# Server Management Tools.

@mcp.tool()
async def list_files(
    path: Annotated[str, Field(description="The starting path to list from (empty string means root directory)")] = "",
    max_depth: Annotated[int, Field(description="Maximum depth to recurse into subdirectories (default: 3)")] = 3,
) -> Annotated[str, Field(description="Tab-separated table with columns: Path, Type, Size, Last_Modified")]:
    """List all files and directories in the Jupyter server's file system.

    This tool recursively lists files and directories from the Jupyter server's content API,
    showing the complete file structure including notebooks, data files, scripts, and directories.
    """
    return await safe_notebook_operation(
        lambda: ListFilesTool().execute(
            mode=server_context.mode,
            server_client=server_context.server_client,
            contents_manager=server_context.contents_manager,
            path=path,
            max_depth=max_depth,
            list_files_recursively_fn=list_files_recursively,
        )
    )


@mcp.tool()
async def list_kernels() -> Annotated[str, Field(description="Tab-separated table with columns: ID, Name, Display_Name, Language, State, Connections, Last_Activity, Environment")]:
    """List all available kernels in the Jupyter server.
    
    This tool shows all running and available kernel sessions on the Jupyter server,
    including their IDs, names, states, connection information, and kernel specifications.
    Useful for monitoring kernel resources and identifying specific kernels for connection.
    """
    return await safe_notebook_operation(
        lambda: ListKernelsTool().execute(
            mode=server_context.mode,
            server_client=server_context.server_client,
            kernel_manager=server_context.kernel_manager,
            kernel_spec_manager=server_context.kernel_spec_manager,
        )
    )


@mcp.tool()
async def assign_kernel_to_notebook(
    notebook_path: Annotated[str, Field(description="Path to the notebook file, relative to the Jupyter server root (e.g. 'notebook.ipynb')")],
    kernel_id: Annotated[str, Field(description="ID of the kernel to assign to the notebook")],
    session_name: Annotated[str, Field(description="Name for the session (If is empty, defaults to notebook path)")] = None,
) -> Annotated[str, Field(description="Success message with session information including session ID")]:
    """Assign a kernel to a notebook by creating a Jupyter session.

    This creates a Jupyter server session that connects a notebook file to a kernel,
    enabling code execution in the notebook. Sessions are the mechanism Jupyter uses
    to maintain the relationship between notebooks and their kernels.
    """
    return await safe_notebook_operation(
        lambda: AssignKernelToNotebookTool().execute(
            mode=server_context.mode,
            server_client=server_context.server_client,
            contents_manager=server_context.contents_manager,
            session_manager=server_context.session_manager,
            kernel_manager=server_context.kernel_manager,
            notebook_path=notebook_path,
            kernel_id=kernel_id,
            session_name=session_name,
        )
    )


###############################################################################
# Multi-Notebook Management Tools.


@mcp.tool()
async def use_notebook(
    notebook_name: Annotated[str, Field(description="Unique identifier for the notebook")],
    notebook_path: Annotated[str, Field(description="Path to the notebook file, relative to the Jupyter server root (e.g. 'notebook.ipynb'). If is empty, switches to an already-connected notebook with the given name.")] = None,
    mode: Annotated[Literal["connect", "create"], Field(description="Mode to use for the notebook. 'connect' to connect to existing, 'create' to create new")] = "connect",
    kernel_id: Annotated[str, Field(description="Specific kernel ID to use (will create new if is empty)")] = None,
) -> Annotated[str, Field(description="Success message with notebook information")]:
    """Use a notebook file (connect to existing or create new, or switch to already-connected notebook)."""
    config = get_config()
    return await safe_notebook_operation(
        lambda: UseNotebookTool().execute(
            mode=server_context.mode,
            server_client=server_context.server_client,
            notebook_name=notebook_name,
            notebook_path=notebook_path,
            use_mode=mode,
            kernel_id=kernel_id,
            ensure_kernel_alive_fn=__ensure_kernel_alive,
            contents_manager=server_context.contents_manager,
            kernel_manager=server_context.kernel_manager,
            session_manager=server_context.session_manager,
            notebook_manager=notebook_manager,
            runtime_url=config.runtime_url if config.runtime_url != "local" else None,
            runtime_token=config.runtime_token,
        )
    )


@mcp.tool()
async def list_notebooks() -> Annotated[str, Field(description="TSV formatted table with notebook information including management status")]:
    """List all notebooks in the Jupyter server (including subdirectories) and show which ones are managed.
    
    To interact with a notebook, it has to be "managed". If a notebook is not managed, you can use it with the `use_notebook` tool.
    """
    return await ListNotebooksTool().execute(
        mode=server_context.mode,
        server_client=server_context.server_client,
        contents_manager=server_context.contents_manager,
        kernel_manager=server_context.kernel_manager,
        notebook_manager=notebook_manager,
    )


@mcp.tool()
async def restart_notebook(
    notebook_name: Annotated[str, Field(description="Notebook identifier to restart")],
) -> Annotated[str, Field(description="Success message")]:
    """Restart the kernel for a specific notebook."""
    return await RestartNotebookTool().execute(
        mode=server_context.mode,
        notebook_name=notebook_name,
        notebook_manager=notebook_manager,
        kernel_manager=server_context.kernel_manager,
    )


@mcp.tool()
async def unuse_notebook(
    notebook_name: Annotated[str, Field(description="Notebook identifier to disconnect")],
) -> Annotated[str, Field(description="Success message")]:
    """Unuse from a specific notebook and release its resources."""
    return await UnuseNotebookTool().execute(
        mode=server_context.mode,
        notebook_name=notebook_name,
        notebook_manager=notebook_manager,
        kernel_manager=server_context.kernel_manager,
    )


###############################################################################
# Cell Tools.

@mcp.tool()
async def insert_cell(
    cell_index: Annotated[int, Field(description="Target index for insertion (0-based). Use -1 to append at end.")],
    cell_type: Annotated[Literal["code", "markdown"], Field(description="Type of cell to insert")],
    cell_source: Annotated[str, Field(description="Source content for the cell")],
) -> Annotated[str, Field(description="Success message and the structure of its surrounding cells (up to 5 cells above and 5 cells below)")]:
    """Insert a cell to specified position."""
    return await safe_notebook_operation(
        lambda: InsertCellTool().execute(
            mode=server_context.mode,
            server_client=server_context.server_client,
            contents_manager=server_context.contents_manager,
            kernel_manager=server_context.kernel_manager,
            notebook_manager=notebook_manager,
            cell_index=cell_index,
            cell_source=cell_source,
            cell_type=cell_type,
        )
    )


@mcp.tool()
async def insert_execute_code_cell(
    cell_index: Annotated[int, Field(description="Index of the cell to insert (0-based). Use -1 to append at end and execute.")],
    cell_source: Annotated[str, Field(description="Code source")],
) -> Annotated[list[str | ImageContent], Field(description="List of outputs from the executed cell")]:
    """Insert and execute a code cell in a Jupyter notebook."""
    return await safe_notebook_operation(
        lambda: InsertExecuteCodeCellTool().execute(
            mode=server_context.mode,
            server_client=server_context.server_client,
            contents_manager=server_context.contents_manager,
            kernel_manager=server_context.kernel_manager,
            notebook_manager=notebook_manager,
            cell_index=cell_index,
            cell_source=cell_source,
            ensure_kernel_alive=__ensure_kernel_alive,
        )
    )


@mcp.tool()
async def overwrite_cell_source(
    cell_index: Annotated[int, Field(description="Index of the cell to overwrite (0-based)")],
    cell_source: Annotated[str, Field(description="New cell source - must match existing cell type")],
) -> Annotated[str, Field(description="Success message with diff showing changes made")]:
    """Overwrite the source of an existing cell. Note this does not execute the modified cell by itself."""
    return await safe_notebook_operation(
        lambda: OverwriteCellSourceTool().execute(
            mode=server_context.mode,
            server_client=server_context.server_client,
            contents_manager=server_context.contents_manager,
            kernel_manager=server_context.kernel_manager,
            notebook_manager=notebook_manager,
            cell_index=cell_index,
            cell_source=cell_source,
        )
    )

@mcp.tool()
async def execute_cell(
    cell_index: Annotated[int, Field(description="Index of the cell to execute (0-based)")],
    timeout_seconds: Annotated[int, Field(description="Maximum time to wait for execution (default: 300s)")] = 300,
    stream: Annotated[bool, Field(description="Enable streaming progress updates for long-running cells (default: False)")] = False,
    progress_interval: Annotated[int, Field(description="Seconds between progress updates when stream=True (default: 5s)")] = 5,
) -> Annotated[list[str | ImageContent], Field(description="List of outputs from the executed cell")]:
    """Execute a cell with configurable timeout and optional streaming progress updates."""
    return await safe_notebook_operation(
        lambda: ExecuteCellTool().execute(
            mode=server_context.mode,
            server_client=server_context.server_client,
            contents_manager=server_context.contents_manager,
            kernel_manager=server_context.kernel_manager,
            notebook_manager=notebook_manager,
            cell_index=cell_index,
            timeout_seconds=timeout_seconds,
            stream=stream,
            progress_interval=progress_interval,
            ensure_kernel_alive_fn=__ensure_kernel_alive,
            wait_for_kernel_idle_fn=wait_for_kernel_idle,
            safe_extract_outputs_fn=safe_extract_outputs,
            execute_cell_with_forced_sync_fn=execute_cell_with_forced_sync,
            extract_output_fn=extract_output,
        ),
        max_retries=1
    )


@mcp.tool()
async def read_cells() -> Annotated[list[dict[str, str | int | list[str | ImageContent]]], Field(description="List of cell information including index, type, source, and outputs (for code cells)")]:
    """Read all cells from the Jupyter notebook."""
    return await safe_notebook_operation(
        lambda: ReadCellsTool().execute(
            mode=server_context.mode,
            server_client=server_context.server_client,
            contents_manager=server_context.contents_manager,
            notebook_manager=notebook_manager,
        )
    )


@mcp.tool()
async def list_cells() -> Annotated[str, Field(description="Tab-separated table with columns: Index, Type, Count, First Line")]:
    """List the basic information of all cells in the notebook.
    
    This provides a quick overview of the notebook structure and is useful for locating specific cells for operations like delete or insert.
    """
    return await safe_notebook_operation(
        lambda: ListCellsTool().execute(
            mode=server_context.mode,
            server_client=server_context.server_client,
            contents_manager=server_context.contents_manager,
            notebook_manager=notebook_manager,
        )
    )


@mcp.tool()
async def read_cell(
    cell_index: Annotated[int, Field(description="Index of the cell to read (0-based)")],
) -> Annotated[dict[str, str | int | list[str | ImageContent]], Field(description="Cell information including index, type, source, and outputs (for code cells)")]:
    """Read a specific cell from the Jupyter notebook."""
    return await safe_notebook_operation(
        lambda: ReadCellTool().execute(
            mode=server_context.mode,
            server_client=server_context.server_client,
            contents_manager=server_context.contents_manager,
            notebook_manager=notebook_manager,
            cell_index=cell_index,
        )
    )

@mcp.tool()
async def delete_cell(
    cell_index: Annotated[int, Field(description="Index of the cell to delete (0-based)")],
) -> Annotated[str, Field(description="Success message")]:
    """Delete a specific cell from the Jupyter notebook."""
    return await safe_notebook_operation(
        lambda: DeleteCellTool().execute(
            mode=server_context.mode,
            server_client=server_context.server_client,
            contents_manager=server_context.contents_manager,
            kernel_manager=server_context.kernel_manager,
            notebook_manager=notebook_manager,
            cell_index=cell_index,
        )
    )


@mcp.tool()
async def execute_ipython(
    code: Annotated[str, Field(description="IPython code to execute (supports magic commands, shell commands with !, and Python code)")],
    timeout: Annotated[int, Field(description="Execution timeout in seconds (default: 60s)")] = 60,
) -> Annotated[list[str | ImageContent], Field(description="List of outputs from the executed code")]:
    """Execute IPython code directly in the kernel on the current active notebook.

    This powerful tool supports:
    1. Magic commands (e.g., %timeit, %who, %load, %run, %matplotlib)
    2. Shell commands (e.g., !pip install, !ls, !cat)
    3. Python code (e.g., print(df.head()), df.info())

    Use cases:
    - Performance profiling and debugging
    - Environment exploration and package management
    - Variable inspection and data analysis
    - File system operations on Jupyter server
    - Temporary calculations and quick tests
    """
    # Get kernel_id for JUPYTER_SERVER mode
    # Let the tool handle getting kernel_id via get_current_notebook_context()
    kernel_id = None
    if server_context.mode == ServerMode.JUPYTER_SERVER:
        current_notebook = notebook_manager.get_current_notebook() or "default"
        kernel_id = notebook_manager.get_kernel_id(current_notebook)
        # Note: kernel_id might be None here if notebook not in manager,
        # but the tool will fall back to config values via get_current_notebook_context()
    
    return await safe_notebook_operation(
        lambda: ExecuteIpythonTool().execute(
            mode=server_context.mode,
            server_client=server_context.server_client,
            kernel_manager=server_context.kernel_manager,
            notebook_manager=notebook_manager,
            code=code,
            timeout=timeout,
            kernel_id=kernel_id,
            ensure_kernel_alive_fn=__ensure_kernel_alive,
            wait_for_kernel_idle_fn=wait_for_kernel_idle,
            safe_extract_outputs_fn=safe_extract_outputs,
        ),
        max_retries=1
    )

###############################################################################
# Helper Functions for Extension.


async def get_registered_tools():
    """
    Get list of all registered MCP tools with their metadata.
    
    This function is used by the Jupyter extension to dynamically expose
    the tool registry without hardcoding tool names and parameters.
    
    Returns:
        list: List of tool dictionaries with name, description, and inputSchema
    """
    # Use FastMCP's list_tools method which returns Tool objects
    tools_list = await mcp.list_tools()
    
    tools = []
    for tool in tools_list:
        tool_dict = {
            "name": tool.name,
            "description": tool.description,
        }
        
        # Extract parameter names from inputSchema
        if hasattr(tool, 'inputSchema') and tool.inputSchema:
            input_schema = tool.inputSchema
            if 'properties' in input_schema:
                tool_dict["parameters"] = list(input_schema['properties'].keys())
            else:
                tool_dict["parameters"] = []
            
            # Include full inputSchema for MCP protocol compatibility
            tool_dict["inputSchema"] = input_schema
        else:
            tool_dict["parameters"] = []
        
        # Include full outputSchema for MCP protocol compatibility
        if hasattr(tool, 'outputSchema') and tool.outputSchema:
            tool_dict["outputSchema"] = tool.outputSchema
        else:
            tool_dict["outputSchema"] = []
        
        tools.append(tool_dict)
    
    return tools