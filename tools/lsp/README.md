# Veda LSP (very small)

This folder contains a tiny Language Server Protocol (LSP) prototype for Veda.

Goal: useful diagnostics (lexer/parser/checker errors) without external dependencies.

What it does today:

- `textDocument/didOpen` and `textDocument/didChange` → publishes diagnostics using Veda’s `check` pipeline.
- Minimal `initialize` handshake.

What it does not do (yet):

- Full go-to-definition / rename / completion.

## Run

This is meant to be wired into an editor configuration that can run an stdio LSP server.

```bash
python tools/lsp/veda_lsp.py
```

