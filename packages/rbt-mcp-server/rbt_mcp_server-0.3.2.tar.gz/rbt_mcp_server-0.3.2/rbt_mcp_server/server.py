"""
MCP Server for Graphiti Memory and Document Chunking.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp

Provides MCP tool functions for graph-based memory operations.
Editor tools have been archived (see tag v-with-editor for restoration).
"""

import os
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP

from . import graphiti_tools
from .chunking import add_document as add_document_impl


# Initialize MCP server
mcp = FastMCP("graphiti-memory-server")


# ========== Graphiti Memory Tools ==========

@mcp.tool()
async def search_memory_nodes(
    query: str,
    group_ids: Optional[List[str]] = None,
    max_nodes: int = 10,
    center_node_uuid: Optional[str] = None,
    entity: str = "",
) -> List[Dict[str, Any]]:
    """
    Search the graph memory for relevant node summaries.

    These contain a summary of all of a node's relationships with other nodes.

    Note: entity is a single entity type to filter results (permitted: "Preference", "Procedure").

    Args:
        query: The search query
        group_ids: Optional list of group IDs to filter results
        max_nodes: Maximum number of nodes to return (default: 10)
        center_node_uuid: Optional UUID of a node to center the search around
        entity: Optional single entity type to filter results (permitted: "Preference", "Procedure")

    Returns:
        List of node dictionaries containing search results

    Example:
        search_memory_nodes(
            query="project architecture decisions",
            group_ids=["knowledge-smith"],
            max_nodes=5
        )

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-007-MCPTools
    """
    return await graphiti_tools.search_nodes_impl(
        query=query,
        group_ids=group_ids,
        max_nodes=max_nodes,
        center_node_uuid=center_node_uuid,
        entity=entity,
    )


