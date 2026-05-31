import textwrap
from typing import List, Dict, Any, Optional, Tuple, Final

class Formatter:
    """
    Class for visualising data as text-based tables in the console.
    Supports automatic word wrapping, color schemes, and zebra striping.
    """

    # Default configuration (Final indicates the constant nature of the dictionary)
    DEFAULT_CONFIG: Final[Dict[str, Any]] = {
        "border": True,               # Whether to draw table borders
        "max_col_width": 30,          # Maximum column width before wrapping text
        "wrap": True,                 # Whether to allow wrapping long text into new lines
        "truncate": False,            # Whether to truncate text instead of wrapping
        "header_align": "center",     # Header alignment (left, center, right)
        "header_bold": False,         # Whether to make headers bold (ANSI)
        "header_capitalize": True,    # Whether to capitalize headers
        "header_custom": None,        # List of custom header names
        "align": "left",              # Alignment of data inside cells
        "id_align_right": True,       # Whether to right-align the ID column
        "color_header": "\033[93m",   # Header color (yellow ANSI)
        "color_reset": "\033[0m",     # Color reset
        "border_chars": {             # Characters used to draw borders
            "h": "═",                 # Horizontal line
            "v": "║",                 # Vertical line
            "c": "╬"                  # Intersection
        },
        "zebra": False,               # Alternating row colors
        "zebra_colors": ("\033[48;5;235m", "\033[0m"), # Colors for zebra striping
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initializes the formatter with optional configuration overrides.
        :param config: Dictionary with user settings.
        """
        self.config = self.DEFAULT_CONFIG.copy()
        if config:
            for key, value in config.items():
                # Recursively update nested dictionaries (e.g., border characters)
                if isinstance(value, dict) and key in self.config:
                    self.config[key].update(value)
                else:
                    self.config[key] = value

    def _apply_color(self, text: str, color_code: Optional[str] = None) -> str:
        """Wraps text in ANSI color codes."""
        if not color_code:
            return text
        return f"{color_code}{text}{self.config['color_reset']}"

    def _wrap_cell_text(self, text: str, width: int) -> List[str]:
        """
        Splits cell text into lines based on the allowed width.
        :param text: Original source text.
        :param width: Maximum permitted column width.
        :return: A list of lines that fit within the specified width.
        """
        if self.config["truncate"]:
            return [text[:width]]
        
        # Use textwrap to automatically split by words
        wrapped_lines = textwrap.wrap(text, width=width)
        return wrapped_lines if wrapped_lines else [""]

    def _align_cell_content(self, text: str, width: int, alignment: str) -> str:
        """Aligns text within a cell using padding spaces."""
        if alignment == "right":
            return text.rjust(width)
        elif alignment == "center":
            return text.center(width)
        return text.ljust(width)

    def make_table(self, rows: List[Dict[str, Any]]) -> str:
        """
        Main method to generate a table string from a list of dictionaries.
        :param rows: Data formatted as [{'col1': val, 'col2': val}, ...].
        :return: A string representation of the table ready for printing.
        """
        if not rows:
            return "Empty dataset."

        cfg = self.config
        borders = cfg["border_chars"]

        # Determine headers (from the first dictionary or custom ones)
        headers = cfg["header_custom"] if cfg["header_custom"] else list(rows[0].keys())

        # 1. Calculate optimal column widths
        column_widths: List[int] = [len(str(h)) for h in headers]
        
        for row in rows:
            for i, header in enumerate(headers):
                cell_value = str(row.get(header, ""))
                # Check text length after virtual word wrapping
                wrapped = self._wrap_cell_text(cell_value, cfg["max_col_width"])
                max_line_in_cell = max(len(line) for line in wrapped)
                if max_line_in_cell > column_widths[i]:
                    column_widths[i] = max_line_in_cell

        # Enforce width constraints according to config limits
        column_widths = [min(width, cfg["max_col_width"]) for width in column_widths]

        # 2. Prepare header row
        formatted_headers: List[str] = []
        for i, header in enumerate(headers):
            display_name = header.capitalize() if cfg["header_capitalize"] else header
            aligned_header = self._align_cell_content(display_name, column_widths[i], cfg["header_align"])
            colored_header = self._apply_color(aligned_header, cfg["color_header"])
            formatted_headers.append(colored_header)

        # 3. Prepare data (split cells into lines)
        table_data_matrix: List[List[List[str]]] = []
        for row in rows:
            formatted_row_cols = []
            for i, header in enumerate(headers):
                val = str(row.get(header, ""))
                
                # Special alignment rules for IDs
                current_align = cfg["align"]
                if cfg["id_align_right"] and i == 0 and val.isdigit():
                    current_align = "right"

                lines = self._wrap_cell_text(val, column_widths[i])
                aligned_lines = [self._align_cell_content(l, column_widths[i], current_align) for l in lines]
                formatted_row_cols.append(aligned_lines)
            table_data_matrix.append(formatted_row_cols)

        # 4. Assemble final table string
        result_lines: List[str] = ["\n"]

        def create_separator() -> Optional[str]:
            """Generates a separator line based on column widths."""
            if not cfg["border"]: return None
            parts = [borders["h"] * width for width in column_widths]
            return borders["c"] + borders["c"].join(parts) + borders["c"]

        separator = create_separator()
        
        # Draw table top border
        if separator: result_lines.append(separator)
        
        header_line = (borders["v"] if cfg["border"] else " | ").join(formatted_headers)
        if cfg["border"]: header_line = borders["v"] + header_line + borders["v"]
        result_lines.append(header_line)
        
        if separator: result_lines.append(separator)

        # Draw data rows line by line
        for row_index, column_data in enumerate(table_data_matrix):
            # Find the maximum line count in the tallest cell of this row
            max_height = max(len(col_lines) for col_lines in column_data)
            
            for line_no in range(max_height):
                row_parts = []
                for col_index, lines_list in enumerate(column_data):
                    # If this cell has fewer lines than its neighbor, pad it with spaces
                    content = lines_list[line_no] if line_no < len(lines_list) else " " * column_widths[col_index]
                    row_parts.append(content)
                
                final_row_line = (borders["v"] if cfg["border"] else " | ").join(row_parts)
                if cfg["border"]: final_row_line = borders["v"] + final_row_line + borders["v"]

                # Apply zebra striping effect
                if cfg["zebra"] and (row_index % 2 == 0):
                    start_color, end_color = cfg["zebra_colors"]
                    final_row_line = f"{start_color}{final_row_line}{end_color}"
                
                result_lines.append(final_row_line)
            
            if separator: result_lines.append(separator)

        return "\n".join(result_lines)