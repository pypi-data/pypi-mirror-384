"""
ia_metadata.py

'ia' subcommand for modifying and retrieving metadata from archive.org items.
"""

# Copyright (C) 2012-2024 Internet Archive
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from copy import copy
from typing import Mapping

from requests import Response

from internetarchive import item
from internetarchive.cli.cli_utils import MetadataAction, QueryStringAction
from internetarchive.exceptions import ItemLocateError
from internetarchive.utils import json


def setup(subparsers):
    """
    Setup args for metadata command.

    Args:
        subparsers: subparser object passed from ia.py
    """
    parser = subparsers.add_parser("metadata",
                                   aliases=["md"],
                                   help="Retrieve and modify archive.org item metadata")

    parser.add_argument("identifier",
                        nargs="?",
                        type=str,
                        help="Identifier for the upload")

    # Mutually exclusive group for metadata modification options
    modify_group = parser.add_mutually_exclusive_group()
    modify_group.add_argument("-m", "--modify",
                              nargs="+",
                              action=MetadataAction,
                              metavar="KEY:VALUE",
                              help="Modify the metadata of an item")
    modify_group.add_argument("-r", "--remove",
                              nargs="+",
                              action=MetadataAction,
                              metavar="KEY:VALUE",
                              help="Remove KEY:VALUE from a metadata element")
    modify_group.add_argument("-a", "--append",
                              nargs="+",
                              action=MetadataAction,
                              metavar="KEY:VALUE",
                              help="Append a string to a metadata element")
    modify_group.add_argument("-A", "--append-list",
                              nargs="+",
                              action=MetadataAction,
                              metavar="KEY:VALUE",
                              help="Append a field to a metadata element")
    modify_group.add_argument("-i", "--insert",
                              nargs="+",
                              action=MetadataAction,
                              metavar="KEY:VALUE",
                              help=("Insert a value into a multi-value field given "
                                    "an index (e.g. `--insert=collection[0]:foo`)"))

    # Additional options
    parser.add_argument("-E", "--expect",
                        nargs="+",
                        action=MetadataAction,
                        metavar="KEY:VALUE",
                        help=("Test an expectation server-side before applying patch "
                              "to item metadata"))
    parser.add_argument("-H", "--header",
                        nargs="+",
                        action=QueryStringAction,
                        metavar="KEY:VALUE",
                        help="S3 HTTP headers to send with your request")
    parser.add_argument("-t", "--target",
                        metavar="target",
                        default="metadata",
                        help="The metadata target to modify")
    parser.add_argument("-s", "--spreadsheet",
                        metavar="metadata.csv",
                        help="Modify metadata in bulk using a spreadsheet as input")
    parser.add_argument("-e", "--exists",
                        action="store_true",
                        help="Check if an item exists")
    parser.add_argument("-F", "--formats",
                        action="store_true",
                        help="Return the file-formats the given item contains")
    parser.add_argument("-p", "--priority",
                        metavar="priority",
                        help="Set the task priority")
    parser.add_argument("--timeout",
                        metavar="value",
                        help="Set a timeout for metadata writes")
    parser.add_argument("-R", "--reduced-priority",
                        action="store_true",
                        help="Submit task at a reduced priority.")
    parser.add_argument("-P", "--parameters",
                        nargs="+",
                        action=QueryStringAction,
                        metavar="KEY:VALUE",
                        help="Parameters to send with your query.")

    parser.set_defaults(func=lambda args: main(args, parser))


def modify_metadata(item: item.Item,
                    metadata: Mapping,
                    args: argparse.Namespace,
                    parser: argparse.ArgumentParser) -> Response:
    """
    Modify metadata helper function.
    """
    append = bool(args.append)
    append_list = bool(args.append_list)
    insert = bool(args.insert)
    try:
        r = item.modify_metadata(metadata, target=args.target, append=append,
                                 expect=args.expect, priority=args.priority,
                                 append_list=append_list, headers=args.header,
                                 insert=insert, reduced_priority=args.reduced_priority,
                                 timeout=args.timeout)
        assert isinstance(r, Response)  # mypy: modify_metadata() -> Request | Response
    except ItemLocateError as exc:
        print(f"{item.identifier} - error: {exc}", file=sys.stderr)
        sys.exit(1)
    if not r.json()["success"]:
        error_msg = r.json()["error"]
        etype = "warning" if "no changes" in r.text else "error"
        print(f"{item.identifier} - {etype} ({r.status_code}): {error_msg}", file=sys.stderr)
        return r
    print(f"{item.identifier} - success: {r.json()['log']}", file=sys.stderr)
    return r


