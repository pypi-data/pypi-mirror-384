"""
Custom error classes for RBT MCP Server.

@REQ: REQ-rbt-mcp-tool
@BP: BP-rbt-mcp-tool
@TASK: TASK-003-DocumentService
"""


class ToolError(Exception):
    """
    Unified error class for MCP tool operations.

    Provides structured error information with error code and message.

    @REQ: REQ-rbt-mcp-tool
    @BP: BP-rbt-mcp-tool
    @TASK: TASK-003-DocumentService
    """

    def __init__(self, code: str, message: str):
        """
        Initialize ToolError.

        Args:
            code: Error code (e.g., 'SECTION_NOT_FOUND', 'INVALID_BLOCK_TYPE')
            message: Human-readable error message
        """
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")
