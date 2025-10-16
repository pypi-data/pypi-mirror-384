import re
from typing import str


def clean_html_content(value: str) -> str:
    """Convert HTML content to docxtpl-compatible inline formatting."""
    if not isinstance(value, str):
        return value
    
    # First handle tables and lists
    if '<table>' in value:
        value = _convert_html_table(value)
    
    if '<ul>' in value or '<ol>' in value:
        value = _convert_html_lists(value)
    
    # Convert HTML formatting to docxtpl inline syntax
    # Bold: use {{r bold_text}}
    value = re.sub(r'<(b|strong)>(.*?)</\1>', r'{{\2|bold}}', value, flags=re.IGNORECASE)
    
    # Headings as bold
    for i in range(1, 7):
        value = re.sub(rf'<h{i}[^>]*>(.*?)</h{i}>', r'\n\n{{\1|bold}}\n', value, flags=re.IGNORECASE)
    
    # Italic
    value = re.sub(r'<(i|em)>(.*?)</\1>', r'{{\2|italic}}', value, flags=re.IGNORECASE)
    
    # Underline
    value = re.sub(r'<u>(.*?)</u>', r'{{\1|underline}}', value, flags=re.IGNORECASE)
    
    # Convert paragraphs and line breaks
    value = re.sub(r'<p[^>]*>', '\n\n', value)
    value = re.sub(r'</p>', '', value)
    value = re.sub(r'<br[^>]*/?>', '\n', value)
    
    # Remove remaining HTML tags
    value = re.sub(r'<[^>]+>', '', value)
    
    # Convert HTML entities
    value = _convert_html_entities(value)
    
    # Clean up extra whitespace
    value = re.sub(r'\n\s*\n\s*\n', '\n\n', value)
    value = re.sub(r'[ \t]+', ' ', value)
    
    return value.strip()


def _convert_html_table(value: str) -> str:
    """Convert HTML table to plain text."""
    headers = re.findall(r'<th[^>]*>(.*?)</th>', value, flags=re.IGNORECASE)
    
    rows = []
    row_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', value, flags=re.IGNORECASE)
    
    for row_html in row_matches:
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row_html, flags=re.IGNORECASE)
        if cells:
            cells = [re.sub(r'<[^>]+>', '', cell) for cell in cells]
            rows.append(cells)
    
    if not rows:
        return ''
    
    all_rows = rows
    if headers:
        all_rows = [headers] + rows
    
    max_widths = []
    for i in range(max(len(row) for row in all_rows) if all_rows else 0):
        max_width = max(len(str(row[i])) if i < len(row) else 0 for row in all_rows)
        max_widths.append(max(max_width, 8))
    
    result = []
    
    if headers:
        header_line = ' | '.join(headers[i].ljust(max_widths[i]) if i < len(headers) else ''.ljust(max_widths[i]) for i in range(len(max_widths)))
        separator = ' | '.join('-' * max_widths[i] for i in range(len(max_widths)))
        result.append(header_line)
        result.append(separator)
        rows = rows[1:] if len(rows) > 1 and headers == rows[0] else rows
    
    for row in rows:
        row_line = ' | '.join(str(row[i]).ljust(max_widths[i]) if i < len(row) else ''.ljust(max_widths[i]) for i in range(len(max_widths)))
        result.append(row_line)
    
    return '\n'.join(result)


def _convert_html_lists(value: str) -> str:
    """Convert HTML lists to plain text."""
    ol_pattern = r'<ol[^>]*>(.*?)</ol>'
    ol_matches = re.findall(ol_pattern, value, flags=re.IGNORECASE | re.DOTALL)
    
    for ol_content in ol_matches:
        items = re.findall(r'<li[^>]*>(.*?)</li>', ol_content, flags=re.IGNORECASE | re.DOTALL)
        formatted_items = []
        for i, item in enumerate(items, 1):
            clean_item = re.sub(r'<[^>]+>', '', item).strip()
            formatted_items.append(f'{i}. {clean_item}')
        
        list_text = '\n'.join(formatted_items)
        value = re.sub(ol_pattern, list_text, value, count=1, flags=re.IGNORECASE | re.DOTALL)
    
    ul_pattern = r'<ul[^>]*>(.*?)</ul>'
    ul_matches = re.findall(ul_pattern, value, flags=re.IGNORECASE | re.DOTALL)
    
    for ul_content in ul_matches:
        items = re.findall(r'<li[^>]*>(.*?)</li>', ul_content, flags=re.IGNORECASE | re.DOTALL)
        formatted_items = []
        for item in items:
            clean_item = re.sub(r'<[^>]+>', '', item).strip()
            formatted_items.append(f'• {clean_item}')
        
        list_text = '\n'.join(formatted_items)
        value = re.sub(ul_pattern, list_text, value, count=1, flags=re.IGNORECASE | re.DOTALL)
    
    return value


def _convert_html_entities(value: str) -> str:
    """Convert HTML entities."""
    entities = {
        '&nbsp;': ' ',
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&apos;': "'",
        '&copy;': '©',
        '&reg;': '®',
        '&trade;': '™',
        '&mdash;': '—',
        '&ndash;': '–',
        '&hellip;': '...',
        '&laquo;': '«',
        '&raquo;': '»',
        '&ldquo;': '"',
        '&rdquo;': '"',
        '&lsquo;': ''',
        '&rsquo;': ''',
    }
    
    for entity, replacement in entities.items():
        value = value.replace(entity, replacement)
    
    value = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), value)
    value = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), value)
    
    return value