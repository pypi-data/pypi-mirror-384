"""
Graphiti MCP Tools - Wrapper functions for Graphiti memory operations.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-007-MCPTools

Provides MCP tool functions for Graphiti knowledge graph operations:
- search_nodes: Search for relevant node summaries
- search_facts: Search for relevant facts (edges)
- get_episodes: Retrieve recent episodes
- delete_episode: Delete an episode
- delete_entity_edge: Delete an entity edge
"""

import os
from typing import Any, Dict, List, Optional
from .chunking.graphiti_client import GraphitiClient
from .errors import ToolError


def get_graphiti_client() -> GraphitiClient:
    """
    Create and return a GraphitiClient instance using environment variables.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-007-MCPTools

    Required environment variables:
        - NEO4J_URI: Neo4j database URI (e.g., 'bolt://localhost:7687')
        - NEO4J_USER: Neo4j username
        - NEO4J_PASSWORD: Neo4j password
        - OPENAI_API_KEY: OpenAI API key

    Returns:
        GraphitiClient instance

    Raises:
        ValueError: If required environment variables are missing
    """
    neo4j_uri = os.environ.get("NEO4J_URI")
    neo4j_user = os.environ.get("NEO4J_USER")
    neo4j_password = os.environ.get("NEO4J_PASSWORD")
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    if not all([neo4j_uri, neo4j_user, neo4j_password, openai_api_key]):
        raise ValueError(
            "Missing required environment variables. Please set: "
            "NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OPENAI_API_KEY"
        )

    return GraphitiClient(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password,
        openai_api_key=openai_api_key,
    )


async def search_nodes_impl(
    query: str,
    group_ids: Optional[List[str]] = None,
    max_nodes: int = 10,
    center_node_uuid: Optional[str] = None,
    entity: str = "",
) -> List[Dict[str, Any]]:
    """
    Search the graph memory for relevant node summaries.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-007-MCPTools

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

    Raises:
        ToolError: If search operation fails
    """
    try:
        client = get_graphiti_client()
        async with client:
            results = await client.search_nodes(
                query=query,
                center_node_uuid=center_node_uuid,
                group_ids=group_ids,
                max_nodes=max_nodes,
            )

            # Filter by entity type if specified
            if entity:
                # Note: The entity filtering would need to be implemented
                # based on node labels or properties. For now, we return all results.
                pass

            return results

    except Exception as e:
        raise ToolError(
            "SEARCH_NODES_ERROR",
            f"Failed to search nodes: {str(e)}"
        ) from e


async def search_facts_impl(
    query: str,
    group_ids: Optional[List[str]] = None,
    max_facts: int = 10,
    center_node_uuid: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search the graph memory for relevant facts.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-007-MCPTools

    Args:
        query: The search query
        group_ids: Optional list of group IDs to filter results
        max_facts: Maximum number of facts to return (default: 10)
        center_node_uuid: Optional UUID of a node to center the search around

    Returns:
        List of fact dictionaries containing search results

    Raises:
        ToolError: If search operation fails
    """
    try:
        client = get_graphiti_client()
        async with client:
            results = await client.search_facts(
                query=query,
                center_node_uuid=center_node_uuid,
                group_ids=group_ids,
                max_facts=max_facts,
            )
            return results

    except Exception as e:
        raise ToolError(
            "SEARCH_FACTS_ERROR",
            f"Failed to search facts: {str(e)}"
        ) from e


async def get_episodes_impl(
    group_id: Optional[str] = None,
    last_n: int = 10,
) -> List[Dict[str, Any]]:
    """
    Get the most recent memory episodes for a specific group.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-007-MCPTools

    Args:
        group_id: ID of the group to retrieve episodes from. If not provided, uses the default group_id.
        last_n: Number of most recent episodes to retrieve (default: 10)

    Returns:
        List of episode dictionaries

    Raises:
        ToolError: If retrieval operation fails
    """
    try:
        client = get_graphiti_client()
        async with client:
            group_ids = [group_id] if group_id else None
            results = await client.get_episodes(
                last_n=last_n,
                group_ids=group_ids,
            )
            return results

    except Exception as e:
        raise ToolError(
            "GET_EPISODES_ERROR",
            f"Failed to retrieve episodes: {str(e)}"
        ) from e


async def delete_episode_impl(uuid: str) -> Dict[str, str]:
    """
    Delete an episode from the graph memory.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-007-MCPTools

    Args:
        uuid: UUID of the episode to delete

    Returns:
        Success message dictionary

    Raises:
        ToolError: If deletion operation fails
    """
    try:
        client = get_graphiti_client()
        async with client:
            await client.delete_episode(uuid)
            return {"message": f"Successfully deleted episode {uuid}"}

    except Exception as e:
        raise ToolError(
            "DELETE_EPISODE_ERROR",
            f"Failed to delete episode: {str(e)}"
        ) from e


async def get_entity_edge_impl(uuid: str) -> Dict[str, Any]:
    """
    Get an entity edge from the graph memory by its UUID.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-007-MCPTools

    Args:
        uuid: UUID of the entity edge to retrieve

    Returns:
        Entity edge dictionary containing edge details

    Raises:
        ToolError: If retrieval operation fails
    """
    try:
        client = get_graphiti_client()
        async with client:
            edge = await client.get_entity_edge(uuid)
            return edge

    except Exception as e:
        raise ToolError(
            "GET_ENTITY_EDGE_ERROR",
            f"Failed to get entity edge: {str(e)}"
        ) from e


async def delete_entity_edge_impl(uuid: str) -> Dict[str, str]:
    """
    Delete an entity edge from the graph memory.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-007-MCPTools

    Args:
        uuid: UUID of the entity edge to delete

    Returns:
        Success message dictionary

    Raises:
        ToolError: If deletion operation fails
    """
    try:
        client = get_graphiti_client()
        async with client:
            await client.delete_entity_edge(uuid)
            return {"message": f"Successfully deleted entity edge {uuid}"}

    except Exception as e:
        raise ToolError(
            "DELETE_ENTITY_EDGE_ERROR",
            f"Failed to delete entity edge: {str(e)}"
        ) from e


async def clear_graph_impl() -> Dict[str, str]:
    """
    Clear all data from the graph memory and rebuild indices.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-007-MCPTools

    WARNING: This operation is irreversible and will delete all data!

    Returns:
        Success message dictionary

    Raises:
        ToolError: If operation fails
    """
    try:
        client = get_graphiti_client()
        async with client:
            await client.clear_graph()
            return {"message": "Successfully cleared graph and rebuilt indices"}

    except Exception as e:
        raise ToolError(
            "CLEAR_GRAPH_ERROR",
            f"Failed to clear graph: {str(e)}"
        ) from e
