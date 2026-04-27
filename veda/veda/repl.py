from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from veda.errors import VedaError
from veda.interpreter import Interpreter
from veda.lexer import Lexer
from veda.parser import Parser
from veda.token_types import TokenType


@dataclass
class Repl:
    output: Callable[[str], None] = print
    input_fn: Callable[[str], str] = input

    def run(self) -> None:
        self.output("Veda v1.0 REPL")
        self.output("Type 'exit' to quit.\n")

        filename = "<repl>"
        buffer_lines: list[str] = []
        interpreter: Optional[Interpreter] = None

        while True:
            prompt = "veda> " if not buffer_lines else "...  "
            line = self.input_fn(prompt)
            if not buffer_lines and line.strip() == "exit":
                return

            buffer_lines.append(line)
            source = "\n".join(buffer_lines) + "\n"

            try:
                if self._block_depth(source, filename) > 0:
                    continue

                tokens = Lexer(source, filename=filename).tokenize()
                program = Parser(tokens, source=source, filename=filename).parse()

                if interpreter is None:
                    interpreter = Interpreter(
                        source=source,
                        filename=filename,
                        output=self.output,
                        input_fn=self.input_fn,
                    )
                else:
                    interpreter.source = source

                interpreter.run(program)
                buffer_lines.clear()
            except VedaError as e:
                self.output(e.pretty())
                buffer_lines.clear()

    def _block_depth(self, source: str, filename: str) -> int:
        tokens = Lexer(source, filename=filename).tokenize()
        opens = 0
        closes = 0
        for t in tokens:
            if t.type == TokenType.KEYWORD and t.lexeme in {"when", "repeat", "count", "work"}:
                opens += 1
            if t.type == TokenType.KEYWORD and t.lexeme == "end":
                closes += 1
        return max(opens - closes, 0)

