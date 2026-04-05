#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bigcontainer import unpack_file


def restore_all(repo_root: Path, overwrite: bool = False) -> list[Path]:
    restored: list[Path] = []

    for manifest_path in repo_root.rglob("*.bigcontainer/manifest.json"):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        out_path = manifest_path.parent.parent / manifest["original_name"]

        if out_path.exists() and not overwrite:
            continue

        unpack_file(manifest_path, out_path)
        restored.append(out_path)

    return restored


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Restore all Big Container bundles found inside a repository tree."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to scan",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite already existing restored files",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    repo_root = Path(args.repo_root)
    restored = restore_all(repo_root, overwrite=args.overwrite)

    if not restored:
        print("No files restored.")
        return

    for path in restored:
        print(path)


if __name__ == "__main__":
    main()
