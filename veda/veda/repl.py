from __future__ import annotations

import atexit
from dataclasses import dataclass
from pathlib import Path
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
        self._setup_history()

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

            if not buffer_lines and line.strip() in {":help", "help"}:
                self.output("Commands: exit, :help, :history, :clear")
                continue
            if not buffer_lines and line.strip() == ":history":
                self._print_history()
                continue
            if not buffer_lines and line.strip() == ":clear":
                self._clear_history()
                continue

            if getattr(self, "_readline", None) is None:
                if not hasattr(self, "_manual_history"):
                    self._manual_history = []
                if line.strip():
                    self._manual_history.append(line)

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

    def _setup_history(self) -> None:
        """
        Use readline history when available (arrow-key history in many terminals).
        Falls back gracefully on environments without readline.
        """
        try:
            import readline  # type: ignore
        except Exception:
            self._readline = None
            self._history_file = None
            self._manual_history: list[str] = []
            return

        self._readline = readline
        self._history_file = Path.home() / ".veda_history"
        try:
            readline.read_history_file(str(self._history_file))
        except FileNotFoundError:
            pass
        except Exception:
            # History is a nice-to-have. REPL should still work.
            self._history_file = None

        atexit.register(self._save_history)

    def _save_history(self) -> None:
        if getattr(self, "_readline", None) is None:
            return
        if getattr(self, "_history_file", None) is None:
            return
        try:
            self._readline.write_history_file(str(self._history_file))
        except Exception:
            pass

    def _print_history(self) -> None:
        if getattr(self, "_readline", None) is not None:
            n = self._readline.get_current_history_length()
            start = max(n - 20, 1)
            for i in range(start, n + 1):
                item = self._readline.get_history_item(i)
                if item:
                    self.output(f"{i}: {item}")
            return
        # Manual history (when readline is unavailable)
        history = getattr(self, "_manual_history", [])
        for i, item in enumerate(history[-20:], start=max(len(history) - 20, 0) + 1):
            self.output(f"{i}: {item}")

    def _clear_history(self) -> None:
        if getattr(self, "_readline", None) is not None:
            try:
                self._readline.clear_history()
            except Exception:
                pass
            return
        self._manual_history = []
