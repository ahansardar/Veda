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
        self._setup_input_and_history()

        self.output("Veda v1.0 REPL")
        self.output("Type 'exit' to quit.\n")

        filename = "<repl>"
        buffer_lines: list[str] = []
        interpreter: Optional[Interpreter] = None

        while True:
            prompt = "veda> " if not buffer_lines else "...  "
            line = self._prompt(prompt)
            if not buffer_lines and line.strip() == "exit":
                return

            if not buffer_lines and line.strip().startswith(":"):
                interpreter = self._handle_command(line.strip(), interpreter=interpreter)
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

    def _setup_input_and_history(self) -> None:
        """
        Prefer prompt_toolkit if installed for a nicer REPL experience.
        Otherwise use readline history when available (arrow-key history in many terminals).
        Falls back gracefully to plain input().
        """
        self._prompt = self.input_fn

        # Optional: prompt_toolkit gives a much better editing experience.
        # It is intentionally optional and controlled via `pip install -e .[repl]`.
        if self.input_fn is input:
            try:
                from prompt_toolkit import prompt as pt_prompt  # type: ignore
                from prompt_toolkit.history import FileHistory  # type: ignore

                history_file = Path.home() / ".veda_history"
                history = FileHistory(str(history_file))

                def _pt(prompt_text: str) -> str:
                    return pt_prompt(prompt_text, history=history)

                self._prompt = _pt
                self._history_file = history_file
                self._readline = None
                self._manual_history = []
                return
            except Exception:
                pass

        try:
            import readline  # type: ignore
        except Exception:
            self._readline = None
            self._history_file = None
            self._manual_history: list[str] = []
            self._prompt = self.input_fn
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
        if getattr(self, "_history_file", None) is not None and self._history_file.exists():
            try:
                lines = self._history_file.read_text(encoding="utf-8", errors="ignore").splitlines()
                for i, item in enumerate(lines[-20:], start=max(len(lines) - 20, 0) + 1):
                    if item.strip():
                        self.output(f"{i}: {item}")
                return
            except Exception:
                pass

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

        if getattr(self, "_history_file", None) is not None:
            try:
                self._history_file.write_text("", encoding="utf-8")
            except Exception:
                pass

    def _handle_command(self, line: str, *, interpreter: Optional[Interpreter]) -> Optional[Interpreter]:
        parts = line.split(maxsplit=1)
        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in {":help", ":h"}:
            self.output("Commands:")
            self.output("  :help              Show this help")
            self.output("  :history           Show recent history")
            self.output("  :clear             Clear history")
            self.output("  :vars              List global variables")
            self.output("  :reset             Reset REPL environment")
            self.output("  :load <file.veda>  Run a file into the current REPL env")
            return interpreter

        if cmd == ":history":
            self._print_history()
            return interpreter

        if cmd == ":clear":
            self._clear_history()
            self.output("History cleared.")
            return interpreter

        if cmd == ":reset":
            self.output("Environment reset.")
            return None

        if cmd == ":vars":
            if interpreter is None:
                self.output("(no variables yet)")
                return interpreter
            names = sorted(
                n for n in interpreter.globals.values.keys() if n not in getattr(interpreter, "builtin_names", set())
            )
            if not names:
                self.output("(no variables yet)")
                return interpreter
            for name in names:
                value = interpreter.globals.values.get(name)
                self.output(f"{name} = {value!r}")
            return interpreter

        if cmd == ":load":
            if not arg:
                self.output("Usage: :load path/to/file.veda")
                return interpreter
            path = Path(arg).expanduser()
            if not path.exists():
                self.output(f"File not found: {arg}")
                return interpreter
            source = path.read_text(encoding="utf-8")
            try:
                tokens = Lexer(source, filename=str(path)).tokenize()
                program = Parser(tokens, source=source, filename=str(path)).parse()
                if interpreter is None:
                    interpreter = Interpreter(
                        source=source,
                        filename=str(path),
                        output=self.output,
                        input_fn=self.input_fn,
                    )
                else:
                    interpreter.source = source
                    interpreter.filename = str(path)
                interpreter.run(program)
            except VedaError as e:
                self.output(e.pretty())
            return interpreter

        self.output("Unknown command. Try :help")
        return interpreter
