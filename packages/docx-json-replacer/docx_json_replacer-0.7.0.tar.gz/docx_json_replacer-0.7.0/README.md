# DOCX JSON Replacer

A powerful Python library for replacing template placeholders in DOCX files with JSON data. Supports advanced features like dynamic tables, HTML formatting in cells, and individual cell styling.

[![PyPI version](https://badge.fury.io/py/docx-json-replacer.svg)](https://badge.fury.io/py/docx-json-replacer)
[![Python Support](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 📝 **Simple placeholder replacement** in paragraphs and tables
- 🎨 **Formatting preservation** - Maintains font styles, sizes, and colors from templates (v0.7.0+)
- 📊 **Dynamic table generation** from JSON data
- 📐 **Cell padding/margins** - Configurable cell spacing and margins (v0.7.0+)
- 🎨 **Advanced table styling** with row-level and cell-level customization
- 🔤 **HTML formatting support** in table cells (`<b>`, `<i>`, `<u>`, `<br>`, `<p>`)
- 📚 **Multiple tables support** - Insert multiple tables from a single placeholder (v0.7.0+)
- 🎯 **Smart HTML tag handling** for malformed or duplicate tags
- 🚀 **Batch processing** capabilities
- 💻 **Command-line interface** for easy automation
- 🐍 **Simple Python API** for integration

## 📦 Installation

```bash
pip install docx-json-replacer
```

## 🚀 Quick Start

### Command Line

```bash
# Basic usage
docx-json-replacer template.docx data.json -o output.docx

# Without -o flag, creates template_replaced.docx
docx-json-replacer template.docx data.json
```

### Python API

```python
from docx_json_replacer import DocxReplacer

# Create replacer instance
replacer = DocxReplacer('template.docx')

# Replace with JSON data
json_data = {
    "name": "John Doe",
    "company": "Acme Corp",
    "table_data": [
        {
            "cells": ["Header 1", "Header 2", "Header 3"],
            "style": {"bg": "4472C4", "color": "FFFFFF", "bold": True}
        },
        {
            "cells": ["Row 1 Col 1", "Row 1 Col 2", "Row 1 Col 3"]
        }
    ]
}

replacer.replace_from_json(json_data)
replacer.save('output.docx')
```

## 📄 Template Format

Use double curly braces for placeholders:

```
Dear {{name}},

Welcome to {{company}}!

{{table_data}}
```

Placeholders work in:
- Regular paragraphs
- Table cells
- Headers and footers
- Nested structures with dots (e.g., `{{client.name}}`)

## 📊 Table Support

### Basic Table (List of Lists)
```json
{
  "simple_table": [
    ["Header 1", "Header 2"],
    ["Row 1 Col 1", "Row 1 Col 2"]
  ]
}
```

### Styled Table with Row-Level Styling
```json
{
  "styled_table": [
    {
      "cells": ["Header 1", "Header 2", "Header 3"],
      "style": {
        "bg": "4472C4",
        "color": "FFFFFF",
        "bold": true
      }
    },
    {
      "cells": ["Data 1", "Data 2", "Data 3"],
      "style": {
        "bg": "F2F2F2"
      }
    }
  ]
}
```

### Individual Cell Styling (v0.6.0+)
```json
{
  "cell_styled_table": [
    {
      "cells": ["Red Cell", "Green Cell", "Blue Cell"],
      "cell_styles": [
        {"bg": "FF0000", "color": "FFFFFF", "bold": true},
        {"bg": "00FF00", "color": "000000", "italic": true},
        {"bg": "0000FF", "color": "FFFFFF", "underline": true}
      ]
    }
  ]
}
```

### Mixed Row and Cell Styling
```json
{
  "mixed_table": [
    {
      "cells": ["Default", "Default", "Special"],
      "style": {"bg": "E7E6E6"},
      "cell_styles": [
        null,
        null,
        {"bg": "FFFF00", "bold": true}
      ]
    }
  ]
}
```

### HTML Formatting in Cells (v0.6.0+)
```json
{
  "html_table": [
    {
      "cells": [
        "Normal text",
        "<b>Bold text</b>",
        "<i>Italic</i> and <u>underline</u>"
      ]
    },
    {
      "cells": [
        "Line 1<br>Line 2<br>Line 3",
        "<b>Title</b><br><i>Subtitle</i>",
        "<p>Paragraph 1</p><p>Paragraph 2</p>"
      ]
    }
  ]
}
```

## 🎨 Style Properties

### Text Formatting
| Property | Description | Example |
|----------|-------------|---------|
| `bg` | Background color (hex without #) | `"4472C4"` |
| `color` | Text color (hex without #) | `"FFFFFF"` |
| `bold` | Bold text | `true`/`false` |
| `italic` | Italic text | `true`/`false` |
| `underline` | Underlined text | `true`/`false` |
| `font_size` | Font size in points | `10`, `12`, `14` |

### Cell Layout (v0.7.0+)
| Property | Description | Example |
|----------|-------------|---------|
| `width` | Cell width | `"4cm"`, `"2in"`, `"100pt"` |
| `height` | Cell height | `"2cm"`, `"1in"`, `"50pt"` |
| `align` | Horizontal alignment | `"left"`, `"center"`, `"right"` |
| `valign` | Vertical alignment | `"top"`, `"center"`, `"bottom"` |
| `padding` | Cell padding/margins | `{"top": 10, "bottom": 10, "left": 5, "right": 5}` |

### Borders (v0.7.0+)
| Property | Description | Example |
|----------|-------------|---------|
| `borders` | Cell borders | `{"top": {"size": 1, "color": "000000"}, "bottom": {...}}` |

### Style Priority Order
1. Inline cell object style (highest priority)
2. `cell_styles` array entry
3. Row `style` (lowest priority)

## 🔧 Advanced Usage

### Processing Multiple Files
```python
from docx_json_replacer import DocxReplacer
import json

# Process multiple documents
templates = ['template1.docx', 'template2.docx']
data_files = ['data1.json', 'data2.json']

for template, data_file in zip(templates, data_files):
    with open(data_file, 'r') as f:
        data = json.load(f)

    replacer = DocxReplacer(template)
    replacer.replace_from_json(data)
    replacer.save(f'output_{template}')
```

### Real-World Example: Invoice Generation
```python
from docx_json_replacer import DocxReplacer

invoice_data = {
    "invoice_number": "INV-2024-001",
    "date": "2024-01-15",
    "client.name": "ABC Corporation",
    "client.address": "123 Business St.",
    "items": [
        {
            "cells": ["Item", "Quantity", "Price", "Total"],
            "style": {"bg": "333333", "color": "FFFFFF", "bold": True}
        },
        {
            "cells": ["Widget A", "10", "$10.00", "$100.00"]
        },
        {
            "cells": ["Widget B", "5", "$20.00", "$100.00"]
        },
        {
            "cells": ["<b>Total</b>", "", "", "<b>$200.00</b>"],
            "cell_styles": [
                {"bg": "E7E6E6", "bold": True},
                {"bg": "E7E6E6"},
                {"bg": "E7E6E6"},
                {"bg": "E7E6E6", "bold": True}
            ]
        }
    ]
}

replacer = DocxReplacer('invoice_template.docx')
replacer.replace_from_json(invoice_data)
replacer.save('invoice_INV-2024-001.docx')
```

## 📋 Complete Example

### Template (template.docx)
```
Contract Number: {{contract_number}}
Client: {{client.name}}
Address: {{client.address}}

Items:
{{items}}

Terms: {{terms}}
```

### Data (data.json)
```json
{
    "contract_number": "2024-001",
    "client.name": "ABC Corporation",
    "client.address": "456 Business Ave",
    "items": [
        {
            "cells": ["Product", "Quantity", "Price"],
            "style": {"bg": "4472C4", "color": "FFFFFF", "bold": true}
        },
        {
            "cells": ["<b>Widget A</b>", "10", "$100"],
            "cell_styles": [{"bg": "E7E6E6"}, null, null]
        },
        {
            "cells": ["<b>Widget B</b>", "5", "$200"],
            "cell_styles": [{"bg": "E7E6E6"}, null, null]
        }
    ],
    "terms": "Payment due in 30 days"
}
```

### Command
```bash
docx-json-replacer template.docx data.json -o contract_2024_001.docx
```

## 🆕 What's New

### v0.7.0 (Latest)
- **Formatting Preservation**: Maintains font styles, sizes, and colors when replacing placeholders
- **Cell Padding/Margins**: Full control over cell spacing with configurable padding
- **Multiple Tables Support**: Insert multiple tables from a single placeholder
- **Enhanced Borders**: Individual border configuration for each cell side
- **Bug Fixes**: Fixed formatting loss in table cells and regular paragraphs

### v0.6.0
- **HTML Support in Tables**: Format text with `<b>`, `<i>`, `<u>`, `<br>`, and `<p>` tags
- **Cell-Level Styling**: Individual styling for each cell in a table
- **Smart Tag Handling**: Properly handles malformed or duplicate HTML tags
- **Improved Performance**: Optimized table generation and styling

## 📋 Requirements

- Python 3.7+
- python-docx >= 0.8.11
- docxcompose >= 1.3.0

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [python-docx](https://python-docx.readthedocs.io/)
- Table composition with [docxcompose](https://github.com/4teamwork/docxcompose)

## 📞 Support

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/liuspatt/docx-json-replacer/issues).

## 📚 Links

- [PyPI Package](https://pypi.org/project/docx-json-replacer/)
- [GitHub Repository](https://github.com/liuspatt/docx-json-replacer)
- [Documentation](https://github.com/liuspatt/docx-json-replacer#readme)