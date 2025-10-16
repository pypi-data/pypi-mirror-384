import json
import os
import pathlib
import re
from typing import Any, Counter

import click
import pathspec


def _write_report(filename: str, data: list[dict[str, Any]]) -> None:
    counter = Counter(match["type"].upper() for match in data)
    summary = dict(counter)
    summary["total"] = sum(counter.values())

    report = {
        "summary": summary,
        "details": data,
    }

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)


def _parse_file(path: pathlib.Path, path_root: pathlib.Path, pattern: re.Pattern) -> list[dict[str, Any]]:
    # FIXME: Ensure that only comments count to matches.
    matches: list[dict[str, Any]] = []

    try:
        for line_number, line in enumerate(open(path)):
            line = line.strip()

            if match := re.search(pattern, line):
                matches.append(
                    {
                        "type": match.group(1),
                        "file": str(path.relative_to(path_root)),
                        "line": line_number + 1,
                        "pos": match.start(1),
                        "content": line.strip(),
                    }
                )

    except UnicodeDecodeError:
        print(f"Error reading {path}")

    return matches


def _parse_directory(
    directory: pathlib.Path,
    path_root: pathlib.Path,
    match_regex: re.Pattern,
    ignore_spec: pathspec.PathSpec,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []

    for path in directory.rglob("*"):
        if not path.is_file():
            continue

        if ignore_spec.match_file(path):
            continue

        match = _parse_file(path, path_root, match_regex)

        if len(match) == 0:
            continue

        matches.extend(match)

    return matches


def _load_ignore_spec(file_path: str) -> pathspec.PathSpec:
    file = pathlib.Path(file_path)

    if not file.is_file():
        return pathspec.PathSpec.from_lines("gitwildmatch", [])

    with open(file, "r", encoding="utf-8") as file:
        return pathspec.PathSpec.from_lines("gitwildmatch", file)


CONTEXT_SETTINGS = {"max_content_width": os.get_terminal_size().columns - 10}


@click.group(context_settings=CONTEXT_SETTINGS)
def cli() -> None:
    pass


@cli.command("report", short_help="Generate a report")
@click.option(
    "--out-file",
    "-o",
    default="report.json",
    show_default=True,
    type=click.Path(),
    help=" Specify path where the report will be saved",
)
@click.option(
    "--format",
    "-f",
    default="json",
    show_default=True,
    type=click.Choice(["json"]),
    help="Specify the format of the generated report",
)
@click.option(
    "--ignore-file",
    default=".gitignore",
    show_default=True,
    type=click.Path(exists=True),
    help="Specify ignore file to use",
)
@click.argument("path", envvar="RA_SEARCH_DIR", default=".", type=click.Path())
def report(path: str, out_file: str, format: str, ignore_file: str) -> None:
    """
    \b
    positional arguments:
        PATH    Specify the path that will be scanned [default: .]
    """
    # TODO: Add support for multiple output formats (junitxml, json, etc.)

    path_root: pathlib.Path = pathlib.Path("./")
    search_directory: pathlib.Path = pathlib.Path(path)

    output_path: str = out_file

    re_match_str: str = r"(TODO|FIXME|HACK|OPTIMIZE|REVIEW)"
    re_match: re.Pattern = re.compile(re_match_str)

    matches: list[dict[str, Any]] = []

    ignore_spec: pathspec.PathSpec = _load_ignore_spec(ignore_file)

    matches = _parse_directory(search_directory, path_root, re_match, ignore_spec)

    _write_report(output_path, matches)


if __name__ == "__main__":
    cli()
