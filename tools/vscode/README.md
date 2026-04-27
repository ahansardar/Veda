# VS Code support

This folder contains a VS Code language extension for Veda:

- Syntax highlighting (TextMate grammar)
- Bracket + comment configuration
- Snippets for common Veda constructs
- Optional file icons (for `.veda`)

It’s kept inside the repo so collaborators can iterate quickly.

## Use locally

### Option A: Install a packaged `.vsix`

1. Build a VSIX (from repo root):
   - `cd tools/vscode`
   - `./package.ps1` (writes to `dist/veda-language-<version>.vsix`)
2. In VS Code: Extensions → `...` → **Install from VSIX…**

### Option B: Run in Extension Development Host

1. Open `tools/vscode` in VS Code
2. Run and Debug → **Run Extension**

## Enable the `.veda` file icon

VS Code only shows file icons when a file icon theme is active.

1. Command Palette → **Preferences: File Icon Theme**
2. Choose **Veda Icons**
