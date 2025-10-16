#  -----------------------------------------------------------------------------------------
#  (C) Copyright IBM Corp. 2025.
#  https://opensource.org/licenses/BSD-3-Clause
#  -----------------------------------------------------------------------------------------

from pathlib import Path
import re
import argparse
import sys

rx = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def semkey(name: str):
    m = rx.match(name)
    return tuple(map(int, m.groups())) if m else None


def main():
    parser = argparse.ArgumentParser(description="Generate HTML redirects to latest version.")
    parser.add_argument(
        "--out",
        default="docs/_build/html",
        help='Output directory for sphinx-multiversion (e.g. "docs/_build/html")',
    )
    args = parser.parse_args()

    OUT = Path(args.out)

    if not OUT.exists():
        sys.exit(f"Output directory does not exist: {OUT}")

    versions = sorted(
        (d for d in OUT.iterdir() if d.is_dir() and rx.match(d.name)),
        key=lambda d: semkey(d.name),
        reverse=True,
    )
    if not versions:
        sys.exit("No vX.Y.Z directories found in the output directory")

    latest = versions[0].name
    latest_dir = OUT / latest

    for htmlfile in latest_dir.rglob("*.html"):
        rel = htmlfile.relative_to(latest_dir)
        target = f"{latest}/{rel.as_posix()}"
        dest = OUT / rel

        dest.parent.mkdir(parents=True, exist_ok=True)
        redirect_html = f"""<!doctype html>
<meta http-equiv="refresh" content="0; url={target}">
<link rel="canonical" href="{target}">
<p>Redirecting to <a href="{target}">{target}</a>…</p>
"""
        dest.write_text(redirect_html, encoding="utf-8")
        print(f"Redirect {dest} -> {target}")


if __name__ == "__main__":
    main()
