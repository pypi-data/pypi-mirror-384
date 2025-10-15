"""
GraphitiClient - Wrapper for graphiti-core operations.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-005-GraphitiClient

This module provides a high-level interface to interact with Graphiti,
encapsulating Neo4j connection management and common operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType, EpisodicNode
from graphiti_core.edges import EntityEdge
from graphiti_core.llm_client import LLMClient, OpenAIClient
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.embedder import EmbedderClient, OpenAIEmbedder
from graphiti_core.embedder.openai import OpenAIEmbedderConfig
import logging

logger = logging.getLogger(__name__)


class GraphitiClient:
    """
    A wrapper client for Graphiti operations.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-005-GraphitiClient

    This client manages:
    - Neo4j connection and configuration
    - OpenAI API key configuration
    - High-level operations for episodes, nodes, and edges

    Attributes:
        graphiti: The underlying Graphiti instance
        neo4j_uri: Neo4j database URI
        neo4j_user: Neo4j username
        neo4j_password: Neo4j password
        openai_api_key: OpenAI API key for embeddings and LLM
    """

    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        openai_api_key: str,
        store_raw_episode_content: bool = True,
    ):
        """
        Initialize GraphitiClient with database and API configurations.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-005-GraphitiClient

        Args:
            neo4j_uri: Neo4j database connection URI (e.g., 'bolt://localhost:7687')
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            openai_api_key: OpenAI API key for embeddings and LLM operations
            store_raw_episode_content: Whether to store raw episode content in Graphiti

        Raises:
            ConnectionError: If unable to connect to Neo4j or OpenAI
            ValueError: If any required parameter is missing
        """
        if not all([neo4j_uri, neo4j_user, neo4j_password, openai_api_key]):
            raise ValueError("All connection parameters must be provided")

        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.openai_api_key = openai_api_key

        try:
            # Initialize LLM client with config
            llm_config = LLMConfig(api_key=openai_api_key)
            llm_client = OpenAIClient(config=llm_config)

            # Initialize embedder with config
            embedder_config = OpenAIEmbedderConfig(api_key=openai_api_key)
            embedder = OpenAIEmbedder(config=embedder_config)

            # Initialize Graphiti instance
            self.graphiti = Graphiti(
                uri=neo4j_uri,
                user=neo4j_user,
                password=neo4j_password,
                llm_client=llm_client,
                embedder=embedder,
                store_raw_episode_content=store_raw_episode_content,
            )

            logger.info(f"GraphitiClient initialized successfully with Neo4j at {neo4j_uri}")

        except Exception as e:
            logger.error(f"Failed to initialize GraphitiClient: {e}")
            raise ConnectionError(f"Failed to connect to Graphiti: {e}") from e

    async def add_episode(
        self,
        name: str,
        episode_body: str,
        source_description: str,
        reference_time: Optional[datetime] = None,
        source: EpisodeType = EpisodeType.message,
        group_id: Optional[str] = None,
        uuid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add an episode to Graphiti.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-005-GraphitiClient

        Args:
            name: Episode name
            episode_body: Content of the episode
            source_description: Description of the episode source
            reference_time: Reference timestamp (defaults to current time)
            source: Episode type (default: message)
            group_id: Optional group identifier for organizing episodes
            uuid: Optional UUID for the episode

        Returns:
            Dictionary containing episode UUID and processing results

        Raises:
            RuntimeError: If episode creation fails
        """
        if reference_time is None:
            reference_time = datetime.now()

        try:
            logger.debug(f"Adding episode: {name} (group_id={group_id})")

            result = await self.graphiti.add_episode(
                name=name,
                episode_body=episode_body,
                source_description=source_description,
                reference_time=reference_time,
                source=source,
                group_id=group_id,
                uuid=uuid,
            )

            logger.info(f"Episode added successfully: {name}")

            return {
                "uuid": result.episode.uuid,
                "entities_created": len(result.nodes) if result.nodes else 0,
                "edges_created": len(result.edges) if result.edges else 0,
            }

        except Exception as e:
            logger.error(f"Failed to add episode {name}: {e}")
            raise RuntimeError(f"Failed to add episode: {e}") from e

    async def delete_episode(self, episode_uuid: str) -> bool:
        """
        Delete an episode from Graphiti by its UUID.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-005-GraphitiClient

        Args:
            episode_uuid: UUID of the episode to delete

        Returns:
            True if deletion was successful

        Raises:
            RuntimeError: If deletion fails
        """
        try:
            logger.debug(f"Deleting episode: {episode_uuid}")

            await self.graphiti.remove_episode(episode_uuid)

            logger.info(f"Episode deleted successfully: {episode_uuid}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete episode {episode_uuid}: {e}")
            raise RuntimeError(f"Failed to delete episode: {e}") from e

    async def search_nodes(
        self,
        query: str,
        center_node_uuid: Optional[str] = None,
        group_ids: Optional[List[str]] = None,
        max_nodes: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for nodes in Graphiti.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-005-GraphitiClient

        Args:
            query: Search query string
            center_node_uuid: Optional UUID of a node to center the search around
            group_ids: Optional list of group IDs to filter results
            max_nodes: Maximum number of nodes to return (default: 10)

        Returns:
            List of node dictionaries containing search results

        Raises:
            RuntimeError: If search fails
        """
        try:
            logger.debug(f"Searching nodes with query: {query}")

            results = await self.graphiti.search(
                query=query,
                center_node_uuid=center_node_uuid,
                group_ids=group_ids,
                num_results=max_nodes,
            )

            # Convert EntityEdge results to dictionaries
            node_dicts = []
            for edge in results:
                node_dicts.append({
                    "uuid": edge.uuid,
                    "source_node_uuid": edge.source_node_uuid,
                    "target_node_uuid": edge.target_node_uuid,
                    "fact": edge.fact,
                    "fact_embedding": edge.fact_embedding,
                    "episodes": edge.episodes,
                    "expired_at": edge.expired_at,
                    "valid_at": edge.valid_at,
                    "invalid_at": edge.invalid_at,
                })

            logger.info(f"Found {len(node_dicts)} nodes for query: {query}")
            return node_dicts

        except Exception as e:
            logger.error(f"Failed to search nodes with query '{query}': {e}")
            raise RuntimeError(f"Failed to search nodes: {e}") from e

    async def search_facts(
        self,
        query: str,
        center_node_uuid: Optional[str] = None,
        group_ids: Optional[List[str]] = None,
        max_facts: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for facts (edges) in Graphiti.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-005-GraphitiClient

        This is an alias for search_nodes, as Graphiti's search returns EntityEdges
        which represent facts/relationships between nodes.

        Args:
            query: Search query string
            center_node_uuid: Optional UUID of a node to center the search around
            group_ids: Optional list of group IDs to filter results
            max_facts: Maximum number of facts to return (default: 10)

        Returns:
            List of fact dictionaries containing search results

        Raises:
            RuntimeError: If search fails
        """
        return await self.search_nodes(
            query=query,
            center_node_uuid=center_node_uuid,
            group_ids=group_ids,
            max_nodes=max_facts,
        )

    async def get_episodes(
        self,
        reference_time: Optional[datetime] = None,
        last_n: int = 3,
        group_ids: Optional[List[str]] = None,
        source: Optional[EpisodeType] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent episodes from Graphiti.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-005-GraphitiClient

        Args:
            reference_time: Reference timestamp (defaults to current time)
            last_n: Number of most recent episodes to retrieve (default: 3)
            group_ids: Optional list of group IDs to filter results
            source: Optional episode type filter

        Returns:
            List of episode dictionaries

        Raises:
            RuntimeError: If retrieval fails
        """
        if reference_time is None:
            reference_time = datetime.now()

        try:
            logger.debug(f"Retrieving last {last_n} episodes")

            episodes = await self.graphiti.retrieve_episodes(
                reference_time=reference_time,
                last_n=last_n,
                group_ids=group_ids,
                source=source,
            )

            # Convert EpisodicNode results to dictionaries
            episode_dicts = []
            for ep in episodes:
                episode_dicts.append({
                    "uuid": ep.uuid,
                    "name": ep.name,
                    "content": ep.content,
                    "source": ep.source.value if ep.source else None,
                    "source_description": ep.source_description,
                    "group_id": ep.group_id,
                    "created_at": ep.created_at,
                    "valid_at": ep.valid_at,
                })

            logger.info(f"Retrieved {len(episode_dicts)} episodes")
            return episode_dicts

        except Exception as e:
            logger.error(f"Failed to retrieve episodes: {e}")
            raise RuntimeError(f"Failed to retrieve episodes: {e}") from e

    async def get_entity_edge(self, edge_uuid: str) -> Dict[str, Any]:
        """
        Get an entity edge from Graphiti by its UUID.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-007-MCPTools

        Args:
            edge_uuid: UUID of the entity edge to retrieve

        Returns:
            Dictionary containing edge details

        Raises:
            RuntimeError: If retrieval fails
        """
        try:
            logger.debug(f"Getting entity edge: {edge_uuid}")

            edge = await self.graphiti.get_edge(edge_uuid)

            if edge is None:
                raise RuntimeError(f"Entity edge not found: {edge_uuid}")

            logger.info(f"Entity edge retrieved successfully: {edge_uuid}")

            return {
                "uuid": edge.uuid,
                "source_node_uuid": edge.source_node_uuid,
                "target_node_uuid": edge.target_node_uuid,
                "fact": edge.fact,
                "fact_embedding": edge.fact_embedding,
                "episodes": edge.episodes,
                "expired_at": edge.expired_at,
                "valid_at": edge.valid_at,
                "invalid_at": edge.invalid_at,
            }

        except Exception as e:
            logger.error(f"Failed to get entity edge {edge_uuid}: {e}")
            raise RuntimeError(f"Failed to get entity edge: {e}") from e

    async def delete_entity_edge(self, edge_uuid: str) -> bool:
        """
        Delete an entity edge from Graphiti by its UUID.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-007-MCPTools

        Args:
            edge_uuid: UUID of the entity edge to delete

        Returns:
            True if deletion was successful

        Raises:
            RuntimeError: If deletion fails
        """
        try:
            logger.debug(f"Deleting entity edge: {edge_uuid}")

            # Use Graphiti's driver to delete the edge
            await self.graphiti.remove_edge(edge_uuid)

            logger.info(f"Entity edge deleted successfully: {edge_uuid}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete entity edge {edge_uuid}: {e}")
            raise RuntimeError(f"Failed to delete entity edge: {e}") from e

    async def clear_graph(self) -> bool:
        """
        Clear all data from the graph memory and rebuild indices.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-007-MCPTools

        WARNING: This operation is irreversible and will delete all data!

        Returns:
            True if operation was successful

        Raises:
            RuntimeError: If operation fails
        """
        try:
            logger.warning("Clearing all graph data - this operation is irreversible!")

            # Import clear_data function
            from graphiti_core.utils.maintenance.graph_data_operations import clear_data

            # Clear all data first
            await clear_data(self.graphiti.driver)
            logger.info("Graph data cleared")

            # Rebuild indices and constraints for future data
            await self.graphiti.build_indices_and_constraints()
            logger.info("Indices and constraints rebuilt")

            logger.info("Graph cleared and indices rebuilt successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to clear graph: {e}")
            raise RuntimeError(f"Failed to clear graph: {e}") from e

    async def close(self):
        """
        Close the Graphiti connection.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-005-GraphitiClient
        """
        try:
            await self.graphiti.close()
            logger.info("GraphitiClient connection closed")
        except Exception as e:
            logger.error(f"Error closing GraphitiClient: {e}")
            raise RuntimeError(f"Failed to close connection: {e}") from e

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
