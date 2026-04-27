from __future__ import annotations

import sys
from pathlib import Path


def _ensure_dev_imports() -> None:
    """
    Allows running `python main.py ...` without installing the package.
    The real package lives in `./veda/veda` (src-style layout).
    """
    repo_root = Path(__file__).resolve().parent
    src_root = repo_root / "veda"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))


def main() -> None:
    _ensure_dev_imports()
    from veda.cli import main as veda_main

    veda_main()


if __name__ == "__main__":
    main()

