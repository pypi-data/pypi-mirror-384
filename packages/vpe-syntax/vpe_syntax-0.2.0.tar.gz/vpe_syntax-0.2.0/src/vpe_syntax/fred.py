"""Temp embedded highlighting code."""

from vpe_syntax import EmbeddedHighlighter


class MyEmbeddedHighlighter(EmbeddedHighlighter):
    """Just for development."""

    def find_embedded_code(
            self, lines: list[str],
        ) -> list[list[tuple[int, int, int]]]:
        """Find all blocks of embedded code.

        :return:
            A list of embedded code blocks. Each block is a list of line
            sections, where each section is a tuple of line_index, start_column
            and end_column. The start and end columns for a Python range. Each
            start column should be set to trim off any unwanted indentation.
        """
        in_code = False
        code_lines = []
        start_ind = 0
        code_ind = None

        for i, raw_line in enumerate(lines):
            line = raw_line.rstrip()
            if line.endswith(':<py>::'):
                start_ind = len(line) - len(line.lstrip())
                in_code = True
                code_ind = None
                continue

            if in_code:
                ind = len(line) - len(line.lstrip())
                if code_ind is None:
                    if not line.strip():
                        continue
                    code_ind = ind

                if line.strip():
                    if ind <= start_ind:
                        in_code = False
                        continue

                code_lines.append((i, code_ind or 0, len(line)))

        return [code_lines]
