"""Support for syntax highlighting nested languages.

This module is mainly for documentation and example purposes.

Introduction
------------

The vpe_syntax plugin has limited support for syntax highlighting of nested
code. Two common examples are:

- Various languages embedded within HTML or a templating language.

- Code examples within comments. In this case the nested language is often the
  same as the main language in the file.

Blocks of such nested code can be sytax highlighted provided the following
conditions hold:

1. A block consists of a sequence of complete lines.

2. A block lies within a single Tree-sitter node's line range.

Taking Python as an example main language. The above rules mean that it is
practicable to highlight code examples within docstrings. However it is not
practicable within multiline coments because:

- The leading '#' characters on each line are part of the comment, which is
  prevented by rule 1.

- Each comment line is a separate Tree-sitter node, which makes rule 2 a
  blocker.

Note that rule 1 also works against a common C/C++ commenting style, like::

    /* Start of comment.
     *
     * Details, possibly including code examples.
     */

I hope that rule 1 may be relaxed in the future so that this style of C/C++
comment can be accomodated.

However, for many practical situations nested highlighting can be achieved.


How it works
------------

The vpe_syntax plugin provide most of the code to support nested highlights,
but a small amount of additional support code must be provided to identify
which lines contain nested code. This mechanism provide maximum flexibility
and keeps the basic syntax configuration files relatively simple.

A block of nested code is identified as follows:

    start_lidx
        The index of the first line of code.
    line_count
        The number of lines of code in the code block.
    indent
        The number of characters by which the code is indented. This number of
        characters is removed from each line before the code is processed.
"""
from vpe_syntax import EmbeddedHighlighter, NestedCodeBlockSpec


class MyEmbeddedHighlighter(EmbeddedHighlighter):
    """Just for development."""

    def find_embedded_code(
            self, lines: list[str]) -> list[NestedCodeBlockSpec]:
        """Find all blocks of embedded code.

        :return:
            A list of nested code specifications.
        """
        def store():
            nonlocal code_ind

            if code_ind is not None:
                blocks.append(NestedCodeBlockSpec(
                    start_lidx, line_count, code_ind))
                code_ind = None

        in_code = False
        start_ind = 0
        start_lidx = 0
        line_count = 0
        code_ind = None
        blocks = []

        for i, raw_line in enumerate(lines):
            line = raw_line.rstrip()
            if line.endswith(':<py>::') and not in_code:
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
                    start_lidx = i
                    line_count = 0

                if line.strip():
                    if ind <= start_ind:
                        in_code = False
                        store()
                        continue

                if code_ind is not None:
                    line_count += 1

        store()
        return blocks
