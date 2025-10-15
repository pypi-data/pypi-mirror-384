"""
Simple Agent with Approval Example

A basic agent with 3 tools where 1 requires human approval.
Demonstrates: Approval workflows, CLI/API interrupt handling

Run with: broadie chat examples/simple_with_approval.py:agent
"""

from pydantic import BaseModel, Field

from broadie import ToolResponse, ToolStatus, create_agent, tool


# Tools
@tool(parse_docstring=True)
def read_file(filename: str) -> ToolResponse:
    """Read contents of a file.

    Args:
        filename: Name of the file to read

    Returns:
        File contents
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Read file: {filename}",
        data={"filename": filename, "contents": f"Contents of {filename}..."},
    )


@tool(parse_docstring=True)
def list_files(directory: str = ".") -> ToolResponse:
    """List files in a directory.

    Args:
        directory: Directory path to list files from

    Returns:
        List of files in the directory
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Listed files in {directory}",
        data={"directory": directory, "files": ["file1.txt", "file2.txt", "config.json"]},
    )


@tool(
    parse_docstring=True,
    approval_required=True,
    approval_message="⚠️  Delete file {filename}? This cannot be undone!",
    risk_level="high",
)
def delete_file(filename: str) -> ToolResponse:
    """Delete a file - REQUIRES APPROVAL!

    This is a destructive operation that requires human approval.

    Args:
        filename: Name of the file to delete

    Returns:
        Deletion result
    """
    return ToolResponse(
        status=ToolStatus.SUCCESS,
        message=f"Deleted file: {filename}",
        data={"filename": filename, "deleted": True},
    )


# Output Schema
class FileOperationOutput(BaseModel):
    summary: str = Field(description="Summary of file operations performed")
    files_affected: list[str] = Field(description="List of files that were affected")
    operations: list[str] = Field(description="List of operations performed")


# Create agent directly - works for both library and CLI usage
agent = create_agent(
    name="FileManagerAgent",
    instruction=(
        "You are a file management assistant with access to file operation tools. "
        "You MUST use the available tools for all file operations - do not simulate or describe actions. "
        "When a user asks to delete, read, or list files, you MUST call the corresponding tool. "
        "For delete operations, the tool requires approval - call the tool and the system will handle approval. "
        "Never respond without using tools when a file operation is requested."
    ),
    tools=[read_file, list_files, delete_file],
    output_schema=FileOperationOutput,
)


agent.run("Please list files in the current directory, read 'config.json', and delete 'file1.txt'.")
