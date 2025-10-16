"""
Table handling module for docx-json-replacer.
Provides functionality to create and style tables from JSON data.
"""
from typing import Dict, Any, List, Union
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


class TableHandler:
    """Handles table creation and styling from JSON data"""
    
    @staticmethod
    def is_table_data(value: Any) -> bool:
        """Check if the value represents table data"""
        # Check for multi-table format with 'list' flag
        if isinstance(value, dict) and value.get('list') == True:
            return True

        if not isinstance(value, list):
            return False

        if len(value) == 0:
            return False

        # Check if it's a list of dictionaries with 'cells' key
        first_item = value[0]
        if isinstance(first_item, dict) and 'cells' in first_item:
            return True

        # Check if it's a list of lists (simple table)
        if isinstance(first_item, list):
            return True

        # Check if it's a list of dictionaries (data table)
        if isinstance(first_item, dict):
            return True

        return False

    @staticmethod
    def is_multi_table_data(value: Any) -> bool:
        """Check if the value represents multiple tables"""
        # Format 1: Object with 'list: true' flag
        if isinstance(value, dict) and value.get('list') == True:
            return True

        # Format 2: Check if it's an array of arrays where each sub-array is table data
        if isinstance(value, list) and len(value) > 0:
            first_item = value[0]
            # If the first item is itself a valid table structure (list of rows)
            if isinstance(first_item, list) and len(first_item) > 0:
                # Check if the first item's first element looks like table data
                first_row = first_item[0]
                if isinstance(first_row, (list, dict)):
                    # This might be [[table1_rows], [table2_rows]]
                    # Verify by checking if all items are table-like
                    return all(
                        isinstance(item, list) and len(item) > 0 and
                        isinstance(item[0], (list, dict))
                        for item in value[:min(2, len(value))]  # Check first 2 items
                    )

        return False
    
    @staticmethod
    def parse_html_table(html_content: str) -> List[Dict[str, Any]]:
        """Parse HTML table string into table data structure"""
        import re
        
        # Basic HTML table parsing
        rows = []
        
        # Find all <tr> tags
        tr_pattern = r'<tr[^>]*>(.*?)</tr>'
        tr_matches = re.findall(tr_pattern, html_content, re.IGNORECASE | re.DOTALL)
        
        for tr_content in tr_matches:
            # Find all <td> or <th> tags
            cell_pattern = r'<(?:td|th)[^>]*>(.*?)</(?:td|th)>'
            cells = re.findall(cell_pattern, tr_content, re.IGNORECASE | re.DOTALL)
            
            # Clean HTML from cell content
            cleaned_cells = []
            for cell in cells:
                # Remove HTML tags
                clean_cell = re.sub(r'<[^>]+>', '', cell).strip()
                cleaned_cells.append(clean_cell)
            
            if cleaned_cells:
                rows.append({'cells': cleaned_cells})
        
        return rows
    
    @staticmethod
    def process_multi_table_data(data: Any) -> List[Dict[str, Any]]:
        """
        Process data that represents multiple tables

        Args:
            data: Multi-table data in one of these formats:
                - Dict with 'list: true' and 'tables' array
                - Array of table data arrays

        Returns:
            List of table contexts for each table
        """
        tables = []

        # Format 1: Object with 'list' flag
        if isinstance(data, dict) and data.get('list') == True:
            tables_data = data.get('tables', [])

            # Check if tables_data contains rows that should be grouped into tables
            # If each item has 'cells' key, they might be rows to group
            if tables_data and all(isinstance(item, dict) and 'cells' in item for item in tables_data):
                # Look for natural breaks in the table data to split into multiple tables
                # We'll split when we see "Apartado 1." again (indicating a new table)
                current_table_rows = []

                for row_data in tables_data:
                    # Check if this is the start of a new table (Apartado 1.)
                    if (row_data.get('cells') and
                        len(row_data['cells']) > 0 and
                        isinstance(row_data['cells'][0], str) and
                        row_data['cells'][0].strip() == "Apartado 1."):

                        # If we have accumulated rows, create a table from them
                        if current_table_rows:
                            processed = TableHandler._process_styled_table(current_table_rows)
                            if processed.get('rows'):
                                tables.append(processed)
                            current_table_rows = []

                    # Add this row to the current table
                    current_table_rows.append(row_data)

                # Don't forget the last table
                if current_table_rows:
                    processed = TableHandler._process_styled_table(current_table_rows)
                    if processed.get('rows'):
                        tables.append(processed)
            else:
                # Original behavior: each item is a separate table
                for table_data in tables_data:
                    processed = TableHandler.process_table_data(table_data)
                    if processed.get('rows'):
                        tables.append(processed)

        # Format 2: Direct array of table arrays
        elif isinstance(data, list):
            # Check if this is multiple tables (array of arrays)
            if data and isinstance(data[0], list) and data[0] and isinstance(data[0][0], (list, dict)):
                for table_data in data:
                    processed = TableHandler.process_table_data(table_data)
                    if processed.get('rows'):
                        tables.append(processed)
            else:
                # Single table - process normally
                processed = TableHandler.process_table_data(data)
                if processed.get('rows'):
                    tables.append(processed)

        return tables

    @staticmethod
    def process_table_data(data: Union[List[Dict], List[List], str]) -> Dict[str, Any]:
        """
        Process various table data formats into a standardized structure

        Args:
            data: Table data in various formats:
                - List of dicts with 'cells' and optional 'style'
                - List of lists (simple rows)
                - List of dicts (data rows)
                - HTML table string

        Returns:
            Standardized table context for docxtpl. May include 'should_split' flag
            indicating that this data should be rendered as multiple separate tables.
        """
        # Handle HTML table strings
        if isinstance(data, str) and '<table' in data.lower():
            data = TableHandler.parse_html_table(data)

        if not isinstance(data, list) or len(data) == 0:
            return {'rows': []}

        first_item = data[0]

        # Format 1: List of dicts with 'cells' key (styled table)
        if isinstance(first_item, dict) and 'cells' in first_item:
            return TableHandler._process_styled_table(data)

        # Format 2: List of lists (simple table)
        elif isinstance(first_item, list):
            return TableHandler._process_simple_table(data)

        # Format 3: List of dicts (data table)
        elif isinstance(first_item, dict):
            result = TableHandler._process_data_table(data)
            # Check if the result indicates we should split into multiple tables
            if result.get('should_split'):
                # Convert each object into a separate key-value table
                split_tables = []
                for obj in result['split_data']:
                    split_tables.append(TableHandler._create_key_value_table(obj))
                return {'rows': [], 'should_split': True, 'split_tables': split_tables}
            return result

        return {'rows': []}
    
    @staticmethod
    def _process_styled_table(data: List[Dict]) -> Dict[str, Any]:
        """Process table with styling information - supports both row-level and cell-level styles"""
        rows = []
        for row_data in data:
            # Handle different formats
            if isinstance(row_data.get('cells'), list):
                cells = []
                cell_styles = row_data.get('cell_styles', [])
                row_style = row_data.get('style', {})

                for idx, cell_content in enumerate(row_data['cells']):
                    # Check if this is already a dict with content and style
                    if isinstance(cell_content, dict) and 'content' in cell_content:
                        cells.append(cell_content)
                    else:
                        # Build cell with individual style or row style
                        cell = {'content': str(cell_content)}

                        # Apply cell-specific style if available
                        if idx < len(cell_styles) and cell_styles[idx]:
                            cell['style'] = cell_styles[idx]
                        # Otherwise use row style if available
                        elif row_style:
                            cell['style'] = row_style
                        else:
                            cell['style'] = {}

                        cells.append(cell)

                row = {
                    'cells': cells,
                    'style': row_style  # Keep row style for compatibility
                }
            else:
                # Legacy format support
                row = {
                    'cells': [{'content': str(c), 'style': row_data.get('style', {})}
                             for c in row_data.get('cells', [])],
                    'style': row_data.get('style', {})
                }

            rows.append(row)

        return {'rows': rows, 'has_style': True}
    
    @staticmethod
    def _process_simple_table(data: List[List]) -> Dict[str, Any]:
        """Process simple list of lists table"""
        rows = []
        for row_data in data:
            rows.append({
                'cells': row_data,
                'style': {}
            })
        
        return {'rows': rows, 'has_style': False}
    
    @staticmethod
    def _create_key_value_table(obj: Dict) -> Dict[str, Any]:
        """
        Create a key-value table from a single dictionary object
        Each row shows: [Key] [Value]

        Args:
            obj: Dictionary to convert to key-value table

        Returns:
            Table data structure with key-value pairs
        """
        rows = []

        # Add header row
        rows.append({
            'cells': ['Field', 'Value'],
            'style': {'bg': '4472C4', 'color': 'FFFFFF', 'bold': True}
        })

        # Add data rows - one for each key-value pair
        for key, value in obj.items():
            rows.append({
                'cells': [str(key), str(value)],
                'style': {}
            })

        return {'rows': rows, 'has_style': True, 'has_headers': True}

    @staticmethod
    def _process_data_table(data: List[Dict], field_threshold: int = 5) -> Dict[str, Any]:
        """
        Process list of dictionaries as table with headers

        Args:
            data: List of dictionaries to convert to table
            field_threshold: If objects have more than this many fields, create separate tables
                           for each object instead of a single table with all objects as rows

        Returns:
            Table data structure, or a special marker indicating multiple tables needed
        """
        if not data:
            return {'rows': []}

        # Extract headers from first item keys
        headers = list(data[0].keys())
        num_fields = len(headers)

        # Check if we should create separate tables for each object
        # This is useful for arrays like joint_obligor_company where each object has many fields
        # Always split into N tables when objects have many fields, regardless of array length
        if num_fields > field_threshold:
            # Return a marker indicating this should be processed as multiple tables
            # Each object will get its own key-value table
            return {
                'rows': [],
                'should_split': True,
                'split_data': data
            }

        rows = []

        # Add header row with default styling
        rows.append({
            'cells': headers,
            'style': {'bg': '4472C4', 'color': 'FFFFFF', 'bold': True}
        })

        # Add data rows
        for item in data:
            cells = [str(item.get(key, '')) for key in headers]
            rows.append({
                'cells': cells,
                'style': {}
            })

        return {'rows': rows, 'has_style': True, 'has_headers': True}
    
    @staticmethod
    def create_table_context(key: str, value: Any) -> Dict[str, Any]:
        """
        Create table context for template rendering
        
        Args:
            key: The JSON key (e.g., 'input.otrosdocs')
            value: The table data
        
        Returns:
            Context dict with table data for docxtpl
        """
        if not TableHandler.is_table_data(value) and not (isinstance(value, str) and '<table' in value.lower()):
            return {key: value}
        
        table_data = TableHandler.process_table_data(value)
        
        # Create context with table data
        context = {
            f"{key}_table": table_data['rows'],
            f"{key}_has_style": table_data.get('has_style', False),
            f"{key}_has_headers": table_data.get('has_headers', False)
        }
        
        return context
    
    @staticmethod
    def apply_cell_style(cell, style: Dict[str, Any]) -> None:
        """
        Apply styling to a table cell
        
        Args:
            cell: docx table cell object
            style: Style dictionary with bg, color, bold, italic
        """
        if not style:
            return
        
        # Apply background color
        if 'bg' in style and style['bg']:
            TableHandler._set_cell_background(cell, style['bg'])
        
        # Apply text formatting
        if cell.paragraphs:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    if 'bold' in style:
                        run.bold = style['bold']
                    if 'italic' in style:
                        run.italic = style['italic']
                    # Note: Text color requires more complex handling
    
    @staticmethod
    def _set_cell_background(cell, color: str) -> None:
        """
        Set background color for a table cell
        
        Args:
            cell: docx table cell
            color: Hex color code (without #)
        """
        # Remove # if present
        color = color.replace('#', '')
        
        # Get or create cell properties
        tc_pr = cell._tc.get_or_add_tcPr()
        
        # Create shading element
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), color)
        
        # Remove existing shading if present
        existing_shd = tc_pr.find(qn('w:shd'))
        if existing_shd is not None:
            tc_pr.remove(existing_shd)
        
        # Add new shading
        tc_pr.append(shd)