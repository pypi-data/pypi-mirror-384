from typing import List, Tuple, Any, Optional

from .operators import OperatorRegistry, DEFAULT_OPERATORS

Token = Tuple[str, Any]  # (type, value)

_FIXED_KEYWORDS = {
    "true": ("BOOL", True),
    "false": ("BOOL", False),
    "null": ("NULL", None),
    "none": ("NULL", None),
    "not": ("NOT", "not"),
}

_BASE_SYMBOLS = {
    "(": "LPAREN",
    ")": "RPAREN",
    ".": "DOT",
    ",": "COMMA",
}


def tokenize(s: str, operators: Optional[OperatorRegistry] = None) -> List[Token]:
    import re

    ops = operators or DEFAULT_OPERATORS
    keyword_tokens = ops.keyword_tokens()
    symbol_tokens = _BASE_SYMBOLS.copy()
    symbol_tokens.update(ops.symbol_tokens())
    max_symbol_len = max((len(sym) for sym in symbol_tokens), default=0)

    tokens: List[Token] = []
    i = 0
    n = len(s)
    ws = re.compile(r"\s+")
    ident = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
    number = re.compile(r"(?:\d+\.\d*|\d*\.\d+|\d+)")
    string = re.compile(r"""('([^'\\]|\\.)*'|"([^"\\]|\\.)*")""")

    while i < n:
        m = ws.match(s, i)
        if m:
            i = m.end()
        if i >= n:
            break

        matched_symbol = False
        for length in range(max_symbol_len, 0, -1):
            if i + length > n:
                continue
            frag = s[i : i + length]
            token_type = symbol_tokens.get(frag)
            if token_type is not None:
                tokens.append((token_type, frag))
                i += length
                matched_symbol = True
                break
        if matched_symbol:
            continue

        m = string.match(s, i)
        if m:
            raw = m.group(0)
            string_val = bytes(raw[1:-1], "utf-8").decode("unicode_escape")
            tokens.append(("STRING", string_val))
            i = m.end()
            continue

        m = number.match(s, i)
        if m:
            numtxt = m.group(0)
            number_val = float(numtxt) if "." in numtxt else int(numtxt)
            tokens.append(("NUMBER", number_val))
            i = m.end()
            continue

        m = ident.match(s, i)
        if m:
            name = m.group(0)
            low = name.lower()
            fixed = _FIXED_KEYWORDS.get(low)
            if fixed is not None:
                tokens.append(fixed)
                i = m.end()
                continue
            op_token = keyword_tokens.get(low)
            if op_token is not None:
                tokens.append((op_token, low))
                i = m.end()
                continue

            tokens.append(("IDENT", name))
            i = m.end()
            continue

        raise SyntaxError(f"Unexpected character at {i}: {s[i]!r}")

    tokens.append(("EOF", None))
    return tokens
