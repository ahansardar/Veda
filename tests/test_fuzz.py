from __future__ import annotations

import random

from veda.lexer import Lexer
from veda.parser import Parser


def test_fuzz_lexer_and_parser_do_not_crash() -> None:
    rng = random.Random(1337)
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789+-*/%()[]{}=<>!,:.#\" \n"

    for _ in range(200):
        s = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 200)))
        tokens, lex_errors = Lexer(s, filename="fuzz.veda").tokenize_with_errors()
        # parse_with_errors should never raise a non-Veda exception.
        Parser(tokens, source=s, filename="fuzz.veda").parse_with_errors()

