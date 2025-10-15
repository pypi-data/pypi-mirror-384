from typing import List, Dict, Any, Optional
from parser import ParsedData, ParsedSection

# @REQ: REQ-md-json-converter
# @BP: BP-md-json-converter
# @TASK: TASK-md-json-converter-002-JsonBuilder

class JsonBuilder:
    """Builds the final nested JSON object from the intermediate parsed data."""

    def build_json(self, parsed_data: ParsedData) -> Dict[str, Any]:
        """Main method to construct the JSON dictionary."""
        
        # 1. Build the section hierarchy
        root_sections = self._build_hierarchy(parsed_data.sections)

        # 2. Assemble the final JSON object
        final_json = {
            "metadata": parsed_data.metadata,
            "info": parsed_data.info,
            "title": parsed_data.main_title,
            "sections": [self._section_to_dict(s) for s in root_sections]
        }

        return final_json

    def _build_hierarchy(self, flat_sections: List[ParsedSection]) -> List[ParsedSection]:
        """Converts a flat list of sections into a nested hierarchy."""
        if not flat_sections:
            return []

        # Create a dictionary for easy access
        section_map = {s.id: s for s in flat_sections}
        # Re-initialize sections to avoid duplication if this is re-run
        for s in flat_sections:
            s.sections = []

        root_sections = []
        parent_stack = []

        for section in flat_sections:
            while parent_stack and parent_stack[-1].level >= section.level:
                parent_stack.pop()

            if not parent_stack:
                root_sections.append(section)
            else:
                parent_id = parent_stack[-1].id
                section.parent_id = parent_id
                # Ensure sections attribute exists
                if not hasattr(section_map[parent_id], 'sections'):
                    section_map[parent_id].sections = []
                section_map[parent_id].sections.append(section)

            parent_stack.append(section)

        return root_sections

    def _section_to_dict(self, section: ParsedSection) -> Dict[str, Any]:
        """Recursively converts a ParsedSection object to a dictionary."""
        return {
            "id": section.id,
            "title": section.title,
            "summary": section.summary,
            "blocks": [self._block_to_dict(b) for b in section.blocks],
            "sections": [self._section_to_dict(s) for s in getattr(section, 'sections', [])]
        }

    def _block_to_dict(self, block) -> Dict[str, Any]:
        """Converts a ParsedBlock object to a dictionary."""
        block_dict = {
            "id": block.id,
            "type": block.type,
            "title": block.title
        }
        if block.type == 'list':
            block_dict['items'] = block.items
        else:
            block_dict['content'] = block.content
        return block_dict
