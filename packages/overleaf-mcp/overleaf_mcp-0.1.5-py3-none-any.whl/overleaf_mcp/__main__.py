from mcp.server.fastmcp import FastMCP
from .mh_overleaf import MHOverleaf
import logging as log
import os

mcp = FastMCP("overleaf_mcp")
project_id = os.getenv("PROJECT_ID")
token = os.getenv("OVERLEAF_TOKEN")
log.info(f"Project ID: {project_id}")
log.info(f"Overleaf Token: {token}")

overleaf = MHOverleaf(project_id, token)

@mcp.tool()
def list_of_files():
    """Returns a list of files in the Overleaf project.

    Returns:
        list: A list of file paths in the Overleaf project.
    """
    return overleaf.list_files()

@mcp.tool()
def read_file(filename):
    """Reads the content of a specific file in the Overleaf project.

    Args:
        filename (str): The name (path) of the file to read. The name is relative to the project root.
        For example, "main.tex" or "sections/chapter1.tex".

    Returns:
        str: The content of the specified file.
    """
    return overleaf.read_file(filename)

def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()