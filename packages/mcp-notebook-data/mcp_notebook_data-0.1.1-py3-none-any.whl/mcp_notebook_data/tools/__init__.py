from mcp_notebook_data.tools.notebook import register_notebook_tools
from mcp_notebook_data.tools.postgresql import register_postgresql_tools


def register_all_tools(server, session):
    """
    Register all available tools with the MCP server.

    This function calls the registration functions from each submodule,
    ensuring all notebook and database tools are available.

    Args:
        server (Server): The MCP server instance.
        session (NotebookSession): The notebook session instance.
    """
    register_notebook_tools(server, session)
    register_postgresql_tools(server, session)
