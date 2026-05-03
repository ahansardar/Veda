from __future__ import annotations
import ctypes
import os
from typing import Any, List, Tuple
from veda.token_types import Token, TokenType, KEYWORDS
from veda.errors import SourceSpan, VedaSyntaxError

# Structure must exactly match the C LexResult struct
class CLexResult(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("line", ctypes.c_int),
        ("column", ctypes.c_int),
        ("length", ctypes.c_int),
        ("start", ctypes.POINTER(ctypes.c_char)) # Use POINTER instead of c_char_p for safer slicing
    ]

class Lexer:
    def __init__(self, source: str, *, filename: str = "<stdin>"):
        self.source_str = source
        self.source_bytes = source.encode('utf-8')
        self.filename = filename
        
        # Cross-platform library loading
        ext = ".dll" if os.name == "nt" else ".so"
        lib_path = os.path.join(os.path.dirname(__file__), f"lexer{ext}")
        
        if not os.path.exists(lib_path):
            raise ImportError(f"Binary lexer not found at {lib_path}. Please compile the C source first.")
            
        try:
            self.lib = ctypes.CDLL(lib_path)
        except Exception as e:
            raise ImportError(f"Failed to load {lib_path}: {e}")

        self.lib.initScanner.argtypes = [ctypes.c_char_p]
        self.lib.next_token.restype = CLexResult

    def tokenize(self) -> List[Token]:
        tokens, errors = self.tokenize_with_errors()
        if errors:
            raise errors[0]
        return tokens

    def tokenize_with_errors(self) -> Tuple[List[Token], List[VedaSyntaxError]]:
        self.lib.initScanner(self.source_bytes)
        py_tokens: List[Token] = []
        errors: List[VedaSyntaxError] = []
        types_list = list(TokenType)

       # Change the mapping logic inside tokenize_with_errors:

        while True:
            res = self.lib.next_token()
            
            # C is 0-indexed, Python auto() is 1-indexed. 
            # If your res.type is 0 (EOF in C), types_list[0] is EOF in Python.
            # This works IF both lists are in the EXACT same order.
            t_type = types_list[res.type]

            #hasattr check or the new enum member
            if t_type.name == "ERROR":
                msg = ctypes.string_at(res.start).decode('utf-8')
                errors.append(VedaSyntaxError(msg, source=self.source_str, 
                             span=SourceSpan(self.filename, res.line, res.column, 1)))
                continue

            # Safely extract the lexeme using the length provided by C
            lexeme_bytes = ctypes.string_at(res.start, res.length)
            lexeme = lexeme_bytes.decode('utf-8')
            
            literal = self._process_literal(t_type, lexeme)
            
            # Double-check keywords if C didn't tag them
            if t_type == TokenType.IDENTIFIER and lexeme in KEYWORDS:
                t_type = TokenType.KEYWORD

            py_tokens.append(Token(
                type=t_type,
                lexeme=lexeme,
                literal=literal,
                filename=self.filename,
                line=res.line,
                column=res.column,
                length=res.length
            ))
            
            if t_type == TokenType.EOF:
                break

        return py_tokens, errors

    def _process_literal(self, t_type: TokenType, lexeme: str) -> Any:
        if t_type == TokenType.NUMBER:
            try:
                return float(lexeme) if "." in lexeme else int(lexeme)
            except ValueError:
                return 0
        if t_type == TokenType.STRING:
            # Strip quotes: handles "text" and """text"""
            content = lexeme[3:-3] if lexeme.startswith('"""') else lexeme[1:-1]
            return self._unescape(content)
        return None

    def _unescape(self, value: str) -> str:
        try:
            return value.encode('utf-8').decode('unicode_escape')
        except Exception:
            return value # Fallback to raw if escape is mangled