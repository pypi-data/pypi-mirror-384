import argparse
import json
from typing import Dict, Any
from .parser import MarkdownParser, ParsedData
from .builder import JsonBuilder
from .generator import MarkdownGenerator

# @REQ: REQ-md-json-converter
# @BP: BP-md-json-converter
# @TASK: TASK-md-json-converter-004-Converter-Class

class MarkdownConverter:
    """ 
    Main class providing a simple interface to convert Markdown to JSON and back.
    This class acts as a facade, orchestrating the parser, builder, and generator modules.
    """

    def __init__(self):
        """Initializes the converter and its components."""
        self.parser = MarkdownParser()
        self.builder = JsonBuilder()
        self.generator = MarkdownGenerator()

    def to_json(self, md_text: str) -> Dict[str, Any]:
        """
        Converts a Markdown string in the custom format to a structured JSON object.

        Args:
            md_text: The Markdown string to convert.

        Returns:
            A dictionary representing the structured JSON.
        """
        try:
            parsed_data = self.parser.parse(md_text)
            json_output = self.builder.build_json(parsed_data)
            return json_output
        except Exception as e:
            print(f"Error during MD to JSON conversion: {e}")
            # Re-raise or handle as needed
            raise

    def to_md(self, json_data: Dict[str, Any]) -> str:
        """
        Converts a structured JSON object back to a Markdown string in the custom format.

        Args:
            json_data: The dictionary to convert.

        Returns:
            A string representing the Markdown document.
        """
        try:
            md_output = self.generator.generate_md(json_data)
            return md_output
        except Exception as e:
            print(f"Error during JSON to MD conversion: {e}")
            # Re-raise or handle as needed
            raise


# @REQ: REQ-md-json-converter
# @BP: BP-md-json-converter
# @TASK: TASK-md-json-converter-005-CLI

def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to JSON or JSON to Markdown.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Subparser for 'to-json' command
    to_json_parser = subparsers.add_parser("to-json", help="Convert Markdown to JSON.")
    to_json_parser.add_argument("--input", "-i", required=True, help="Input Markdown file path.")
    to_json_parser.add_argument("--output", "-o", help="Output JSON file path (defaults to stdout).")

    # Subparser for 'to-md' command
    to_md_parser = subparsers.add_parser("to-md", help="Convert JSON to Markdown.")
    to_md_parser.add_argument("--input", "-i", required=True, help="Input JSON file path.")
    to_md_parser.add_argument("--output", "-o", help="Output Markdown file path (defaults to stdout).")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    converter = MarkdownConverter()

    try:
        if args.command == "to-json":
            with open(args.input, 'r', encoding='utf-8') as f:
                md_content = f.read()
            json_output = converter.to_json(md_content)
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(json_output, f, ensure_ascii=False, indent=2)
                print(f"Successfully converted '{args.input}' to '{args.output}'.")
            else:
                print(json.dumps(json_output, ensure_ascii=False, indent=2))

        elif args.command == "to-md":
            with open(args.input, 'r', encoding='utf-8') as f:
                json_input = json.load(f)
            md_output = converter.to_md(json_input)
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(md_output)
                print(f"Successfully converted '{args.input}' to '{args.output}'.")
            else:
                print(md_output)

    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{args.input}'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()