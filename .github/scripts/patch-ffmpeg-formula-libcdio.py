#!/usr/bin/env python3
"""Teach the homebrew-ffmpeg formula a --with-libcdio option.

FFmpeg grabs audio CDs through libcdio when configured with --enable-libcdio,
but the formula neither declares that option nor depends on libcdio /
libcdio-paranoia (FFmpeg's configure needs the paranoia headers and
pkg-config module). Patching the tapped formula before `brew options` and
`brew install` run means both build jobs pick the option up through the
option list they already compute.
"""

import pathlib
import sys

# (anchor line, insert before/after it, lines to insert)
INSERTIONS = [
    (
        'option "with-libflite"',
        "before",
        ['  option "with-libcdio", "Enable audio CD grabbing with libcdio"'],
    ),
    (
        'depends_on "libcaca" => :optional',
        "after",
        [
            '  depends_on "libcdio" => :optional',
            '  depends_on "libcdio-paranoia" => :optional',
        ],
    ),
    (
        'args << "--enable-libcaca" if build.with? "libcaca"',
        "after",
        [
            '    args << "--enable-libcdio" if build.with? "libcdio"',
            '    args << "--enable-indev=libcdio" if build.with? "libcdio"',
        ],
    ),
]


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path/to/ffmpeg.rb>", file=sys.stderr)
        return 2

    path = pathlib.Path(sys.argv[1])
    # newline="" keeps the file's own line endings intact on every platform
    with path.open(encoding="utf-8", newline="") as fh:
        text = fh.read()
    if 'option "with-libcdio"' in text:
        print(f"{path}: already patched, nothing to do")
        return 0
    if "libcdio" in text:
        print(
            f"{path}: formula mentions libcdio but has no with-libcdio option; "
            "review the formula by hand",
            file=sys.stderr,
        )
        return 1

    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines(keepends=True)
    for anchor, position, new_lines in INSERTIONS:
        hits = [i for i, line in enumerate(lines) if anchor in line]
        if len(hits) != 1:
            print(
                f"{path}: expected exactly one line containing {anchor!r}, "
                f"found {len(hits)}; the formula layout changed",
                file=sys.stderr,
            )
            return 1
        at = hits[0] if position == "before" else hits[0] + 1
        lines[at:at] = [f"{line}{newline}" for line in new_lines]

    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write("".join(lines))
    print(f"{path}: added --with-libcdio (libcdio + libcdio-paranoia)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
