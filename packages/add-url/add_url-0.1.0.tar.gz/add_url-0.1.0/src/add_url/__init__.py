import argparse
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from pzp import pzp
from tomlkit import dump, load, table

# https://packaging.python.org/en/latest/specifications/well-known-project-urls/#well-known-labels
WELL_KNOWN_LABELS = [
    "homepage",
    "source",
    "download",
    "changelog",
    "releasenotes",
    "documentation",
    "issues",
    "funding",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pyproject",
        nargs="?",
        type=Path,
        default="pyproject.toml",
        help="Path to pyproject %(default)s",
    )
    parser.add_argument("url", type=urlsplit)
    parser.add_argument("--label", choices=WELL_KNOWN_LABELS)
    args = parser.parse_args()

    if args.label is None:
        args.label = pzp(
            WELL_KNOWN_LABELS,
            height=len(WELL_KNOWN_LABELS),
            fullscreen=False,
        )

    with args.pyproject.open("rb") as fp:
        pyproject = load(fp)

        try:
            urls = pyproject["project"]["urls"]
        except KeyError:
            urls = {}

        if args.url.scheme:
            urls[args.label] = urlunsplit(args.url)
        else:
            urls[args.label] = f"https://{args.url.path}"

        tbl = table()
        tbl.update(urls)
        pyproject["project"]["urls"] = tbl

        with args.pyproject.open("w") as fp:
            dump(pyproject, fp)
