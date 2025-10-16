#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

# Handle both direct execution and module execution
try:
    from .docx_replacer import DocxReplacer
except ImportError:
    from docx_replacer import DocxReplacer


def main():
    parser = argparse.ArgumentParser(description='Replace template text in DOCX files with values from JSON')
    parser.add_argument('docx_file', help='Input DOCX file path')
    parser.add_argument('json_file', help='JSON file with replacement values')
    parser.add_argument('-o', '--output', help='Output DOCX file path (default: adds _replaced suffix)')

    args = parser.parse_args()

    docx_path = Path(args.docx_file)
    json_path = Path(args.json_file)

    if not docx_path.exists():
        print(f"Error: DOCX file '{docx_path}' not found", file=sys.stderr)
        sys.exit(1)

    if not json_path.exists():
        print(f"Error: JSON file '{json_path}' not found", file=sys.stderr)
        sys.exit(1)

    if args.output:
        output_path = args.output
    else:
        output_path = docx_path.stem + '_replaced' + docx_path.suffix

    try:
        replacer = DocxReplacer(str(docx_path))
        replacer.replace_from_json_file(str(json_path))
        replacer.save(output_path)
        print(f"Successfully created '{output_path}'")
    except Exception as e:
        print(f"Error processing files: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()