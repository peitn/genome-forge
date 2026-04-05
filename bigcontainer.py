#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def pack_file(src: Path, out_dir: Path, chunk_size: int = 24000) -> Path:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    if not src.is_file():
        raise FileNotFoundError(f"Source file not found: {src}")

    raw = src.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")

    pack_dir = out_dir / f"{src.name}.bigcontainer"
    pack_dir.mkdir(parents=True, exist_ok=True)

    parts = []
    for i in range(0, len(b64), chunk_size):
        idx = i // chunk_size
        part_name = f"part_{idx:04d}.b64"
        part_path = pack_dir / part_name
        part_text = b64[i:i + chunk_size]

        part_path.write_text(part_text, encoding="utf-8")

        parts.append(
            {
                "index": idx,
                "file": part_name,
                "chars": len(part_text),
                "sha256": sha256_text(part_text),
            }
        )

    manifest = {
        "format": "share-import-big-container.v1",
        "original_name": src.name,
        "original_size_bytes": len(raw),
        "original_sha256": sha256_bytes(raw),
        "encoding": "base64",
        "chunk_size_chars": chunk_size,
        "part_count": len(parts),
        "parts": parts,
        "commands": {
            "pack": f"python bigcontainer.py pack {src.name}",
            "unpack": (
                f"python bigcontainer.py unpack "
                f"--manifest manifest.json --out {src.name}"
            ),
        },
    }

    manifest_path = pack_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return pack_dir


def unpack_file(manifest_path: Path, out_path: Path) -> None:
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base_dir = manifest_path.parent

    joined_parts: list[str] = []

    for part in manifest["parts"]:
        part_path = base_dir / part["file"]
        if not part_path.is_file():
            raise FileNotFoundError(f"Missing part file: {part_path}")

        text = part_path.read_text(encoding="utf-8")

        if sha256_text(text) != part["sha256"]:
            raise ValueError(f"Checksum mismatch for part {part['file']}")

        joined_parts.append(text)

    try:
        raw = base64.b64decode("".join(joined_parts).encode("ascii"), validate=True)
    except (binascii.Error, ValueError) as e:
        raise ValueError("Invalid base64 payload during reconstruction") from e

    if sha256_bytes(raw) != manifest["original_sha256"]:
        raise ValueError("Final SHA256 mismatch after reconstruction")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(raw)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pack and unpack files using the Big Container format."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_pack = sub.add_parser("pack", help="Split a file into base64 parts")
    p_pack.add_argument("src", help="Source file path")
    p_pack.add_argument("--out-dir", default=".", help="Output directory")
    p_pack.add_argument(
        "--chunk-size",
        type=int,
        default=24000,
        help="Chunk size in base64 characters",
    )

    p_unpack = sub.add_parser("unpack", help="Reassemble a file from manifest.json")
    p_unpack.add_argument(
        "--manifest",
        required=True,
        help="Path to manifest.json",
    )
    p_unpack.add_argument(
        "--out",
        required=True,
        help="Output file path",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "pack":
        src = Path(args.src)
        out_dir = Path(args.out_dir)
        pack_dir = pack_file(src, out_dir, args.chunk_size)
        print(pack_dir)
        return

    if args.command == "unpack":
        manifest_path = Path(args.manifest)
        out_path = Path(args.out)
        unpack_file(manifest_path, out_path)
        print(out_path)
        return

    raise RuntimeError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
