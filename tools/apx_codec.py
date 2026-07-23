"""Encode AFL formula text for embedding in an .apx <FormulaContent> tag.

AmiBroker stores the formula with C-style escaping: backslash doubled and
newlines as the two characters \\r\\n (the whole formula is one XML line).
On load it unescapes. Embedding RAW text corrupts the formula. See
ORB/lessons/apx-formulacontent-escaping.md.
"""

import html


def encode_formula(afl_text: str) -> str:
    t = afl_text.replace("\\", "\\\\")
    t = t.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\r\\n")
    return html.escape(t, quote=False)
