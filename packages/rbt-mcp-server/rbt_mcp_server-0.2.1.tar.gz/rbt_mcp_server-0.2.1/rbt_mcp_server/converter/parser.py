import re
import yaml
import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# @REQ: REQ-md-json-converter
# @BP: BP-md-json-converter
# @TASK: TASK-md-json-converter-001-Parser

# --- Intermediate Data Structures ---

@dataclass
class ParsedBlock:
    id: str
    type: str
    title: Optional[str] = None
    content: Optional[str] = None
    items: List[str] = field(default_factory=list)

@dataclass
class ParsedSection:
    id: str
    title: str
    level: int
    summary: Optional[str] = None
    blocks: List[ParsedBlock] = field(default_factory=list)
    # Temp fields for building hierarchy
    parent_id: Optional[str] = None

@dataclass
class ParsedData:
    metadata: Dict[str, Any] = field(default_factory=dict)
    info: Dict[str, Any] = field(default_factory=dict)
    main_title: str = ""
    sections: List[ParsedSection] = field(default_factory=list)


class MarkdownParser:
    """Parses the custom Markdown format into an intermediate structure."""

    def _convert_dates_to_iso(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively converts date/datetime objects in a dictionary to ISO 8601 strings."""
        if data is None:
            return None
        for key, value in data.items():
            if isinstance(value, (datetime.date, datetime.datetime)):
                data[key] = value.isoformat()
            elif isinstance(value, dict):
                data[key] = self._convert_dates_to_iso(value)
        return data

    def parse(self, md_text: str) -> ParsedData:
        """Main method to parse the entire Markdown string."""
        parsed_data = ParsedData()

        # 1. Split content into YAML, Info, and Main parts
        try:
            _, yaml_content, main_content = md_text.split('---\n', 2)
            parsed_data.metadata = yaml.safe_load(yaml_content)
            parsed_data.metadata = self._convert_dates_to_iso(parsed_data.metadata)
        except (ValueError, yaml.YAMLError) as e:
            raise ValueError(f"Error parsing YAML front matter: {e}")

        lines = main_content.strip().split('\n')

        # 2. Parse Info Section
        if lines and lines[0] == '<!-- info-section -->':
            lines.pop(0)
            info_lines = []
            while lines and lines[0].startswith('> '):
                info_lines.append(lines.pop(0)[2:])
            parsed_data.info = yaml.safe_load('\n'.join(info_lines))
            parsed_data.info = self._convert_dates_to_iso(parsed_data.info)
            if lines and not lines[0].strip(): lines.pop(0) # Pop blank line after info

        # 3. Parse Main Title and Root Section Comment
        if lines and lines[0] == '<!-- id: sec-root -->':
            lines.pop(0) # Consume the root section comment
            if lines and lines[0].startswith('# '):
                parsed_data.main_title = lines.pop(0).lstrip('# ').strip()
                if lines and not lines[0].strip(): lines.pop(0) # Pop blank line after title
            else:
                raise ValueError("Root section comment must be followed by a main title (#).")
        else:
            raise ValueError("Document must start with a root section comment (<!-- id: sec-root -->).")

        # 4. Parse Sections and Blocks
        current_section: Optional[ParsedSection] = None
        current_block_meta: Optional[Dict[str, str]] = None
        content_buffer: List[str] = []

        i = 0
        while i < len(lines):
            line = lines[i]
            comment_match = re.match(r'^<!--\s*(.*?)\s*-->$', line)

            if comment_match:
                # Finalize previous block if it exists and buffer is not empty
                if current_block_meta and content_buffer:
                    self._finalize_block(content_buffer, current_block_meta, current_section)
                    content_buffer.clear()

                meta_string = comment_match.group(1)
                meta = dict(re.findall(r'(\w+):\s*([^,]+(?:\s*[^,]+)*)', meta_string))
                
                # Check if next line is a section heading
                next_line_idx = i + 1
                next_line_is_section_heading = (next_line_idx < len(lines)) and re.match(r'^#+\s', lines[next_line_idx])

                if next_line_is_section_heading:
                    # This comment is for a section
                    current_section = self._create_section(meta, lines[next_line_idx])
                    parsed_data.sections.append(current_section)
                    current_block_meta = None # Ensure block meta is cleared for a new section
                    i += 1 # Consume the section title line

                    # Check for summary after section title
                    summary_line_idx = i + 1
                    if summary_line_idx < len(lines):
                        summary_line = lines[summary_line_idx].strip()
                        summary_match = re.match(r'^\[SUMMARY:(.*?)\]$', summary_line)
                        if summary_match:
                            current_section.summary = summary_match.group(1).strip()
                            i += 1 # Consume the summary line
                else:
                    # This comment is for a block
                    current_block_meta = meta
                    # The line after the comment is the start of the block content
                    # We don't consume it here, it will be consumed by the main loop
            elif re.match(r'^##\s', line):
                # Heading without id comment - auto-generate section
                # Finalize previous block first
                if current_block_meta and content_buffer:
                    self._finalize_block(content_buffer, current_block_meta, current_section)
                    content_buffer.clear()
                    current_block_meta = None

                # Auto-generate section id from heading text
                heading_text = line.lstrip('#').strip()
                auto_id = self._generate_section_id(heading_text)
                auto_meta = {'id': auto_id}

                current_section = self._create_section(auto_meta, line)
                parsed_data.sections.append(current_section)
            elif current_section:
                is_summary = re.match(r'^\[SUMMARY:(.*?)\]$', line)
                if is_summary:
                    current_section.summary = is_summary.group(1).strip()
                # Only append content if we are inside a section and it's not a heading
                elif not re.match(r'^#+\s', line):
                    content_buffer.append(line)

            i += 1 # Move to the next line

        # Finalize the very last block if any content remains
        if current_block_meta and content_buffer:
            self._finalize_block(content_buffer, current_block_meta, current_section)

        return parsed_data

    def _generate_section_id(self, heading_text: str) -> str:
        """
        Generate a section ID from heading text (auto-generate for sections without id comment).

        Examples:
            "Section 1" -> "sec-section-1"
            "1. 任務目標與前置" -> "sec-1-任務目標與前置"
            "Implementation & Testing" -> "sec-implementation-testing"
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

        # Add "sec-" prefix if not already present
        if not slug.startswith('sec-'):
            slug = f"sec-{slug}"

        return slug

    def _create_section(self, meta: Dict[str, str], title_line: str) -> ParsedSection:
        level = title_line.find(' ')
        title = title_line.lstrip('# ').strip()
        return ParsedSection(id=meta['id'], title=title, level=level)

    def _finalize_block(self, buffer: List[str], meta: Optional[Dict[str, str]], section: Optional[ParsedSection]):
        if not meta or not section:
            return

        content_str = '\n'.join(buffer).strip()
        if not content_str:
            return

        block = ParsedBlock(id=meta['id'], type=meta['type'])

        # Extract title if it exists (must be first line of content_str)
        lines = content_str.split('\n')
        first_line = lines[0].strip()
        # Check for bold title pattern: **Title** or **Title**:
        title_match = re.match(r'^\*\*(.*?)\*\*(:?)$', first_line)
        if title_match:
            block.title = title_match.group(1).strip()
            lines.pop(0)
            content_str = '\n'.join(lines).strip()

        # Process content based on type
        if block.type == 'list':
            # Remove all leading '-' and whitespace (handles nested lists)
            block.items = [
                re.sub(r'^[\s\-]+', '', line).strip()
                for line in content_str.split('\n')
                if line.strip()
            ]
        elif block.type == 'code':
            # For code, strip the ``` markers
            if content_str.startswith('```') and content_str.endswith('```'):
                content_str = '\n'.join(content_str.split('\n')[1:-1]).strip()
            block.content = content_str
        elif block.type in ['table', 'paragraph']:
            block.content = content_str
        
        section.blocks.append(block)