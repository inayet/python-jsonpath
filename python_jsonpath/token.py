""""""
import sys

# Utility tokens
TOKEN_EOF = sys.intern("EOF")
TOKEN_ILLEGAL = sys.intern("ILLEGAL")
TOKEN_SKIP = sys.intern("SKIP")

# JSONPath expression tokens
TOKEN_BRACKET_PROPERTY = sys.intern("BRACKET_PROPERTY")
TOKEN_COLON = sys.intern("COLON")
TOKEN_COMMA = sys.intern("COMMA")
TOKEN_DDOT = sys.intern("DDOT")
TOKEN_DOT = sys.intern("DOT")
TOKEN_DOT_INDEX = sys.intern("DINDEX")
TOKEN_DOT_PROPERTY = sys.intern("DOT_PROPERTY")
TOKEN_FILTER_END = sys.intern("FILTER_END")
TOKEN_FILTER_START = sys.intern("FILTER_START")
TOKEN_IDENT = sys.intern("IDENT")
TOKEN_INDEX = sys.intern("IDX")
TOKEN_LIST_END = sys.intern("RBRACKET")
TOKEN_BARE_PROPERTY = sys.intern("BARE_PROPERTY")
TOKEN_LIST_SLICE = sys.intern("LSLICE")
TOKEN_LIST_START = sys.intern("LBRACKET")
TOKEN_PROPERTY = sys.intern("PROP")
TOKEN_QUESTION = sys.intern("QUESTION")
TOKEN_QUOTE_PROPERTY = sys.intern("QUOTE_PROPERTY")
TOKEN_ROOT = sys.intern("ROOT")
TOKEN_SLICE = sys.intern("SLICE")
TOKEN_SLICE_START = sys.intern("SLICE_START")
TOKEN_SLICE_STEP = sys.intern("SLICE_STEP")
TOKEN_SLICE_STOP = sys.intern("SLICE_STOP")
TOKEN_WILD = sys.intern("WILD")

# Filter expression tokens
TOKEN_AND = sys.intern("AND")
TOKEN_BLANK = sys.intern("BLANK")
TOKEN_CONTAINS = sys.intern("CONTAINS")
TOKEN_EMPTY = sys.intern("EMPTY")
TOKEN_EQ = sys.intern("EQ")
TOKEN_FALSE = sys.intern("FALSE")
TOKEN_FLOAT = sys.intern("FLOAT")
TOKEN_GE = sys.intern("GE")
TOKEN_GT = sys.intern("GT")
TOKEN_IN = sys.intern("IN")
TOKEN_INT = sys.intern("INT")
TOKEN_LE = sys.intern("LE")
TOKEN_LG = sys.intern("LG")
TOKEN_LPAREN = sys.intern("LPAREN")
TOKEN_LT = sys.intern("LT")
TOKEN_NE = sys.intern("NE")
TOKEN_NIL = sys.intern("NIL")
TOKEN_NONE = sys.intern("NONE")
TOKEN_NOT = sys.intern("NOT")
TOKEN_NULL = sys.intern("NULL")
TOKEN_OP = sys.intern("OP")
TOKEN_OR = sys.intern("OR")
TOKEN_RE = sys.intern("RE")
TOKEN_RE_FLAGS = sys.intern("RE_FLAGS")
TOKEN_RE_PATTERN = sys.intern("RE_PATTERN")
TOKEN_RPAREN = sys.intern("RPAREN")
TOKEN_SELF = sys.intern("SELF")
TOKEN_STRING = sys.intern("STRING")
TOKEN_TRUE = sys.intern("TRUE")
TOKEN_UNDEFINED = sys.intern("UNDEFINED")
TOKEN_MISSING = sys.intern("MISSING")

# Extension tokens
TOKEN_UNION = sys.intern("UNION")
TOKEN_INTERSECTION = sys.intern("INTERSECT")


# pylint: disable=too-few-public-methods
class Token:
    """A token, as returned from :meth:`lex.Lexer.tokenize`."""

    __slots__ = ("kind", "value", "index", "path")

    def __init__(
        self,
        kind: str,
        value: str,
        index: int,
        path: str,
    ) -> None:
        self.kind = kind
        self.value = value
        self.index = index
        self.path = path

    def __repr__(self) -> str:
        return (
            f"Token(kind={self.kind!r}, value={self.value!r}, "
            f"index={self.index}, path={self.path!r})"
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Token)
            and self.kind == other.kind
            and self.value == other.value
            and self.index == other.index
            and self.path == other.path
        )