"""
Test cases for GraphitiClient module.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-005-GraphitiClient

Test GraphitiClient implementation with mock Graphiti instance.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from rbt_mcp_server.chunking.graphiti_client import GraphitiClient
from graphiti_core.nodes import EpisodeType


class MockEpisode:
    """Mock class for Episode returned by Graphiti."""
    def __init__(self, uuid: str):
        self.uuid = uuid


class MockAddEpisodeResults:
    """Mock class for Graphiti AddEpisodeResults."""
    def __init__(self, episode_uuid: str, created_entities=None, created_edges=None):
        self.episode = MockEpisode(episode_uuid)
        self.nodes = created_entities or []
        self.edges = created_edges or []


class MockEpisodicNode:
    """Mock class for Graphiti EpisodicNode."""
    def __init__(self, uuid: str, name: str, content: str):
        self.uuid = uuid
        self.name = name
        self.content = content
        self.source = EpisodeType.message
        self.source_description = "test source"
        self.group_id = "test-group"
        self.created_at = datetime.now()
        self.valid_at = datetime.now()


class MockEntityEdge:
    """Mock class for Graphiti EntityEdge."""
    def __init__(self, uuid: str, fact: str):
        self.uuid = uuid
        self.source_node_uuid = "source-uuid"
        self.target_node_uuid = "target-uuid"
        self.fact = fact
        self.fact_embedding = []
        self.episodes = []
        self.expired_at = None
        self.valid_at = datetime.now()
        self.invalid_at = None


class TestGraphitiClient:
    """Test GraphitiClient with mocked Graphiti instance."""

    @pytest.fixture
    def mock_graphiti(self):
        """Create a mock Graphiti instance."""
        with patch("rbt_mcp_server.chunking.graphiti_client.Graphiti") as mock:
            instance = MagicMock()
            mock.return_value = instance
            yield instance

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        with patch("rbt_mcp_server.chunking.graphiti_client.OpenAIClient") as mock:
            yield mock

    @pytest.fixture
    def mock_embedder(self):
        """Create a mock embedder."""
        with patch("rbt_mcp_server.chunking.graphiti_client.OpenAIEmbedder") as mock:
            yield mock

    @pytest.fixture
    def client(self, mock_graphiti, mock_llm_client, mock_embedder):
        """
        Create a GraphitiClient instance with mocked dependencies.

        Test Case: Graphiti connection success
        Given: Valid Neo4j and OpenAI credentials
        When: Creating GraphitiClient instance
        Then: Client initializes successfully
        """
        client = GraphitiClient(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password",
            openai_api_key="test-api-key",
        )
        return client

    def test_init_success(self, client):
        """
        Test Case 1: GraphitiClient initialization success.
        Given: Valid configuration parameters
        When: Creating GraphitiClient instance
        Then: Client is initialized with correct attributes
        """
        assert client.neo4j_uri == "bolt://localhost:7687"
        assert client.neo4j_user == "neo4j"
        assert client.neo4j_password == "password"
        assert client.openai_api_key == "test-api-key"
        assert client.graphiti is not None

    def test_init_missing_parameters(self):
        """
        Test Case: GraphitiClient initialization with missing parameters.
        Given: Missing required parameters
        When: Creating GraphitiClient instance
        Then: Raises ValueError
        """
        with pytest.raises(ValueError, match="All connection parameters must be provided"):
            GraphitiClient(
                neo4j_uri="",
                neo4j_user="neo4j",
                neo4j_password="password",
                openai_api_key="test-api-key",
            )

    @pytest.mark.asyncio
    async def test_add_episode_success(self, client):
        """
        Test Case 2: add_episode operates successfully.
        Given: GraphitiClient instance
        When: Calling add_episode()
        Then: Episode is successfully stored in Graphiti
        """
        # Setup mock
        mock_result = MockAddEpisodeResults(
            episode_uuid="test-uuid-123",
            created_entities=["entity1", "entity2"],
            created_edges=["edge1"],
        )
        client.graphiti.add_episode = AsyncMock(return_value=mock_result)

        # Execute
        result = await client.add_episode(
            name="Test Episode",
            episode_body="This is a test episode content",
            source_description="test source",
        )

        # Assert
        assert result["uuid"] == "test-uuid-123"
        assert result["entities_created"] == 2
        assert result["edges_created"] == 1

        # Verify add_episode was called
        client.graphiti.add_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_episode_with_group_id(self, client):
        """
        Test Case: add_episode with group_id.
        Given: GraphitiClient instance
        When: Calling add_episode() with group_id
        Then: Episode is stored with correct group_id
        """
        # Setup mock
        mock_result = MockAddEpisodeResults(episode_uuid="test-uuid-456")
        client.graphiti.add_episode = AsyncMock(return_value=mock_result)

        # Execute
        result = await client.add_episode(
            name="Test Episode",
            episode_body="Test content",
            source_description="test",
            group_id="test-group-123",
        )

        # Assert
        assert result["uuid"] == "test-uuid-456"

        # Verify group_id was passed
        call_kwargs = client.graphiti.add_episode.call_args[1]
        assert call_kwargs["group_id"] == "test-group-123"

    @pytest.mark.asyncio
    async def test_delete_episode_success(self, client):
        """
        Test Case 3: delete_episode operates successfully.
        Given: Existing episode UUID
        When: Calling delete_episode()
        Then: Episode is successfully deleted
        """
        # Setup mock
        client.graphiti.remove_episode = AsyncMock()

        # Execute
        result = await client.delete_episode("test-uuid-123")

        # Assert
        assert result is True
        client.graphiti.remove_episode.assert_called_once_with("test-uuid-123")

    @pytest.mark.asyncio
    async def test_delete_episode_failure(self, client):
        """
        Test Case: delete_episode handles errors.
        Given: Invalid episode UUID
        When: Calling delete_episode()
        Then: Raises RuntimeError
        """
        # Setup mock to raise exception
        client.graphiti.remove_episode = AsyncMock(side_effect=Exception("Episode not found"))

        # Execute and assert
        with pytest.raises(RuntimeError, match="Failed to delete episode"):
            await client.delete_episode("invalid-uuid")

    @pytest.mark.asyncio
    async def test_search_nodes_success(self, client):
        """
        Test Case 4: search_nodes operates successfully.
        Given: Graphiti contains related nodes
        When: Calling search_nodes()
        Then: Returns relevant search results
        """
        # Setup mock
        mock_edges = [
            MockEntityEdge(uuid="edge-1", fact="Fact 1"),
            MockEntityEdge(uuid="edge-2", fact="Fact 2"),
        ]
        client.graphiti.search = AsyncMock(return_value=mock_edges)

        # Execute
        results = await client.search_nodes(
            query="test query",
            max_nodes=10,
        )

        # Assert
        assert len(results) == 2
        assert results[0]["uuid"] == "edge-1"
        assert results[0]["fact"] == "Fact 1"
        assert results[1]["uuid"] == "edge-2"
        assert results[1]["fact"] == "Fact 2"

        client.graphiti.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_nodes_with_filters(self, client):
        """
        Test Case: search_nodes with group_ids filter.
        Given: Multiple groups in Graphiti
        When: Calling search_nodes() with group_ids
        Then: Returns filtered results
        """
        # Setup mock
        mock_edges = [MockEntityEdge(uuid="edge-1", fact="Fact 1")]
        client.graphiti.search = AsyncMock(return_value=mock_edges)

        # Execute
        results = await client.search_nodes(
            query="test",
            group_ids=["group1", "group2"],
            center_node_uuid="center-node",
        )

        # Assert
        assert len(results) == 1

        # Verify parameters
        call_kwargs = client.graphiti.search.call_args[1]
        assert call_kwargs["group_ids"] == ["group1", "group2"]
        assert call_kwargs["center_node_uuid"] == "center-node"

    @pytest.mark.asyncio
    async def test_search_facts_success(self, client):
        """
        Test Case: search_facts operates successfully.
        Given: Graphiti contains facts
        When: Calling search_facts()
        Then: Returns relevant facts
        """
        # Setup mock
        mock_edges = [MockEntityEdge(uuid="fact-1", fact="Test Fact")]
        client.graphiti.search = AsyncMock(return_value=mock_edges)

        # Execute
        results = await client.search_facts(query="test fact", max_facts=5)

        # Assert
        assert len(results) == 1
        assert results[0]["fact"] == "Test Fact"

    @pytest.mark.asyncio
    async def test_get_episodes_success(self, client):
        """
        Test Case: get_episodes retrieves recent episodes.
        Given: Graphiti contains episodes
        When: Calling get_episodes()
        Then: Returns recent episodes
        """
        # Setup mock
        mock_episodes = [
            MockEpisodicNode(
                uuid="ep-1",
                name="Episode 1",
                content="Content 1",
            ),
            MockEpisodicNode(
                uuid="ep-2",
                name="Episode 2",
                content="Content 2",
            ),
        ]
        client.graphiti.retrieve_episodes = AsyncMock(return_value=mock_episodes)

        # Execute
        results = await client.get_episodes(last_n=2)

        # Assert
        assert len(results) == 2
        assert results[0]["uuid"] == "ep-1"
        assert results[0]["name"] == "Episode 1"
        assert results[1]["uuid"] == "ep-2"
        assert results[1]["name"] == "Episode 2"

    @pytest.mark.asyncio
    async def test_get_episodes_with_filters(self, client):
        """
        Test Case: get_episodes with group_ids filter.
        Given: Multiple groups with episodes
        When: Calling get_episodes() with group_ids
        Then: Returns filtered episodes
        """
        # Setup mock
        mock_episodes = [MockEpisodicNode(uuid="ep-1", name="Ep", content="C")]
        client.graphiti.retrieve_episodes = AsyncMock(return_value=mock_episodes)

        # Execute
        results = await client.get_episodes(
            last_n=5,
            group_ids=["group1"],
            source=EpisodeType.message,
        )

        # Assert
        assert len(results) == 1

        # Verify parameters
        call_kwargs = client.graphiti.retrieve_episodes.call_args[1]
        assert call_kwargs["last_n"] == 5
        assert call_kwargs["group_ids"] == ["group1"]
        assert call_kwargs["source"] == EpisodeType.message

    @pytest.mark.asyncio
    async def test_delete_entity_edge_success(self, client):
        """
        Test Case: delete_entity_edge successfully deletes an edge.
        Given: Valid entity edge UUID
        When: Calling delete_entity_edge()
        Then: Edge is deleted successfully

        @TASK: TASK-007-MCPTools
        """
        # Setup mock
        client.graphiti.remove_edge = AsyncMock()

        # Execute
        result = await client.delete_entity_edge("edge-uuid-123")

        # Assert
        assert result is True
        client.graphiti.remove_edge.assert_called_once_with("edge-uuid-123")

    @pytest.mark.asyncio
    async def test_delete_entity_edge_failure(self, client):
        """
        Test Case: delete_entity_edge handles errors.
        Given: Invalid entity edge UUID
        When: Calling delete_entity_edge()
        Then: RuntimeError is raised

        @TASK: TASK-007-MCPTools
        """
        # Setup mock to raise exception
        client.graphiti.remove_edge = AsyncMock(side_effect=Exception("Edge not found"))

        # Execute & Assert
        with pytest.raises(RuntimeError) as exc_info:
            await client.delete_entity_edge("invalid-uuid")

        assert "Failed to delete entity edge" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_close_connection(self, client):
        """
        Test Case: close() properly closes Graphiti connection.
        Given: Active GraphitiClient instance
        When: Calling close()
        Then: Graphiti connection is closed
        """
        # Setup mock
        client.graphiti.close = AsyncMock()

        # Execute
        await client.close()

        # Assert
        client.graphiti.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_graphiti, mock_llm_client, mock_embedder):
        """
        Test Case: GraphitiClient works as async context manager.
        Given: GraphitiClient instance
        When: Using as async context manager
        Then: Properly initializes and closes connection
        """
        mock_graphiti.close = AsyncMock()

        async with GraphitiClient(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password",
            openai_api_key="test-key",
        ) as client:
            assert client is not None
            assert client.graphiti is not None

        # Verify close was called
        client.graphiti.close.assert_called_once()
