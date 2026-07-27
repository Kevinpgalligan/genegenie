"""
This just mutates all the paths in the genegenie sample website (under the docs/ folder) so
that they correctly point to kevingal.com/genegenie/. So the steps are:
  1. Generate the site under the build/ directory (don't forget the --anonymise flag).
  2. Copy it over to the docs/ folder (which, annoyingly, is the name expected by GitHub Pages).
  3. Call this script on the docs/ folder.

Usage:
  python3 <path-to-script> <path-to-docs/-folder>
"""

import sys
from pathlib import Path

ORIGINAL = 'href="/'
NEW = 'href="/genegenie/'

SRC_ORIG = 'src="/'
SRC_NEW = 'src="/genegenie/'

def main():
    html_files = list(Path(sys.argv[1]).rglob("**/*.html"))
    print("Found", len(html_files), "HTML files")
    for name in html_files:
        with open(name, "r") as f:
            s = f.read()
        if ORIGINAL in s or SRC_ORIG in s:
            with open(name, "w") as f:
                f.write(s.replace(ORIGINAL, NEW).replace(SRC_ORIG, SRC_NEW))

if __name__ == "__main__":
    main()
