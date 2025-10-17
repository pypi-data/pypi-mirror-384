#!/usr/bin/env python3
"""Thin ctypes-based helpers for interacting with the MuPDF JSON extractor."""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path
from typing import List, Sequence

from ._lib import get_default_library_path


class LibraryLoadError(RuntimeError):
    """Raised when the shared library cannot be located or loaded."""


def _resolve_library_path(provided: str | Path | None) -> Path:
    """Resolve a concrete filesystem path to the shared library."""
    if provided is not None:
        candidate = Path(provided)
    else:
        default = get_default_library_path()
        candidate = Path(default) if default is not None else None

    if candidate is None:
        raise LibraryLoadError(
            "C library not found. Build it with 'make tomd' or set "
            "PYMUPDF4LLM_C_LIB to the compiled shared object."
        )

    candidate = candidate.resolve()
    if not candidate.exists():
        raise LibraryLoadError(f"C library not found at {candidate}")

    return candidate


def _load_library(lib_path: str | Path | None) -> ctypes.CDLL:
    path = _resolve_library_path(lib_path)
    lib = ctypes.CDLL(str(path))

    lib.pdf_to_json.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    lib.pdf_to_json.restype = ctypes.c_int

    lib.page_to_json_string.argtypes = [ctypes.c_char_p, ctypes.c_int]
    lib.page_to_json_string.restype = ctypes.c_char_p

    return lib


def convert_pdf_to_json(
    pdf_path: str | Path,
    output_dir: str | Path,
    lib_path: str | Path | None = None,
) -> Sequence[Path]:
    """Invoke the C extractor to materialise page-level JSON files."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"Input PDF not found: {pdf_path}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    lib = _load_library(lib_path)
    rc = lib.pdf_to_json(str(pdf_path).encode("utf-8"), str(output_dir).encode("utf-8"))
    if rc != 0:
        raise RuntimeError(f"C extractor reported failure (exit code {rc})")

    json_files: List[Path] = sorted(output_dir.glob("page_*.json"))
    return tuple(json_files)


def extract_page_json(
    pdf_path: str | Path,
    page_number: int,
    lib_path: str | Path | None = None,
) -> str:
    """Return raw JSON for a single page using the in-memory C helper."""
    if page_number < 0:
        raise ValueError("page_number must be >= 0")

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"Input PDF not found: {pdf_path}")

    lib = _load_library(lib_path)
    result_ptr = lib.page_to_json_string(str(pdf_path).encode("utf-8"), page_number)
    if not result_ptr:
        raise RuntimeError("C extractor returned NULL for page JSON")

    json_bytes = ctypes.cast(result_ptr, ctypes.c_char_p).value or b""

    from ctypes import util as _ctypes_util

    libc_name = _ctypes_util.find_library("c")
    if sys.platform == "win32":
        libc_name = "msvcrt"

    libc = ctypes.CDLL(libc_name) if libc_name else ctypes.CDLL(None)
    try:
        free_fn = libc.free
    except AttributeError:  # pragma: no cover - extremely rare runtimes
        free_fn = None

    if free_fn is not None:
        free_fn.argtypes = [ctypes.c_void_p]
        free_fn.restype = None
        free_fn(result_ptr)

    return json_bytes.decode("utf-8")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for producing per-page JSON artefacts."""
    argv = list(sys.argv[1:] if argv is None else argv)

    if not argv or len(argv) > 2:
        script = Path(sys.argv[0]).name
        print(f"Usage: {script} <input.pdf> [output_dir]")
        return 1

    pdf_path = Path(argv[0])
    output_dir = Path(argv[1]) if len(argv) == 2 else pdf_path.with_suffix("")
    if len(argv) == 1:
        output_dir = output_dir.parent / f"{output_dir.name}_json"

    try:
        json_files = convert_pdf_to_json(pdf_path, output_dir)
    except (FileNotFoundError, LibraryLoadError, RuntimeError) as exc:
        print(f"error: {exc}")
        return 1

    print(f"Extracted {len(json_files)} JSON files to {output_dir}")
    for path in json_files:
        print(f"  • {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual usage
    raise SystemExit(main())
