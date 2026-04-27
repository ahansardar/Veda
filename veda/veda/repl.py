from __future__ import annotations

import atexit
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from veda.errors import VedaError
from veda.interpreter import Interpreter
from veda.lexer import Lexer
from veda.options import InterpreterOptions
from veda.parser import Parser
from veda.token_types import TokenType


@dataclass
class Repl:
    output: Callable[[str], None] = print
    input_fn: Callable[[str], str] = input
    options: Optional[InterpreterOptions] = None

    def run(self) -> None:
        self._setup_input_and_history()

        self.output("Veda v1.0 REPL")
        self.output("Type 'exit' to quit.\n")

        filename = "<repl>"
        buffer_lines: list[str] = []
        interpreter: Optional[Interpreter] = None
        self._last_source: str | None = None
        self._last_filename: str | None = None
        self._last_tokens = None
        self._last_program = None

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
                self._last_source = source
                self._last_filename = filename
                self._last_tokens = tokens
                self._last_program = program

                if interpreter is None:
                    interpreter = Interpreter(
                        source=source,
                        filename=filename,
                        output=self.output,
                        input_fn=self.input_fn,
                        options=self.options,
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
            self.output("  :tokens [file]     Show tokens for last input (or a file)")
            self.output("  :ast [file]        Show AST for last input (or a file)")
            self.output("  :type <expr>       Evaluate and show the type of an expression")
            self.output("  :doc <name>        Show builtin docs/signature (if available)")
            self.output("  :check [file]      Run veda check for last input (or a file)")
            self.output("  :save <file.json>  Save variables (simple types only)")
            self.output("  :loadenv <json>    Load variables from a saved json file")
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
                        options=self.options,
                    )
                else:
                    interpreter.source = source
                    interpreter.filename = str(path)
                interpreter.run(program)
            except VedaError as e:
                self.output(e.pretty())
            return interpreter

        if cmd == ":tokens":
            self._show_tokens(arg)
            return interpreter

        if cmd == ":ast":
            self._show_ast(arg)
            return interpreter

        if cmd == ":type":
            if not arg:
                self.output("Usage: :type <expression>")
                return interpreter
            interpreter = interpreter or Interpreter(
                source="",
                filename="<repl>",
                output=self.output,
                input_fn=self.input_fn,
                options=self.options,
            )
            self._run_snippet(interpreter, f"show type({arg})\n", filename="<repl:type>")
            return interpreter

        if cmd == ":doc":
            if not arg:
                self.output("Usage: :doc <name>")
                return interpreter
            interpreter = interpreter or Interpreter(
                source="",
                filename="<repl>",
                output=self.output,
                input_fn=self.input_fn,
                options=self.options,
            )
            self._show_doc(interpreter, arg)
            return interpreter

        if cmd == ":check":
            self._repl_check(interpreter, arg)
            return interpreter

        if cmd == ":save":
            if not arg:
                self.output("Usage: :save path/to/file.json")
                return interpreter
            if interpreter is None:
                self.output("(no variables yet)")
                return interpreter
            self._save_env(interpreter, Path(arg).expanduser())
            return interpreter

        if cmd == ":loadenv":
            if not arg:
                self.output("Usage: :loadenv path/to/file.json")
                return interpreter
            interpreter = interpreter or Interpreter(
                source="",
                filename="<repl>",
                output=self.output,
                input_fn=self.input_fn,
                options=self.options,
            )
            self._load_env(interpreter, Path(arg).expanduser())
            return interpreter

        self.output("Unknown command. Try :help")
        return interpreter

    def _show_tokens(self, arg: str) -> None:
        try:
            if arg:
                path = Path(arg).expanduser()
                if not path.exists():
                    self.output(f"File not found: {arg}")
                    return
                source = path.read_text(encoding="utf-8")
                tokens = Lexer(source, filename=str(path)).tokenize()
            else:
                tokens = self._last_tokens
                if tokens is None:
                    self.output("(no previous input)")
                    return

            for t in tokens:
                if t.type == TokenType.NEWLINE:
                    continue
                self.output(f"{t.line}:{t.column}  {t.type.name:<12} {t.lexeme!r}")
        except VedaError as e:
            self.output(e.pretty())
        return

    def _show_ast(self, arg: str) -> None:
        try:
            if arg:
                path = Path(arg).expanduser()
                if not path.exists():
                    self.output(f"File not found: {arg}")
                    return
                source = path.read_text(encoding="utf-8")
                tokens = Lexer(source, filename=str(path)).tokenize()
                program = Parser(tokens, source=source, filename=str(path)).parse()
            else:
                program = self._last_program
                if program is None:
                    self.output("(no previous input)")
                    return
            self.output(repr(program))
        except VedaError as e:
            self.output(e.pretty())
        return

    def _run_snippet(self, interpreter: Interpreter, snippet: str, *, filename: str) -> None:
        try:
            tokens = Lexer(snippet, filename=filename).tokenize()
            program = Parser(tokens, source=snippet, filename=filename).parse()
            old_source = interpreter.source
            old_filename = interpreter.filename
            try:
                interpreter.source = snippet
                interpreter.filename = filename
                interpreter.run(program)
            finally:
                interpreter.source = old_source
                interpreter.filename = old_filename
        except VedaError as e:
            self.output(e.pretty())

    def _show_doc(self, interpreter: Interpreter, name: str) -> None:
        value = interpreter.globals.values.get(name)
        if value is None:
            self.output(f"(no such name: {name})")
            return

        # Builtins are instances of BuiltinFunction; user functions show as <work ...>.
        try:
            from veda.builtins import BuiltinFunction
        except Exception:
            BuiltinFunction = None  # type: ignore

        if BuiltinFunction is not None and isinstance(value, BuiltinFunction):
            if value.max_arity is None:
                sig = f"{name}(...)"
            elif value.min_arity == value.max_arity:
                sig = f"{name}({', '.join(['arg'] * value.min_arity)})"
            else:
                sig = f"{name}({value.min_arity}..{value.max_arity} args)"
            self.output(sig)
            doc = getattr(interpreter, "_builtin_docs", {}).get(name)
            if doc:
                self.output(doc)
            return

        self.output(f"{name} = {value!r}")

    def _repl_check(self, interpreter: Optional[Interpreter], arg: str) -> None:
        """
        Runs the same checks as `veda check`, but prints to the REPL.
        """
        from veda.builtins import BuiltinFunction
        from veda.checker import Checker

        if arg:
            path = Path(arg).expanduser()
            if not path.exists():
                self.output(f"File not found: {arg}")
                return
            source = path.read_text(encoding="utf-8")
            filename = str(path)
        else:
            if not self._last_source:
                self.output("(no previous input)")
                return
            source = self._last_source
            filename = self._last_filename or "<repl>"

        tokens, lex_errors = Lexer(source, filename=filename).tokenize_with_errors()
        _, parse_errors = Parser(tokens, source=source, filename=filename).parse_with_errors()
        errors: list[VedaError] = list(lex_errors) + list(parse_errors)

        if not errors:
            program, _ = Parser(tokens, source=source, filename=filename).parse_with_errors()
            tmp = interpreter or Interpreter(
                source=source,
                filename=filename,
                output=lambda s: None,
                input_fn=self.input_fn,
                options=self.options,
            )
            builtin_names = tmp.builtin_names | {"args"}
            builtin_arity: dict[str, tuple[int, int | None]] = {}
            for n, v in tmp.globals.values.items():
                if isinstance(v, BuiltinFunction):
                    builtin_arity[n] = (v.min_arity, v.max_arity)
            errors.extend(Checker(filename=filename, source=source, builtin_names=builtin_names, builtin_arity=builtin_arity).check(program))

        if not errors:
            self.output("OK")
            return

        errors = sorted(errors, key=lambda e: (e.span.line, e.span.column))
        for i, err in enumerate(errors):
            if i:
                self.output("")
            self.output(err.pretty())
        self.output(f"\nFound {len(errors)} error(s).")

    def _save_env(self, interpreter: Interpreter, path: Path) -> None:
        def _encode(value):
            if value is None or isinstance(value, (bool, int, float, str)):
                return value
            if isinstance(value, list):
                return [_encode(v) for v in value]
            if isinstance(value, dict):
                out = {}
                for k, v in value.items():
                    if not isinstance(k, str):
                        continue
                    out[k] = _encode(v)
                return out
            raise TypeError("unsupported")

        data = {}
        skipped = 0
        for name, value in interpreter.globals.values.items():
            if name in interpreter.builtin_names:
                continue
            if name == "args":
                continue
            try:
                data[name] = _encode(value)
            except Exception:
                skipped += 1

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        if skipped:
            self.output(f"Saved {len(data)} variable(s). Skipped {skipped} unsupported value(s).")
        else:
            self.output(f"Saved {len(data)} variable(s).")

    def _load_env(self, interpreter: Interpreter, path: Path) -> None:
        if not path.exists():
            self.output(f"File not found: {path}")
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            self.output("Could not read JSON.")
            return
        if not isinstance(data, dict):
            self.output("Expected a JSON object.")
            return
        for name, value in data.items():
            if not isinstance(name, str):
                continue
            interpreter.globals.define(name, value)
        self.output(f"Loaded {len(data)} variable(s).")