def remove_metadata(item: item.Item,
                    metadata: Mapping,
                    args: argparse.Namespace,
                    parser: argparse.ArgumentParser) -> Response:
    """
    Remove metadata helper function.
    """
    md: dict[str, list | str] = defaultdict(list)
    for key in metadata:
        src_md = {}
        if args.target.startswith("files/"):
            for f in item.get_files():
                if f.name == "/".join(args.target.split("/")[1:]):
                    src_md = f.__dict__.get(key, {})
                    break
        else:
            src_md = copy(item.metadata.get(key, {}))
        if not src_md:
            continue

        if key == "collection":
            _col = copy(metadata[key])
            _src_md = copy(src_md)
            if not isinstance(_col, list):
                _col = [_col]
            if not isinstance(_src_md, list):
                _src_md = [_src_md]  # type: ignore
            for c in _col:
                if c not in _src_md:
                    r = item.remove_from_simplelist(c, "holdings")
                    j = r.json()
                    if j.get("success"):
                        print(f"{item.identifier} - success: {item.identifier} no longer in {c}",
                              file=sys.stderr)
                        sys.exit(0)
                    elif j.get("error", "").startswith("no row to delete for"):
                        print(f"{item.identifier} - success: {item.identifier} no longer in {c}",
                              file=sys.stderr)
                        sys.exit(0)
                    else:
                        print(f"{item.identifier} - error: {j.get('error')}", file=sys.stderr)
                        sys.exit(1)

        if not isinstance(src_md, list):
            if key == "subject":
                if isinstance(src_md, str):
                    src_md = src_md.split(";")
            elif key == "collection":
                print(f"{item.identifier} - error: all collections would be removed, "
                      "not submitting task.", file=sys.stderr)
                sys.exit(1)

            if src_md == metadata[key]:
                md[key] = "REMOVE_TAG"
                continue

        for x in src_md:
            if isinstance(metadata[key], list):
                if x not in metadata[key]:
                    md[key].append(x)  # type: ignore
            else:
                if x != metadata[key]:
                    md[key].append(x)  # type: ignore

        if len(md[key]) == len(src_md):
            del md[key]

    if md.get("collection") == []:
        print(f"{item.identifier} - error: all collections would be removed, not submitting task.",
              file=sys.stderr)
        sys.exit(1)
    elif not md:
        print(f"{item.identifier} - warning: nothing needed to be removed.", file=sys.stderr)
        sys.exit(0)

    r = modify_metadata(item, md, args, parser)
    return r


def main(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """
    Main entry point for 'ia metadata'.
    """
    formats = set()
    responses: list[bool | Response] = []

    item = args.session.get_item(args.identifier,
                                 request_kwargs={'params': args.parameters})

    # Check existence of item.
    if args.exists:
        if item.exists:
            responses.append(True)
            print(f"{args.identifier} exists", file=sys.stderr)
        else:
            responses.append(False)
            print(f"{args.identifier} does not exist", file=sys.stderr)
        if all(r is True for r in responses):
            sys.exit(0)
        else:
            sys.exit(1)

    # Modify metadata.
    elif (args.modify or args.append or args.append_list
          or args.remove or args.insert):
        # TODO: Find a better way to handle this.
        if args.modify:
            metadata = args.modify
        elif args.append:
            metadata = args.append
        elif args.append_list:
            metadata = args.append_list
        elif args.insert:
            metadata = args.insert
        if args.remove:
            metadata = args.remove

        if args.remove:
            responses.append(remove_metadata(item, metadata, args, parser))
        else:
            responses.append(modify_metadata(item, metadata, args, parser))
        if all(r.status_code == 200 for r in responses):  # type: ignore
            sys.exit(0)
        else:
            for r in responses:
                assert isinstance(r, Response)
                if r.status_code == 200:
                    continue
                # We still want to exit 0 if the non-200 is a
                # "no changes to xml" error.
                elif "no changes" in r.text:
                    continue
                else:
                    sys.exit(1)

    # Get metadata.
    elif args.formats:
        for f in item.get_files():
            formats.add(f.format)
        print("\n".join(formats))

    # Edit metadata for items in bulk, using a spreadsheet as input.
    elif args.spreadsheet:
        if not args.priority:
            args.priority = -5
        with open(args.spreadsheet, newline="", encoding="utf-8-sig") as csvfp:
            spreadsheet = csv.DictReader(csvfp)
            responses = []
            for row in spreadsheet:
                if not row["identifier"]:
                    continue
                item = args.session.get_item(row["identifier"])
                if row.get("file"):
                    del row["file"]
                metadata = {k.lower(): v for k, v in row.items() if v}
                responses.append(modify_metadata(item, metadata, args, parser))

            if all(r.status_code == 200 for r in responses):  # type: ignore
                sys.exit(0)
            else:
                for r in responses:
                    assert isinstance(r, Response)
                    if r.status_code == 200:
                        continue
                    # We still want to exit 0 if the non-200 is a
                    # "no changes to xml" error.
                    elif "no changes" in r.text:
                        continue
                    else:
                        sys.exit(1)

    # Dump JSON to stdout.
    else:
        metadata_str = json.dumps(item.item_metadata)
        print(metadata_str)
