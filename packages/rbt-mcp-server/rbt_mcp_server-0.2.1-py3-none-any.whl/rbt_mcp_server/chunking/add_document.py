"""
add_document MCP tool - Main entry point for document chunking and syncing to Graphiti.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-006-AddDocument

This module provides the primary interface for adding/updating documents in the Graphiti
knowledge graph. It orchestrates the entire pipeline from document reading to chunk
synchronization.
"""

import os
import logging
import asyncio
import shutil
import re
from typing import Optional
from pathlib import Path

from ..path_resolver import PathResolver
from .rbt_chunker import RBTChunker
from .markdown_chunker import MarkdownChunker
from .comparator import ChunkComparator
from .graphiti_client import GraphitiClient
from .models import ChunkMetadata, SyncResult

logger = logging.getLogger(__name__)


def _get_graphiti_client() -> GraphitiClient:
    """
    Create GraphitiClient from environment variables.

    This is a local version to avoid circular imports with graphiti_tools.
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

# Valid RBT document types
VALID_RBT_TYPES = {"REQ", "BP", "TASK"}


def _extract_document_id_from_frontmatter(content: str) -> Optional[str]:
    """
    Extract document ID from YAML frontmatter.

    Args:
        content: Document content with YAML frontmatter

    Returns:
        Document ID (e.g., "TASK-001-AddDocument") or None if not found

    Example:
        >>> content = "---\\nid: TASK-001-AddDocument\\n---\\n# Title"
        >>> _extract_document_id_from_frontmatter(content)
        'TASK-001-AddDocument'
    """
    # Match YAML frontmatter (between --- delimiters)
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not frontmatter_match:
        return None

    frontmatter = frontmatter_match.group(1)

    # Extract 'id' field from frontmatter
    id_match = re.search(r'^id:\s*(.+?)\s*$', frontmatter, re.MULTILINE)
    if not id_match:
        return None

    return id_match.group(1).strip()


async def add_document(
    new_file_path: str,
    project_id: str,
    feature_id: Optional[str],
    doc_type: Optional[str],
    file_path: Optional[str],
    root_dir: str,
    graphiti_client: GraphitiClient,
    sync_mode: bool = False
) -> SyncResult:
    """
    Compare new file with ROOT original file and sync differences to Graphiti.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument

    This is the main entry point for document comparison and syncing pipeline.
    It performs the following steps:
    1. Reads new file content
    2. Uses PathResolver to locate ROOT original file
    3. Reads ROOT original file content
    4. Chunks both new and old files
    5. Compares chunks to identify changes
    6. Synchronizes changes to Graphiti (add/update/delete episodes)
    7. Returns sync results

    Args:
        new_file_path: Absolute path to the new/modified file
        project_id: Project identifier (e.g., 'knowledge-smith')
        feature_id: Feature identifier (e.g., 'graphiti-chunk-mcp'), optional for general docs
        doc_type: Document type (e.g., 'REQ', 'BP', 'TASK', or None for general docs)
        file_path: TASK identifier or relative path for general documents
        root_dir: Root directory for document resolution
        graphiti_client: GraphitiClient instance for Graphiti operations
        sync_mode: If True, wait for Graphiti sync to complete (for testing).
                   If False (default), schedule Graphiti sync in background and return immediately.

    Returns:
        SyncResult containing statistics about added, updated, deleted, and unchanged chunks.
        Note: In background mode (sync_mode=False), the sync is scheduled but may not be
        complete when this function returns.

    Raises:
        FileNotFoundError: If new file or ROOT original file cannot be found
        ValueError: If invalid parameters provided
        RuntimeError: If Graphiti operations fail

    Examples:
        >>> # Sync TASK document
        >>> async with GraphitiClient(...) as client:
        ...     result = await add_document(
        ...         new_file_path="/path/to/TASK-006-AddDocument.md",
        ...         project_id="knowledge-smith",
        ...         feature_id="graphiti-chunk-mcp",
        ...         doc_type="TASK",
        ...         file_path="006",
        ...         root_dir="/path/to/root",
        ...         graphiti_client=client
        ...     )
        ...     print(f"Added: {len(result.added)}, Updated: {len(result.updated)}")
    """
    logger.info(f"Starting add_document: new_file={new_file_path}, "
                f"project_id={project_id}, feature_id={feature_id}, "
                f"doc_type={doc_type}, file_path={file_path}")

    try:
        # Step 0: Validate parameters
        logger.debug("Step 0: Validating parameters")

        # Validate doc_type
        if doc_type is not None and doc_type not in VALID_RBT_TYPES:
            raise ValueError(
                f"Invalid doc_type: '{doc_type}'. "
                f"Must be one of {sorted(VALID_RBT_TYPES)} for RBT documents, or None for general documents.\n"
                f"For general documents (e.g., todos, guides), set doc_type=None and use file_path "
                f"(e.g., file_path='todos/TODO-001.md')."
            )

        # Step 1: Validate and read new file
        logger.debug("Step 1: Reading new file")
        if not os.path.exists(new_file_path):
            raise FileNotFoundError(f"New file does not exist: {new_file_path}")

        with open(new_file_path, 'r', encoding='utf-8') as f:
            new_content = f.read()
        logger.info(f"Read {len(new_content)} characters from new file")

        # Step 1.5: For TASK documents, extract full task identifier from frontmatter if needed
        if doc_type == "TASK" and file_path:
            # Check if file_path is a simple number (e.g., "001")
            # If so, try to extract full task ID from document frontmatter
            if file_path.replace("TASK-", "").replace("-", "").isdigit():
                logger.debug("Step 1.5: Extracting full TASK identifier from frontmatter")
                doc_id = _extract_document_id_from_frontmatter(new_content)
                if doc_id and doc_id.startswith("TASK-"):
                    # Extract the full task identifier (e.g., "TASK-001-AddDocument" → "001-AddDocument")
                    task_full_id = doc_id.replace("TASK-", "", 1)
                    logger.info(f"Extracted full TASK identifier from frontmatter: {task_full_id}")
                    file_path = task_full_id
                else:
                    logger.warning(f"Could not extract TASK ID from frontmatter, using original file_path: {file_path}")

        # Step 2: Use PathResolver to locate ROOT original file
        logger.debug("Step 2: Resolving ROOT original file")
        resolver = PathResolver(root_dir=root_dir)

        try:
            old_path_info = resolver.resolve(
                project_id=project_id,
                feature_id=feature_id,
                doc_type=doc_type,
                file_path=file_path
            )
        except FileNotFoundError as e:
            # Enhance error message
            raise FileNotFoundError(
                f"Could not find ROOT original file\n"
                f"Please check parameters:\n"
                f"  project_id: {project_id}\n"
                f"  feature_id: {feature_id}\n"
                f"  doc_type: {doc_type}\n"
                f"  file_path: {file_path}\n"
                f"Original error: {e}"
            ) from e

        logger.info(f"Resolved ROOT file path: {old_path_info.file_path} (exists={old_path_info.file_exists})")

        # Step 3: Read ROOT original file content (if exists)
        if not old_path_info.file_exists:
            # ROOT file does not exist - treat as new document
            logger.info(f"ROOT file does not exist, treating as new document: {old_path_info.file_path}")
            old_chunks = []
        else:
            # ROOT file exists - read and chunk it
            logger.debug("Step 3: Reading ROOT original file")
            with open(old_path_info.file_path, 'r', encoding='utf-8') as f:
                old_content = f.read()
            logger.info(f"Read {len(old_content)} characters from ROOT file")

            # Chunk ROOT file
            logger.debug("Step 3b: Chunking ROOT file")
            old_chunks = _chunk_document(
                document_content=old_content,
                project_id=project_id,
                feature_id=feature_id or old_path_info.feature_id,
                doc_type=doc_type or old_path_info.doc_type
            )
            logger.info(f"Created {len(old_chunks)} chunks from ROOT file")

        # Step 4: Chunk new file
        logger.debug("Step 4: Chunking new file")
        new_chunks = _chunk_document(
            document_content=new_content,
            project_id=project_id,
            feature_id=feature_id or old_path_info.feature_id,
            doc_type=doc_type or old_path_info.doc_type
        )
        logger.info(f"Created {len(new_chunks)} chunks from new file")

        # Step 5: Compare chunks
        logger.debug("Step 5: Comparing chunks")
        comparator = ChunkComparator()
        sync_result = comparator.compare(old_chunks=old_chunks, new_chunks=new_chunks)
        logger.info(f"Comparison result: {len(sync_result.added)} added, "
                   f"{len(sync_result.updated)} updated, {len(sync_result.deleted)} deleted, "
                   f"{sync_result.unchanged} unchanged")

        # Step 6: Update ROOT file immediately after comparison
        logger.debug("Step 6: Updating ROOT file")
        _update_root_file(new_file_path, old_path_info.file_path)
        logger.info(f"Updated ROOT file: {old_path_info.file_path}")

        # Step 7: Synchronize changes to Graphiti
        if sync_mode:
            # Synchronous mode: Wait for Graphiti sync to complete
            logger.debug("Step 7: Synchronizing changes to Graphiti (sync mode)")
            await _sync_chunks_to_graphiti(
                graphiti_client=graphiti_client,
                new_chunks=new_chunks,
                sync_result=sync_result,
                project_id=project_id
            )
            logger.info("Successfully synchronized all changes to Graphiti (sync mode)")
        else:
            # Asynchronous mode: Schedule background synchronization
            logger.debug("Step 7: Scheduling background synchronization to Graphiti")
            asyncio.create_task(
                _sync_chunks_to_graphiti_background(
                    new_chunks=new_chunks,
                    sync_result=sync_result,
                    project_id=project_id
                )
            )
            logger.info("Background synchronization task scheduled")

        # Step 8: Return sync results
        logger.info(f"add_document completed successfully. Total chunks: {sync_result.total_chunks}")
        return sync_result

    except FileNotFoundError:
        raise
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in add_document: {e}", exc_info=True)
        raise RuntimeError(f"Failed to add document: {e}") from e


def _chunk_document(
    document_content: str,
    project_id: str,
    feature_id: Optional[str],
    doc_type: Optional[str]
) -> list[ChunkMetadata]:
    """
    Chunk document based on document type.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument

    Args:
        document_content: Raw document content
        project_id: Project identifier
        feature_id: Feature identifier (optional)
        doc_type: Document type (None for general markdown files)

    Returns:
        List of ChunkMetadata objects
    """
    # For general files (doc_type=None), use "General" as default
    if doc_type is None:
        doc_type = "General"

    # Determine if this is an RBT document
    is_rbt_doc = doc_type in ['REQ', 'BP', 'TASK']

    if is_rbt_doc:
        # Use RBTChunker for RBT documents
        logger.debug(f"Using RBTChunker for doc_type={doc_type}")
        chunker = RBTChunker()
        chunks = chunker.chunk(
            document_content=document_content,
            project_id=project_id,
            feature_id=feature_id,
            doc_type=doc_type
        )
    else:
        # Use MarkdownChunker for general documents
        logger.debug(f"Using MarkdownChunker for doc_type={doc_type}")
        chunker = MarkdownChunker()
        chunks = chunker.chunk(
            document_content=document_content,
            project_id=project_id,
            feature_id=feature_id,
            doc_type=doc_type,
            file_path=""  # File path not needed for chunking
        )

    return chunks




def _update_root_file(new_file_path: str, root_file_path: str) -> None:
    """
    Update ROOT file by copying new file content.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument

    Args:
        new_file_path: Path to the new/modified file
        root_file_path: Path to the ROOT original file

    Raises:
        RuntimeError: If file copy fails
    """
    try:
        # Ensure parent directory exists
        root_dir = Path(root_file_path).parent
        root_dir.mkdir(parents=True, exist_ok=True)

        # Copy new file to ROOT location
        shutil.copy2(new_file_path, root_file_path)
        logger.info(f"Successfully updated ROOT file: {root_file_path}")
    except Exception as e:
        logger.error(f"Failed to update ROOT file {root_file_path}: {e}", exc_info=True)
        raise RuntimeError(f"Failed to update ROOT file: {e}") from e


async def _sync_chunks_to_graphiti_background(
    new_chunks: list[ChunkMetadata],
    sync_result: SyncResult,
    project_id: str
) -> None:
    """
    Background wrapper for Graphiti synchronization with error handling.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument

    This function creates its own GraphitiClient to avoid connection issues
    from the parent context closing. Any errors are logged but not raised.

    Note: ROOT file is already updated in the main flow before this background task starts.

    Args:
        new_chunks: List of new ChunkMetadata objects
        sync_result: SyncResult from comparison
        project_id: Project identifier for group_id
    """
    try:
        logger.info(f"Starting background Graphiti synchronization for project: {project_id}")

        # Create a new GraphitiClient for this background task
        graphiti_client = _get_graphiti_client()

        async with graphiti_client:
            await _sync_chunks_to_graphiti(
                graphiti_client=graphiti_client,
                new_chunks=new_chunks,
                sync_result=sync_result,
                project_id=project_id
            )

        logger.info(f"Background Graphiti synchronization completed successfully for project: {project_id}")
    except Exception as e:
        logger.error(
            f"Background Graphiti synchronization failed for project {project_id}: {e}",
            exc_info=True
        )
        # Don't raise - this is a background task


async def _sync_chunks_to_graphiti(
    graphiti_client: GraphitiClient,
    new_chunks: list[ChunkMetadata],
    sync_result: SyncResult,
    project_id: str
) -> None:
    """
    Synchronize chunk changes to Graphiti.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-006-AddDocument

    This function applies the changes identified by ChunkComparator to Graphiti:
    - Added chunks: Create new episodes
    - Updated chunks: Delete old episode and create new one
    - Deleted chunks: Remove episodes

    Args:
        graphiti_client: GraphitiClient instance
        new_chunks: List of new ChunkMetadata objects
        sync_result: SyncResult from comparison
        project_id: Project identifier for group_id

    Raises:
        RuntimeError: If any Graphiti operation fails
    """
    # Build chunk lookup map
    chunk_map = {chunk.metadata["chunk_id"]: chunk for chunk in new_chunks}

    # Handle added chunks
    for chunk_id in sync_result.added:
        chunk = chunk_map[chunk_id]
        logger.debug(f"Adding chunk: {chunk_id}")

        await graphiti_client.add_episode(
            name=chunk.metadata["chunk_id"],
            episode_body=chunk.content,
            source_description=f"Document chunk from {chunk.metadata['doc_type']}",
            group_id=project_id,
            uuid=None  # Let Graphiti generate UUID
        )
        logger.info(f"Added chunk: {chunk_id}")

    # Handle updated chunks
    for chunk_id in sync_result.updated:
        chunk = chunk_map[chunk_id]
        logger.debug(f"Updating chunk: {chunk_id}")

        # Delete old version
        # Note: We need to find the episode UUID for this chunk_id
        # Since we stored chunks with chunk_id as the episode name,
        # we need to search for the episode by name
        try:
            episodes = await graphiti_client.get_episodes(
                group_ids=[project_id],
                last_n=1000
            )

            # Find episode with matching name
            old_episode_uuid = None
            for episode in episodes:
                if episode.get('name') == chunk_id:
                    old_episode_uuid = episode.get('uuid')
                    break

            if old_episode_uuid:
                await graphiti_client.delete_episode(old_episode_uuid)
                logger.debug(f"Deleted old episode for chunk: {chunk_id}")
            else:
                logger.warning(f"Could not find old episode for chunk: {chunk_id}")

        except Exception as e:
            logger.warning(f"Failed to delete old episode for {chunk_id}: {e}")

        # Add new version
        await graphiti_client.add_episode(
            name=chunk.metadata["chunk_id"],
            episode_body=chunk.content,
            source_description=f"Document chunk from {chunk.metadata['doc_type']}",
            group_id=project_id,
            uuid=None
        )
        logger.info(f"Updated chunk: {chunk_id}")

    # Handle deleted chunks
    for chunk_id in sync_result.deleted:
        logger.debug(f"Deleting chunk: {chunk_id}")

        # Find and delete the episode
        try:
            episodes = await graphiti_client.get_episodes(
                group_ids=[project_id],
                last_n=1000
            )

            # Find episode with matching name
            episode_uuid = None
            for episode in episodes:
                if episode.get('name') == chunk_id:
                    episode_uuid = episode.get('uuid')
                    break

            if episode_uuid:
                await graphiti_client.delete_episode(episode_uuid)
                logger.info(f"Deleted chunk: {chunk_id}")
            else:
                logger.warning(f"Could not find episode to delete for chunk: {chunk_id}")

        except Exception as e:
            logger.error(f"Failed to delete chunk {chunk_id}: {e}")
            raise RuntimeError(f"Failed to delete chunk: {e}") from e

    logger.info(f"Synchronization complete: {len(sync_result.added)} added, "
               f"{len(sync_result.updated)} updated, {len(sync_result.deleted)} deleted")
