"""
Markdown chunker that splits documents by h3 headings.

@REQ: REQ-graphiti-chunk-mcp
@BP: BP-graphiti-chunk-mcp
@TASK: TASK-003-MarkdownChunker
"""

import re
import yaml
import datetime
from typing import List, Optional, Dict, Any
from .models import ChunkMetadata


class MarkdownChunker:
    """
    Chunks Markdown documents by h3 (###) headings.

    @REQ: REQ-graphiti-chunk-mcp
    @BP: BP-graphiti-chunk-mcp
    @TASK: TASK-003-MarkdownChunker

    This chunker identifies ### headings as chunk boundaries and generates
    stable chunk IDs based on heading slugs.
    """

    # Regex pattern to match h3 headings (### heading)
    H3_PATTERN = re.compile(r'^###\s+(.+)$', re.MULTILINE)

    def __init__(self):
        """Initialize the MarkdownChunker."""
        pass

    def chunk(
        self,
        document_content: str,
        project_id: str,
        feature_id: Optional[str],
        doc_type: str,
        file_path: str
    ) -> List[ChunkMetadata]:
        """
        Chunk a Markdown document by h3 headings.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-003-MarkdownChunker

        Args:
            document_content: The full Markdown document content
            project_id: Project identifier
            feature_id: Feature identifier (None for general documents)
            doc_type: Document type (REQ/BP/TASK or custom)
            file_path: File path of the document

        Returns:
            List of ChunkMetadata objects, one per h3 section (or one for entire doc if no h3)

        Examples:
            >>> chunker = MarkdownChunker()
            >>> chunks = chunker.chunk(
            ...     "### Introduction\\nSome text\\n### Implementation\\nMore text",
            ...     "knowledge-smith",
            ...     "my-feature",
            ...     "REQ",
            ...     "docs/requirements.md"
            ... )
            >>> len(chunks)
            2
            >>> chunks[0].section_title
            'Introduction'
        """
        chunks: List[ChunkMetadata] = []

        # Check for info-section and extract it first
        content_after_info = document_content
        info_data = self._extract_info_section(document_content)

        if info_data:
            # Create info chunk
            info_chunk_id = self._generate_chunk_id(project_id, feature_id, "info")
            parent_document_id = self._generate_parent_id(project_id, feature_id, doc_type)

            chunks.append(ChunkMetadata(
                metadata={
                    "chunk_id": info_chunk_id,
                    "parent_document_id": parent_document_id,
                    "project_id": project_id,
                    "feature_id": feature_id,
                    "doc_type": doc_type,
                    "section_id": "info",
                    "section_title": "Info Section",
                    "section_summary": None,
                    "info": info_data["info"]
                },
                content=info_data["content"]
            ))

            # Remove info section from content for h3 processing
            content_after_info = info_data["remaining_content"]

        # Find all code block ranges (fenced code blocks with ```)
        code_block_ranges = self._find_code_block_ranges(content_after_info)

        # Find all h3 headings and their positions
        all_h3_matches = list(self.H3_PATTERN.finditer(content_after_info))

        # Filter out h3 headings that are inside code blocks
        h3_matches = [
            match for match in all_h3_matches
            if not self._is_inside_code_block(match.start(), code_block_ranges)
        ]

        if not h3_matches:
            # No h3 headings found - return entire document as one chunk (if not already returned info chunk)
            if not chunks:  # Only if no info chunk was created
                chunk_id = self._generate_chunk_id(project_id, feature_id, "document")
                parent_document_id = self._generate_parent_id(project_id, feature_id, doc_type)

                chunks.append(ChunkMetadata(
                    metadata={
                        "chunk_id": chunk_id,
                        "parent_document_id": parent_document_id,
                        "project_id": project_id,
                        "feature_id": feature_id,
                        "doc_type": doc_type,
                        "section_id": None,
                        "section_title": None,
                        "section_summary": None
                    },
                    content=content_after_info
                ))
            return chunks

        # Process each h3 section
        for i, match in enumerate(h3_matches):
            heading_text = match.group(1).strip()
            heading_slug = self._generate_slug(heading_text)

            # Determine content boundaries
            start_pos = match.start()
            end_pos = h3_matches[i + 1].start() if i + 1 < len(h3_matches) else len(content_after_info)

            # Extract section content
            section_content = content_after_info[start_pos:end_pos].strip()

            # Generate IDs
            chunk_id = self._generate_chunk_id(project_id, feature_id, heading_slug)
            parent_document_id = self._generate_parent_id(project_id, feature_id, doc_type)

            chunks.append(ChunkMetadata(
                metadata={
                    "chunk_id": chunk_id,
                    "parent_document_id": parent_document_id,
                    "project_id": project_id,
                    "feature_id": feature_id,
                    "doc_type": doc_type,
                    "section_id": heading_slug,
                    "section_title": heading_text,
                    "section_summary": None
                },
                content=section_content
            ))

        return chunks

    def _find_code_block_ranges(self, content: str) -> List[tuple]:
        """
        Find all fenced code block ranges in the content.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-003-MarkdownChunker

        Args:
            content: Document content

        Returns:
            List of (start_pos, end_pos) tuples for each code block
        """
        code_block_pattern = re.compile(r'^```.*?$', re.MULTILINE)
        matches = list(code_block_pattern.finditer(content))

        ranges = []
        i = 0
        while i < len(matches):
            # Opening fence
            start_pos = matches[i].start()
            # Find matching closing fence
            if i + 1 < len(matches):
                end_pos = matches[i + 1].end()
                ranges.append((start_pos, end_pos))
                i += 2  # Skip both opening and closing
            else:
                # Unclosed code block - treat rest of document as code
                ranges.append((start_pos, len(content)))
                break

        return ranges

    def _is_inside_code_block(self, position: int, code_block_ranges: List[tuple]) -> bool:
        """
        Check if a position is inside any code block.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-003-MarkdownChunker

        Args:
            position: Character position to check
            code_block_ranges: List of (start, end) tuples

        Returns:
            True if position is inside a code block, False otherwise
        """
        for start, end in code_block_ranges:
            if start <= position < end:
                return True
        return False

    def _convert_dates_to_iso(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively converts date/datetime objects in a dictionary to ISO 8601 strings.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-003-MarkdownChunker
        """
        if data is None:
            return None
        for key, value in data.items():
            if isinstance(value, (datetime.date, datetime.datetime)):
                data[key] = value.isoformat()
            elif isinstance(value, dict):
                data[key] = self._convert_dates_to_iso(value)
        return data

    def _extract_info_section(self, document_content: str) -> Optional[dict]:
        """
        Extract info-section from document if present.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-003-MarkdownChunker

        Args:
            document_content: Full document content

        Returns:
            Dictionary with 'info', 'content', and 'remaining_content' if info section exists, None otherwise
        """
        # Check if document has YAML header
        if not document_content.startswith('---'):
            return None

        # Split by YAML header
        parts = document_content.split('---\n', 2)
        if len(parts) < 3:
            return None

        # After YAML header
        after_yaml = parts[2]

        # Check for info-section marker
        if not after_yaml.strip().startswith('<!-- info-section -->'):
            return None

        lines = after_yaml.strip().split('\n')

        # Skip the info-section comment
        if lines[0] == '<!-- info-section -->':
            lines.pop(0)
        else:
            return None

        # Collect info lines (lines starting with >)
        info_lines = []
        while lines and lines[0].startswith('> '):
            info_lines.append(lines.pop(0)[2:])  # Remove '> ' prefix

        if not info_lines:
            return None

        # Parse info as YAML
        try:
            info_dict = yaml.safe_load('\n'.join(info_lines))
            # Convert date/datetime objects to ISO strings
            info_dict = self._convert_dates_to_iso(info_dict)
        except yaml.YAMLError:
            return None

        # Build info content (for chunk content)
        info_content_lines = ['<!-- info-section -->']
        for key, value in info_dict.items():
            info_content_lines.append(f'> {key}: {value}')

        info_content = '\n'.join(info_content_lines)

        # Remaining content is everything after info section
        remaining_content = '\n'.join(lines).strip()

        return {
            'info': info_dict,
            'content': info_content,
            'remaining_content': remaining_content
        }

    def _generate_slug(self, heading_text: str) -> str:
        """
        Generate a URL-friendly slug from heading text.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-003-MarkdownChunker

        Args:
            heading_text: The heading text to slugify

        Returns:
            Lowercase slug with special characters removed and spaces replaced with hyphens

        Examples:
            >>> chunker = MarkdownChunker()
            >>> chunker._generate_slug("Hello World!")
            'hello-world'
            >>> chunker._generate_slug("Implementation & Testing")
            'implementation-testing'
            >>> chunker._generate_slug("1. 任務目標與前置")
            '1-任務目標與前置'
        """
        # Convert to lowercase
        slug = heading_text.lower()

        # Replace spaces and underscores with hyphens
        slug = re.sub(r'[\s_]+', '-', slug)

        # Remove special characters except hyphens, alphanumerics, and unicode letters
        slug = re.sub(r'[^\w\-]', '', slug, flags=re.UNICODE)

        # Remove multiple consecutive hyphens
        slug = re.sub(r'-+', '-', slug)

        # Strip leading/trailing hyphens
        slug = slug.strip('-')

        return slug

    def _generate_chunk_id(
        self,
        project_id: str,
        feature_id: Optional[str],
        heading_slug: str
    ) -> str:
        """
        Generate a stable chunk ID.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-003-MarkdownChunker

        Args:
            project_id: Project identifier
            feature_id: Feature identifier (None for general documents)
            heading_slug: Slugified heading text

        Returns:
            Chunk ID in format: {project_id}+{feature_id or 'general'}+{heading_slug}

        Examples:
            >>> chunker = MarkdownChunker()
            >>> chunker._generate_chunk_id("knowledge-smith", "my-feature", "introduction")
            'knowledge-smith+my-feature+introduction'
            >>> chunker._generate_chunk_id("knowledge-smith", None, "overview")
            'knowledge-smith+general+overview'
        """
        feature_part = feature_id if feature_id else "general"
        return f"{project_id}+{feature_part}+{heading_slug}"

    def _generate_parent_id(
        self,
        project_id: str,
        feature_id: Optional[str],
        doc_type: str
    ) -> str:
        """
        Generate parent document ID.

        @REQ: REQ-graphiti-chunk-mcp
        @BP: BP-graphiti-chunk-mcp
        @TASK: TASK-003-MarkdownChunker

        Args:
            project_id: Project identifier
            feature_id: Feature identifier (None for general documents)
            doc_type: Document type

        Returns:
            Parent ID in format: {project_id}+{feature_id or 'general'}+{doc_type}

        Examples:
            >>> chunker = MarkdownChunker()
            >>> chunker._generate_parent_id("knowledge-smith", "my-feature", "REQ")
            'knowledge-smith+my-feature+REQ'
            >>> chunker._generate_parent_id("knowledge-smith", None, "Guide")
            'knowledge-smith+general+Guide'
        """
        feature_part = feature_id if feature_id else "general"
        return f"{project_id}+{feature_part}+{doc_type}"
