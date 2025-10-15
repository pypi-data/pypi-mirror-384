import yaml
import re
from typing import List, Dict, Any, Optional

# @REQ: REQ-md-json-converter
# @BP: BP-md-json-converter
# @TASK: TASK-md-json-converter-003-Generator

class MarkdownGenerator:
    """Generates the custom Markdown format from a JSON object."""

    def generate_md(self, json_data: Dict[str, Any]) -> str:
        """Main method to generate the entire Markdown string."""
        md_parts = []

        # 1. Generate YAML front matter from metadata
        if 'metadata' in json_data:
            md_parts.append("---")
            for key, value in json_data['metadata'].items():
                md_parts.append(f"{key}: {value}")
            md_parts.append("---")

        # 2. Generate Info Section
        if 'info' in json_data and json_data['info'] is not None:
            md_parts.append("\n<!-- info-section -->")
            for key, value in json_data['info'].items():
                md_parts.append(f"> {key}: {value}")
        elif 'info' in json_data and json_data['info'] is None:
            # Empty info section
            md_parts.append("\n<!-- info-section -->")

        # 3. Generate Main Title
        if 'title' in json_data:
            md_parts.append("\n<!-- id: sec-root -->")
            md_parts.append(f"# {json_data['title']}")

        # 4. Generate Sections
        if 'sections' in json_data:
            md_parts.append(self._generate_sections(json_data['sections'], level=3))

        return "\n".join(md_parts)

    def _generate_sections(self, sections: List[Dict[str, Any]], level: int) -> str:
        section_parts = []
        for section in sections:
            section_parts.append(f"\n<!-- id: {section['id']} -->")
            section_parts.append(f"{ '#' * level} {section['title']}")

            if section.get('summary'):
                section_parts.append(f"\n[SUMMARY: {section['summary']}]")

            if section.get('blocks'):
                for block in section['blocks']:
                    section_parts.append(self._generate_block(block))

            if section.get('sections'):
                section_parts.append(self._generate_sections(section['sections'], level + 1))
        
        return "\n".join(section_parts)

    def _generate_block(self, block: Dict[str, Any]) -> str:
        block_parts = [f"\n<!-- id: {block['id']}, type: {block['type']} -->"]

        if block.get('title'):
            block_parts.append(f"**{block['title']}**")

        if block['type'] == 'list' and block.get('items'):
            for item in block['items']:
                # Ensure multiline items are indented correctly
                lines = str(item).split('\n')
                block_parts.append(f"  - {lines[0]}")
                for line in lines[1:]:
                    block_parts.append(f"  {line}")
        elif block.get('content'):  
            content = block['content']
            if block['type'] == 'code':
                lang = block.get('language', '')
                content = f"```{lang}\n{content}\n```"
            block_parts.append(content)

        return "\n".join(block_parts)