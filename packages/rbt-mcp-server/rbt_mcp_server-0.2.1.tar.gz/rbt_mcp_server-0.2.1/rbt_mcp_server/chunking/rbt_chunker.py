"""
RBT document chunker.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-002-RBTChunker
"""

import re
from typing import Any, Dict, List, Optional
from ..converter import MarkdownConverter
from .models import ChunkMetadata


class RBTChunker:
    """
    Chunks RBT documents based on their structure.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-002-RBTChunker

    The chunker parses RBT documents and creates chunks for each section,
    generating stable chunk IDs based on the document structure.
    """

    def __init__(self):
        """
        Initialize RBTChunker.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-002-RBTChunker
        """
        self.converter = MarkdownConverter()

    def chunk(
        self,
        document_content: str,
        project_id: str,
        feature_id: str,
        doc_type: str
    ) -> List[ChunkMetadata]:
        """
        Chunk an RBT document into sections.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-002-RBTChunker

        Args:
            document_content: The raw markdown content of the RBT document
            project_id: Project identifier
            feature_id: Feature identifier
            doc_type: Document type (REQ/BP/TASK)

        Returns:
            List of ChunkMetadata objects, one for each section

        Example:
            >>> chunker = RBTChunker()
            >>> chunks = chunker.chunk(
            ...     document_content="# Title\\n\\n## Section\\n...",
            ...     project_id="knowledge-smith",
            ...     feature_id="graphiti-chunk-mcp",
            ...     doc_type="TASK"
            ... )
        """
        # Store original content for raw extraction
        self._document_content = document_content

        # Parse document to JSON structure
        doc_json = self.converter.to_json(document_content)

        # Generate parent document ID
        parent_document_id = f"{project_id}+{feature_id}+{doc_type}"

        # Extract metadata and info for chunk metadata
        document_metadata = doc_json.get("metadata", {})
        document_info = doc_json.get("info", {})

        # Start collecting chunks
        chunks: List[ChunkMetadata] = []

        # Create a chunk for info section if it exists and has content
        if document_info:
            info_chunk_id = f"{project_id}+{feature_id}+sec-info"
            info_content = self._generate_info_content(document_info)

            info_chunk_metadata = {
                "chunk_id": info_chunk_id,
                "parent_document_id": parent_document_id,
                "project_id": project_id,
                "feature_id": feature_id,
                "doc_type": doc_type,
                "section_id": "sec-info",
                "section_title": "Info Section",
                "section_summary": None,
                "info": document_info  # Only info chunk has info field
            }

            info_chunk = ChunkMetadata(
                metadata=info_chunk_metadata,
                content=info_content
            )
            chunks.append(info_chunk)

        # Process all sections recursively
        sections = doc_json.get("sections", [])
        for section in sections:
            self._process_section(
                section=section,
                project_id=project_id,
                feature_id=feature_id,
                doc_type=doc_type,
                parent_document_id=parent_document_id,
                chunks=chunks
            )

        return chunks

    def _process_section(
        self,
        section: Dict[str, Any],
        project_id: str,
        feature_id: str,
        doc_type: str,
        parent_document_id: str,
        chunks: List[ChunkMetadata],
        depth: int = 0
    ) -> None:
        """
        Recursively process a section and its nested sections.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-002-RBTChunker

        Args:
            section: Section data from JSON
            project_id: Project identifier
            feature_id: Feature identifier
            doc_type: Document type
            parent_document_id: Parent document identifier
            chunks: List to append chunks to
            depth: Current nesting depth
        """
        section_id = section.get("id")
        section_title = section.get("title")
        section_summary = section.get("summary")  # Can be None

        # Generate chunk_id
        chunk_id = f"{project_id}+{feature_id}+{section_id}"

        # Generate content for this section
        content = self._generate_section_content(section)

        # Build metadata dict with all required fields
        chunk_metadata = {
            "chunk_id": chunk_id,
            "parent_document_id": parent_document_id,
            "project_id": project_id,
            "feature_id": feature_id,
            "doc_type": doc_type,
            "section_id": section_id,
            "section_title": section_title,
            "section_summary": section_summary  # Will be None if not present
        }

        # Create chunk with new structure
        chunk = ChunkMetadata(
            metadata=chunk_metadata,
            content=content
        )

        chunks.append(chunk)

        # Process nested sections recursively
        nested_sections = section.get("sections", [])
        for nested_section in nested_sections:
            self._process_section(
                section=nested_section,
                project_id=project_id,
                feature_id=feature_id,
                doc_type=doc_type,
                parent_document_id=parent_document_id,
                chunks=chunks,
                depth=depth + 1
            )

    def _generate_section_content(self, section: Dict[str, Any]) -> str:
        """
        Generate markdown content for a section.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-002-RBTChunker

        Args:
            section: Section data from JSON

        Returns:
            Markdown content string for the section
        """
        section_id = section.get("id")

        # Extract raw section content from original markdown
        raw_content = self._extract_raw_section_content(section_id)

        if raw_content:
            return raw_content

        # Fallback to JSON-based generation if raw extraction fails
        lines = []

        # Add section title
        title = section.get("title", "")
        if title:
            lines.append(f"## {title}")
            lines.append("")

        # Add section summary if present
        summary = section.get("summary")
        if summary:
            lines.append(summary)
            lines.append("")

        # Add blocks
        blocks = section.get("blocks", [])
        for block in blocks:
            block_content = self._generate_block_content(block)
            if block_content:
                lines.append(block_content)
                lines.append("")

        return "\n".join(lines).strip()

    def _generate_info_content(self, info: Dict[str, Any]) -> str:
        """
        Generate markdown content for info section.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-002-RBTChunker

        Args:
            info: Info section data from JSON

        Returns:
            Markdown content string for the info section
        """
        lines = ["<!-- info-section -->"]

        # Add each field from info
        for key, value in info.items():
            lines.append(f"> {key}: {value}")

        return "\n".join(lines)

    def _generate_block_content(self, block: Dict[str, Any]) -> str:
        """
        Generate markdown content for a block.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-002-RBTChunker

        Args:
            block: Block data from JSON

        Returns:
            Markdown content string for the block
        """
        block_type = block.get("type", "")

        if block_type == "paragraph":
            return block.get("content", "")

        elif block_type == "code":
            language = block.get("language", "")
            content = block.get("content", "")
            return f"```{language}\n{content}\n```"

        elif block_type == "list":
            lines = []
            title = block.get("title")
            if title:
                lines.append(f"**{title}**")
                lines.append("")

            items = block.get("items", [])
            for item in items:
                lines.append(f"- {item}")

            return "\n".join(lines)

        elif block_type == "table":
            lines = []
            header = block.get("header", [])
            rows = block.get("rows", [])

            if header:
                # Header row
                lines.append("| " + " | ".join(header) + " |")
                # Separator row
                lines.append("| " + " | ".join(["---"] * len(header)) + " |")

            # Data rows
            for row in rows:
                lines.append("| " + " | ".join(row) + " |")

            return "\n".join(lines)

        else:
            # Unknown block type, return empty string
            return ""

    def _extract_raw_section_content(self, section_id: str) -> Optional[str]:
        """
        Extract raw section content from original markdown.

        This method finds the section by its ID comment and extracts all content
        until the next section ID comment or end of document.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-002-RBTChunker

        Args:
            section_id: Section ID to extract (e.g., "sec-data-structures")

        Returns:
            Raw markdown content for the section, or None if not found
        """
        if not hasattr(self, '_document_content'):
            return None

        content = self._document_content

        # Pattern to match section ID comment: <!-- id: sec-xxx -->
        section_pattern = rf'<!--\s*id:\s*{re.escape(section_id)}\s*-->'

        # Find the section start
        match = re.search(section_pattern, content)
        if not match:
            return None

        start_pos = match.end()

        # Find the next section ID comment or end of document
        # Pattern: <!-- id: sec-xxx --> or <!-- id: blk-xxx -->
        next_section_pattern = r'<!--\s*id:\s*sec-[\w-]+\s*-->'

        next_match = re.search(next_section_pattern, content[start_pos:])

        if next_match:
            end_pos = start_pos + next_match.start()
        else:
            end_pos = len(content)

        # Extract section content
        section_content = content[start_pos:end_pos].strip()

        return section_content
