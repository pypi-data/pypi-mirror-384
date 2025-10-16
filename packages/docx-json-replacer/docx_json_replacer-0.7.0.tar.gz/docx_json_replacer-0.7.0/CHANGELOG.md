# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2025-01-15

### Added
- **Formatting Preservation**: Placeholders now maintain their original formatting when replaced
  - Preserves bold, italic, underline, font size, font name, and font color
  - Works for both regular paragraphs and table cells
  - Handles placeholders split across multiple runs in Word documents

- **Cell Padding/Margins Support**: Added configurable padding for table cells
  - New `padding` property with top, bottom, left, right configuration
  - Supports multiple units: points (default), cm, inches, pixels
  - Properly sets Word XML cell margins (`tcMar`)

- **Enhanced Style Properties**
  - Added `font_size` property for cell text
  - Added `width` and `height` properties for cells with multiple unit support
  - Added `valign` property for vertical alignment (top, center, bottom)
  - Individual border configuration for each cell side

### Fixed
- **Fixed Formatting Loss Issues**
  - Fixed loss of formatting when replacing placeholders in regular paragraphs
  - Fixed loss of formatting when replacing placeholders in table cells
  - Fixed handling of placeholders split across multiple Word runs

- **Improved Placeholder Handling**
  - Unmatched placeholders are now removed instead of remaining in output
  - Better handling of complex placeholder patterns
  - More robust processing of nested table data

### Changed
- Refactored `_process_paragraphs` to work with runs instead of plain text
- Refactored `_process_tables` to reuse run-processing logic
- Added new `_process_paragraph_runs` method for formatting preservation
- Added new `_set_cell_padding` method for margin configuration
- Improved error handling and fallback behavior for invalid style values

## [0.6.4] - 2025-10-03

### Fixed
- **Always Create N Tables for Arrays with Many Fields**
  - Fixed logic to ALWAYS create separate tables for each item in arrays with many fields (>5)
  - Now creates N tables even for single-item arrays like `joint_obligor_company`
  - Each object in the array gets its own dedicated key-value table
  - Removed condition that required multiple items for splitting

## [0.6.3] - 2025-10-03

### Fixed
- **Array Objects with Many Fields Now Create Separate Tables**
  - Fixed issue where arrays of objects with many fields (>5) were merged into a single table
  - Arrays like `joint_obligor_company` now correctly create separate key-value tables for each object
  - Each object in the array gets its own table showing field names and values
  - Maintains backward compatibility for arrays with few fields (≤5 fields)

### Added
- **Key-Value Table Generation**
  - New method to create key-value tables from objects with many fields
  - Automatic detection of when to split arrays into multiple tables
  - Configurable field threshold for triggering the split behavior

## [0.6.2] - 2025-10-03

### Added
- **List Tables Support**
  - Support for generating multiple tables from a single placeholder
  - New `list: true` flag to indicate multi-table data
  - Automatic spacing between generated tables
  - Each table in the list can have its own styling and formatting

### Improved
- **Enhanced Stability**
  - More robust error handling in table generation
  - Better handling of malformed or unexpected data structures
  - Improved performance for large table datasets

### Changed
- Refined table insertion logic for better document structure
- Updated table styling system for more flexibility

## [0.6.1] - 2024-10-03

### Fixed
- **Critical Page Break Issue in Tables**
  - Fixed unwanted page breaks appearing after the first row of tables
  - Added `keepNext` and `keepLines` properties to paragraphs before tables
  - Implemented `cantSplit` property to prevent row splitting across pages
  - Changed row height rule from 'exact'/'atLeast' to 'auto' for flexible height
  - Empty placeholder paragraphs are now removed to avoid spacing issues
  - Added comprehensive page break prevention for both single and multi-table insertions

### Added
- New helper methods for page break prevention:
  - `_prevent_row_page_break()` - Prevents rows from splitting
  - `_set_paragraph_keep_with_next()` - Keeps paragraphs with following tables
  - `_set_table_no_page_break()` - Prevents table page breaks

### Changed
- Table insertion logic now removes empty placeholder paragraphs
- First row of tables receives special handling to prevent page breaks
- Improved table positioning relative to surrounding content

## [0.6.0] - 2024-09-30

### Added
- **HTML Formatting Support in Table Cells**
  - Support for `<b>`, `<strong>`, `<i>`, `<em>`, `<u>` tags for text formatting
  - Support for `<br>` line breaks and `<p>` paragraph tags
  - Smart handling of malformed HTML (unclosed tags, duplicate opening tags)

- **Cell-Level Styling**
  - Individual styling for each cell in a table row
  - New `cell_styles` array property for per-cell customization
  - Mixed styling support (row defaults with cell overrides)
  - Inline cell objects with `content` and `style` properties

- **Improved HTML Parser**
  - Sequential character-by-character parsing for better accuracy
  - Handles duplicate opening tags as closing tags
  - Properly processes nested and malformed HTML structures

### Changed
- Updated dependencies: `docxcompose>=1.3.0` (was `docxtpl>=0.20.0`)
- Improved table generation performance
- Better error handling for invalid table data

### Fixed
- Fixed issue where multiple `<b>` tags would make all text between them bold
- Fixed HTML tag processing in table cells preserving proper formatting
- Fixed style application priority (cell > row > default)

## [0.5.1] - 2024-01-15

### Fixed
- Bug fixes in table cell replacement

## [0.5.0] - 2024-01-10

### Added
- Table support with dynamic generation from JSON arrays
- Row-level styling for tables
- Background colors, text colors, bold, and italic support

## [0.4.0] - 2023-12-20

### Added
- Support for placeholders in table cells
- Batch processing capabilities

### Changed
- Improved placeholder detection algorithm

## [0.3.0] - 2023-11-15

### Added
- Support for nested JSON keys with dots (e.g., `client.name`)
- Command-line interface

## [0.2.0] - 2023-10-10

### Added
- HTML tag cleaning
- Support for headers and footers

## [0.1.0] - 2023-09-01

### Added
- Initial release
- Basic placeholder replacement in paragraphs
- JSON file support
- Python API