@mcp.tool()
async def search_memory_facts(
    query: str,
    group_ids: Optional[List[str]] = None,
    max_facts: int = 10,
    center_node_uuid: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search the graph memory for relevant facts.

    Args:
        query: The search query
        group_ids: Optional list of group IDs to filter results
        max_facts: Maximum number of facts to return (default: 10)
        center_node_uuid: Optional UUID of a node to center the search around

    Returns:
        List of fact dictionaries containing search results

    Example:
        search_memory_facts(
            query="implementation dependencies",
            group_ids=["knowledge-smith"],
            max_facts=10
        )

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-007-MCPTools
    """
    return await graphiti_tools.search_facts_impl(
        query=query,
        group_ids=group_ids,
        max_facts=max_facts,
        center_node_uuid=center_node_uuid,
    )


@mcp.tool()
async def get_episodes(
    group_id: Optional[str] = None,
    last_n: int = 10,
) -> List[Dict[str, Any]]:
    """
    Get the most recent memory episodes for a specific group.

    Args:
        group_id: ID of the group to retrieve episodes from. If not provided, uses the default group_id.
        last_n: Number of most recent episodes to retrieve (default: 10)

    Returns:
        List of episode dictionaries

    Example:
        get_episodes(group_id="knowledge-smith", last_n=5)

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-007-MCPTools
    """
    return await graphiti_tools.get_episodes_impl(
        group_id=group_id,
        last_n=last_n,
    )


@mcp.tool()
async def delete_episode(uuid: str) -> Dict[str, str]:
    """
    Delete an episode from the graph memory.

    Args:
        uuid: UUID of the episode to delete

    Returns:
        Success message dictionary

    Example:
        delete_episode(uuid="episode-uuid-123")

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-007-MCPTools
    """
    return await graphiti_tools.delete_episode_impl(uuid=uuid)


@mcp.tool()
async def get_entity_edge(uuid: str) -> Dict[str, Any]:
    """
    Get an entity edge from the graph memory by its UUID.

    Args:
        uuid: UUID of the entity edge to retrieve

    Returns:
        Entity edge dictionary containing edge details:
        {
            "uuid": "edge-uuid",
            "source_node_uuid": "source-uuid",
            "target_node_uuid": "target-uuid",
            "fact": "relationship description",
            "episodes": ["episode-uuid-1", "episode-uuid-2"],
            "valid_at": "2025-01-01T00:00:00Z",
            "invalid_at": null
        }

    Example:
        get_entity_edge(uuid="edge-uuid-123")

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-007-MCPTools
    """
    return await graphiti_tools.get_entity_edge_impl(uuid=uuid)


@mcp.tool()
async def delete_entity_edge(uuid: str) -> Dict[str, str]:
    """
    Delete an entity edge from the graph memory.

    Args:
        uuid: UUID of the entity edge to delete

    Returns:
        Success message dictionary

    Example:
        delete_entity_edge(uuid="edge-uuid-123")

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-007-MCPTools
    """
    return await graphiti_tools.delete_entity_edge_impl(uuid=uuid)


@mcp.tool()
async def clear_graph() -> Dict[str, str]:
    """
    Clear all data from the graph memory and rebuild indices.

    WARNING: This operation is irreversible and will delete all data from the graph!
    Use with extreme caution.

    Returns:
        Success message dictionary

    Example:
        clear_graph()

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-007-MCPTools
    """
    return await graphiti_tools.clear_graph_impl()


@mcp.tool()
async def add_document(
    new_file_path: str,
    project_id: str,
    feature_id: Optional[str] = None,
    rbt_type: Optional[str] = None,
    file_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compare new file with ROOT original file and sync differences to Graphiti.

    This tool compares a modified document with its original version in the ROOT
    directory, chunks both versions, identifies changes, and syncs the differences
    to the Graphiti knowledge graph.

    Args:
        new_file_path: Absolute path to the new/modified file
        project_id: Project identifier (e.g., "knowledge-smith")
        feature_id: Feature identifier (required for RBT documents)
        rbt_type: RBT document type ("REQ"/"BP"/"TASK"). Leave as None for general documents.
        file_path:
            - For RBT TASK: task identifier (e.g., "006")
            - For general files: relative path (e.g., "todos/xxx.md" or "docs/todos/xxx.md")
              Note: "docs/" prefix is optional and will be handled automatically.

    Returns:
        Sync statistics:
        {
            "status": "success",
            "added": 3,      # Number of chunks added
            "updated": 2,    # Number of chunks updated
            "deleted": 1,    # Number of chunks deleted
            "unchanged": 5,  # Number of chunks unchanged
            "total": 11      # Total chunks
        }

    Raises:
        FileNotFoundError: If new file not found
        ValueError: If invalid rbt_type or parameter combination

    Examples:
        # RBT TASK document
        add_document(
            new_file_path="/Users/me/workspace/TASK-006-AddDocument.md",
            project_id="knowledge-smith",
            feature_id="graphiti-chunk-mcp",
            rbt_type="TASK",
            file_path="006"
        )

        # RBT BP document
        add_document(
            new_file_path="/Users/me/workspace/BP-graphiti-chunk-mcp.md",
            project_id="knowledge-smith",
            feature_id="graphiti-chunk-mcp",
            rbt_type="BP"
        )

        # General document (both work)
        add_document(
            new_file_path="/Users/me/workspace/TODO-001.md",
            project_id="General",
            file_path="todos/TODO-001.md"  # or "docs/todos/TODO-001.md"
        )

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument
    """
    # Read environment variable
    root_dir = os.environ.get("RBT_ROOT_DIR")
    if not root_dir:
        raise ValueError("Environment variable RBT_ROOT_DIR is not set")

    # Validate new file exists
    if not os.path.exists(new_file_path):
        raise FileNotFoundError(f"New file does not exist: {new_file_path}")

    # Create GraphitiClient
    client = graphiti_tools.get_graphiti_client()

    async with client:
        result = await add_document_impl(
            new_file_path=new_file_path,
            project_id=project_id,
            feature_id=feature_id,
            doc_type=rbt_type,  # Internal implementation still uses doc_type
            file_path=file_path,
            root_dir=root_dir,
            graphiti_client=client
        )

    # Return simplified statistics
    return {
        "status": "success",
        "added": len(result.added),
        "updated": len(result.updated),
        "deleted": len(result.deleted),
        "unchanged": result.unchanged,
        "total": result.total_chunks
    }


# ========== Main Entry Point ==========

def main():
    """
    Main entry point for MCP server.

    Runs server with stdio transport (default for FastMCP).

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    """
    mcp.run()


if __name__ == "__main__":
    main()
