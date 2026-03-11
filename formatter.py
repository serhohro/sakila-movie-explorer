import textwrap

class Formatter:

    DEFAULT_CONFIG = {
        "border": True,
        "max_col_width": 30,
        "wrap": True,
        "truncate": False,
        "header_align": "center",
        "header_bold": None,
        "header_capitalize": True,
        "header_custom": None,
        "align": "left",
        "id_align_right": True,
        "color_header": "\033[93m",
        "color_reset": "\033[0m",
        "border_chars": {
            "h": "═",
            "v": "║",
            "c": "╬"
        },
        "zebra": False,
        "zebra_colors": ("\033[48;5;235m", "\033[0m"),
    }

    def __init__(self, config=None):
        self.config = self.DEFAULT_CONFIG.copy()
        if config:
            for k, v in config.items():
                if isinstance(v, dict) and k in self.config:
                    self.config[k].update(v)
                else:
                    self.config[k] = v

    def _apply_color(self, text, color=None):
        if not color:
            return text
        return f"{color}{text}{self.config['color_reset']}"

    def _format_header(self, name):
        if self.config["header_capitalize"]:
            name = name.capitalize()
        if self.config["header_bold"]:
            name = f"\033[1m{name}\033[0m"
        return name

    def _wrap_text(self, text, width):
        if self.config["truncate"]:
            return [text[:width]]
        wrapped = textwrap.wrap(text, width=width)
        return wrapped or [""]

    def _align_text(self, text, width, align):
        if align == "right":
            return text.rjust(width)
        elif align == "center":
            return text.center(width)
        return text.ljust(width)

    def make_table(self, rows):
        if not rows:
            return ""

        cfg = self.config
        bc = cfg["border_chars"]

        # Заголовки
        if cfg["header_custom"]:
            headers = cfg["header_custom"]
        else:
            headers = list(rows[0].keys())

        # --------------------------
        # 1. Вычисляем ширину колонок (учитывая данные и заголовки)
        # --------------------------
        col_widths = [len(h) for h in headers]

        for row in rows:
            for i, h in enumerate(headers):
                val = str(row[h])
                # Разделяем на строки для wrap
                wrapped = self._wrap_text(val, cfg["max_col_width"])
                max_len = max(len(line) for line in wrapped)
                if max_len > col_widths[i]:
                    col_widths[i] = max_len
        # Ограничение максимальной ширины
        col_widths = [min(w, cfg["max_col_width"]) for w in col_widths]

        # --------------------------
        # 2. Формируем заголовки
        # --------------------------
        header_cells = []
        for i, h in enumerate(headers):
            hn = self._format_header(h)
            hn = self._align_text(hn, col_widths[i], cfg["header_align"])
            hn = self._apply_color(hn, cfg["color_header"])
            header_cells.append(hn)

        # --------------------------
        # 3. Формируем строки данных
        # --------------------------
        str_rows = []
        for row in rows:
            wrapped_cols = []
            for i, h in enumerate(headers):
                val = str(row[h])
                if cfg["id_align_right"] and i == 0 and val.isdigit():
                    align = "right"
                else:
                    align = cfg["align"]

                wrapped = self._wrap_text(val, col_widths[i])
                wrapped_aligned = [self._align_text(line, col_widths[i], align) for line in wrapped]
                wrapped_cols.append(wrapped_aligned)
            str_rows.append(wrapped_cols)

        # --------------------------
        # 4. Генерация таблицы
        # --------------------------
        output = []
        output.append("\n")

        def make_sep():
            if not cfg["border"]:
                return None
            parts = [bc["h"] * w for w in col_widths]
            return bc["c"] + bc["c"].join(parts) + bc["c"]

        sep_line = make_sep()
        if sep_line:
            output.append(sep_line)

        if cfg["border"]:
            output.append(bc["v"] + bc["v"].join(header_cells) + bc["v"])
            output.append(sep_line)
        else:
            output.append(" | ".join(header_cells))
            output.append("-" * (sum(col_widths) + 3 * (len(col_widths) - 1)))

        for idx, row in enumerate(str_rows):
            max_lines = max(len(col) for col in row)
            for line_idx in range(max_lines):
                line_cells = []
                for i, col in enumerate(row):
                    line_cells.append(col[line_idx] if line_idx < len(col) else " " * col_widths[i])
                line_str = (bc["v"] if cfg["border"] else "").join(line_cells)
                if cfg["border"]:
                    line_str = bc["v"] + line_str + bc["v"]
                # Зебра
                if cfg["zebra"] and (idx % 2 == 0):
                    start, end = cfg["zebra_colors"]
                    line_str = start + line_str + end
                output.append(line_str)
            if sep_line:
                output.append(sep_line)

        return "\n".join(output)