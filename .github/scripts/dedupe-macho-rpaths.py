#!/usr/bin/env python3
"""Collapse duplicate LC_RPATH entries left behind by dylibbundler.

dylibbundler rewrites *every* LC_RPATH of a bundled library to the prefix given
with -p. Some Homebrew bottles ship a library with more than one entry (tbb has
both @loader_path/../lib and @loader_path/../../..), so after bundling the same
path is present twice. dyld on macOS 15+ refuses to load such an image:

    Library not loaded: @executable_path/../lib/libtbb.12.19.dylib
      Reason: tried: ... (duplicate LC_RPATH '@executable_path/../lib/')

Usage: dedupe-macho-rpaths.py <file-or-directory> [...]
"""

import subprocess
import sys
from pathlib import Path

MACHO_MAGICS = {
    b"\xcf\xfa\xed\xfe",  # 64-bit, little endian (arm64)
    b"\xce\xfa\xed\xfe",  # 32-bit, little endian
    b"\xfe\xed\xfa\xcf",  # 64-bit, big endian
    b"\xfe\xed\xfa\xce",  # 32-bit, big endian
    b"\xca\xfe\xba\xbe",  # universal, big endian
    b"\xbe\xba\xfe\xca",  # universal, little endian
}


def run(*args):
    return subprocess.run(args, capture_output=True, text=True)


def rpaths(path):
    out = run("otool", "-l", str(path)).stdout
    entries, in_command = [], False
    for line in out.splitlines():
        stripped = line.strip()
        if stripped.startswith("cmd "):
            in_command = stripped == "cmd LC_RPATH"
        elif in_command and stripped.startswith("path "):
            entries.append(stripped.split(None, 1)[1].rsplit(" (offset", 1)[0])
    return entries


def dedupe(path):
    changed = False
    for value in sorted(set(rpaths(path))):
        while rpaths(path).count(value) > 1:
            before = len(rpaths(path))
            result = run("install_name_tool", "-delete_rpath", value, str(path))
            if result.returncode != 0 or len(rpaths(path)) >= before:
                sys.exit(
                    f"{path}: could not delete a duplicate LC_RPATH {value}: "
                    f"{result.stderr.strip()}"
                )
            changed = True
        # install_name_tool may drop every occurrence at once; keep one.
        if rpaths(path).count(value) == 0:
            result = run("install_name_tool", "-add_rpath", value, str(path))
            if result.returncode != 0:
                sys.exit(f"{path}: could not restore LC_RPATH {value}: {result.stderr.strip()}")
            changed = True
    if changed:
        run(
            "codesign", "--force", "--deep",
            "--preserve-metadata=entitlements,requirements,flags,runtime",
            "--sign", "-", str(path),
        )
    return changed


def targets(arguments):
    for argument in arguments:
        path = Path(argument)
        if not path.is_dir():
            yield path
            continue
        for entry in sorted(path.iterdir()):
            if entry.is_file() and not entry.is_symlink():
                yield entry


def main():
    count = 0
    for path in targets(sys.argv[1:]):
        try:
            with open(path, "rb") as handle:
                magic = handle.read(4)
        except OSError as error:
            sys.exit(f"{path}: {error}")
        if magic not in MACHO_MAGICS:
            continue
        if dedupe(path):
            print(f"deduplicated LC_RPATH in {path}")
            count += 1
    print(f"deduplicated {count} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
