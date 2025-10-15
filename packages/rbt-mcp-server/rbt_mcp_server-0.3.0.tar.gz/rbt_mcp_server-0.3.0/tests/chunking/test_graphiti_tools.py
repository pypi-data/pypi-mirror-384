"""
Test cases for Graphiti MCP tools.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-007-MCPTools

Test the MCP tool wrapper functions for Graphiti operations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from rbt_mcp_server import graphiti_tools
from rbt_mcp_server.errors import ToolError


class MockGraphitiClient:
    """Mock GraphitiClient for testing."""

    def __init__(self):
        self.search_nodes = AsyncMock()
        self.search_facts = AsyncMock()
        self.get_episodes = AsyncMock()
        self.delete_episode = AsyncMock()
        self.delete_entity_edge = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("NEO4J_URI", "bolt://localhost:7687")
    monkeypatch.setenv("NEO4J_USER", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "password")
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")


@pytest.fixture
def mock_client():
    """Create a mock GraphitiClient."""
    return MockGraphitiClient()


class TestGetGraphitiClient:
    """Test get_graphiti_client function."""

    def test_missing_env_vars(self, monkeypatch):
        """
        Test Case: Missing environment variables
        Given: Required environment variables are not set
        When: Calling get_graphiti_client()
        Then: ValueError is raised
        """
        # Clear all environment variables
        monkeypatch.delenv("NEO4J_URI", raising=False)
        monkeypatch.delenv("NEO4J_USER", raising=False)
        monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ValueError) as exc_info:
            graphiti_tools.get_graphiti_client()

        assert "Missing required environment variables" in str(exc_info.value)

    def test_with_env_vars(self, mock_env_vars):
        """
        Test Case: Valid environment variables
        Given: All required environment variables are set
        When: Calling get_graphiti_client()
        Then: GraphitiClient instance is created successfully
        """
        with patch("rbt_mcp_server.graphiti_tools.GraphitiClient") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            client = graphiti_tools.get_graphiti_client()

            assert client is not None
            mock_class.assert_called_once_with(
                neo4j_uri="bolt://localhost:7687",
                neo4j_user="neo4j",
                neo4j_password="password",
                openai_api_key="test-api-key",
            )


class TestSearchNodesImpl:
    """Test search_nodes_impl function."""

    @pytest.mark.asyncio
    async def test_search_nodes_success(self, mock_env_vars, mock_client):
        """
        Test Case 1: search_nodes與graphiti-mcp行為一致
        Given: Valid search query
        When: Calling search_nodes_impl()
        Then: Returns search results from GraphitiClient
        """
        expected_results = [
            {
                "uuid": "node-1",
                "source_node_uuid": "source-1",
                "target_node_uuid": "target-1",
                "fact": "Test fact 1",
                "fact_embedding": [],
                "episodes": [],
                "expired_at": None,
                "valid_at": datetime.now(),
                "invalid_at": None,
            }
        ]
        mock_client.search_nodes.return_value = expected_results

        with patch("rbt_mcp_server.graphiti_tools.get_graphiti_client", return_value=mock_client):
            results = await graphiti_tools.search_nodes_impl(
                query="test query",
                group_ids=["test-group"],
                max_nodes=5,
            )

            assert results == expected_results
            mock_client.search_nodes.assert_called_once_with(
                query="test query",
                center_node_uuid=None,
                group_ids=["test-group"],
                max_nodes=5,
            )

    @pytest.mark.asyncio
    async def test_search_nodes_error(self, mock_env_vars, mock_client):
        """
        Test Case: search_nodes handles errors
        Given: GraphitiClient raises an exception
        When: Calling search_nodes_impl()
        Then: ToolError is raised
        """
        mock_client.search_nodes.side_effect = Exception("Connection error")

        with patch("rbt_mcp_server.graphiti_tools.get_graphiti_client", return_value=mock_client):
            with pytest.raises(ToolError) as exc_info:
                await graphiti_tools.search_nodes_impl(query="test")

            assert "SEARCH_NODES_ERROR" in str(exc_info.value)


class TestSearchFactsImpl:
    """Test search_facts_impl function."""

    @pytest.mark.asyncio
    async def test_search_facts_success(self, mock_env_vars, mock_client):
        """
        Test Case 2: search_facts與graphiti-mcp行為一致
        Given: Valid search query
        When: Calling search_facts_impl()
        Then: Returns search results from GraphitiClient
        """
        expected_results = [
            {
                "uuid": "fact-1",
                "source_node_uuid": "source-1",
                "target_node_uuid": "target-1",
                "fact": "Test fact",
                "fact_embedding": [],
                "episodes": [],
            }
        ]
        mock_client.search_facts.return_value = expected_results

        with patch("rbt_mcp_server.graphiti_tools.get_graphiti_client", return_value=mock_client):
            results = await graphiti_tools.search_facts_impl(
                query="test query",
                group_ids=["test-group"],
                max_facts=10,
            )

            assert results == expected_results
            mock_client.search_facts.assert_called_once_with(
                query="test query",
                center_node_uuid=None,
                group_ids=["test-group"],
                max_facts=10,
            )

    @pytest.mark.asyncio
    async def test_search_facts_error(self, mock_env_vars, mock_client):
        """
        Test Case: search_facts handles errors
        Given: GraphitiClient raises an exception
        When: Calling search_facts_impl()
        Then: ToolError is raised
        """
        mock_client.search_facts.side_effect = Exception("Search error")

        with patch("rbt_mcp_server.graphiti_tools.get_graphiti_client", return_value=mock_client):
            with pytest.raises(ToolError) as exc_info:
                await graphiti_tools.search_facts_impl(query="test")

            assert "SEARCH_FACTS_ERROR" in str(exc_info.value)


class TestGetEpisodesImpl:
    """Test get_episodes_impl function."""

    @pytest.mark.asyncio
    async def test_get_episodes_success(self, mock_env_vars, mock_client):
        """
        Test Case 3: get_episodes運作正常
        Given: Graphiti中有多個episodes
        When: Calling get_episodes_impl(last_n=5)
        Then: 返回最近5個episodes
        """
        expected_episodes = [
            {
                "uuid": f"episode-{i}",
                "name": f"Episode {i}",
                "content": f"Content {i}",
                "source": "message",
                "source_description": "test",
                "group_id": "test-group",
                "created_at": datetime.now(),
                "valid_at": datetime.now(),
            }
            for i in range(5)
        ]
        mock_client.get_episodes.return_value = expected_episodes

        with patch("rbt_mcp_server.graphiti_tools.get_graphiti_client", return_value=mock_client):
            results = await graphiti_tools.get_episodes_impl(
                group_id="test-group",
                last_n=5,
            )

            assert len(results) == 5
            assert results == expected_episodes
            mock_client.get_episodes.assert_called_once_with(
                last_n=5,
                group_ids=["test-group"],
            )

    @pytest.mark.asyncio
    async def test_get_episodes_no_group(self, mock_env_vars, mock_client):
        """
        Test Case: get_episodes without group_id
        Given: No group_id specified
        When: Calling get_episodes_impl()
        Then: Returns episodes from all groups
        """
        mock_client.get_episodes.return_value = []

        with patch("rbt_mcp_server.graphiti_tools.get_graphiti_client", return_value=mock_client):
            results = await graphiti_tools.get_episodes_impl(last_n=10)

            mock_client.get_episodes.assert_called_once_with(
                last_n=10,
                group_ids=None,
            )


class TestDeleteEpisodeImpl:
    """Test delete_episode_impl function."""

    @pytest.mark.asyncio
    async def test_delete_episode_success(self, mock_env_vars, mock_client):
        """
        Test Case 4: delete_episode運作正常
        Given: 已存在的episode UUID
        When: Calling delete_episode_impl()
        Then: episode成功刪除
        """
        mock_client.delete_episode.return_value = True

        with patch("rbt_mcp_server.graphiti_tools.get_graphiti_client", return_value=mock_client):
            result = await graphiti_tools.delete_episode_impl(uuid="episode-123")

            assert result == {"message": "Successfully deleted episode episode-123"}
            mock_client.delete_episode.assert_called_once_with("episode-123")

    @pytest.mark.asyncio
    async def test_delete_episode_error(self, mock_env_vars, mock_client):
        """
        Test Case: delete_episode handles errors
        Given: Invalid episode UUID
        When: Calling delete_episode_impl()
        Then: ToolError is raised
        """
        mock_client.delete_episode.side_effect = Exception("Episode not found")

        with patch("rbt_mcp_server.graphiti_tools.get_graphiti_client", return_value=mock_client):
            with pytest.raises(ToolError) as exc_info:
                await graphiti_tools.delete_episode_impl(uuid="invalid-uuid")

            assert "DELETE_EPISODE_ERROR" in str(exc_info.value)


class TestDeleteEntityEdgeImpl:
    """Test delete_entity_edge_impl function."""

    @pytest.mark.asyncio
    async def test_delete_entity_edge_success(self, mock_env_vars, mock_client):
        """
        Test Case: delete_entity_edge運作正常
        Given: 已存在的entity edge UUID
        When: Calling delete_entity_edge_impl()
        Then: Entity edge成功刪除
        """
        mock_client.delete_entity_edge.return_value = True

        with patch("rbt_mcp_server.graphiti_tools.get_graphiti_client", return_value=mock_client):
            result = await graphiti_tools.delete_entity_edge_impl(uuid="edge-123")

            assert result == {"message": "Successfully deleted entity edge edge-123"}
            mock_client.delete_entity_edge.assert_called_once_with("edge-123")

    @pytest.mark.asyncio
    async def test_delete_entity_edge_error(self, mock_env_vars, mock_client):
        """
        Test Case: delete_entity_edge handles errors
        Given: Invalid edge UUID
        When: Calling delete_entity_edge_impl()
        Then: ToolError is raised
        """
        mock_client.delete_entity_edge.side_effect = Exception("Edge not found")

        with patch("rbt_mcp_server.graphiti_tools.get_graphiti_client", return_value=mock_client):
            with pytest.raises(ToolError) as exc_info:
                await graphiti_tools.delete_entity_edge_impl(uuid="invalid-uuid")

            assert "DELETE_ENTITY_EDGE_ERROR" in str(exc_info.value)
