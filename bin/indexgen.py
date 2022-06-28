#!/usr/bin/env python3
# ---
# Copyright 2020 glowinthedark
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and limitations under the License.
# ---
#
# Generate index.html files for
# all subdirectories in a directory tree.

# handle symlinked files and folders: displayed with custom icons

# By default only the current folder is processed and hidden files (starting with a dot) are skipped.
# To force inclusion of hidden files pass --include-hidden.

# Use -r or --recursive to process nested folders.

import argparse
import datetime
import os
import sys
from pathlib import Path
from urllib.parse import quote

DEFAULT_OUTPUT_FILE = 'index.html'


def process_dir(top_dir, opts):
    glob_patt = opts.filter or '*'

    path_top_dir = Path(top_dir)

    index_path = Path(path_top_dir, opts.output_file)

    if opts.verbose:
        print(f'Traversing dir {path_top_dir.absolute()}')

    try:
        index_file = open(index_path, 'w')
    except Exception as e:
        print('cannot create file %s %s' % (index_path, e))
        return

    index_file.write("""
---
layout: page
title: Taken Notes
description: "Lashi Bandara - Taken Notes"
---

<div class="panel panel-default content-panel">
  <div class="panel-heading">
    <h1 class="panel-title"> """
                     f'{path_top_dir.name}'
                     """</h1>
  </div>
  <div class="panel-body">

                     <table aria-describedby="summary">
                         <thead>
                         <tr>
                             <th></th>
                             <th>Name</th>
                             <th>Size</th>
                             <th class="hideable">
                                 Modified
                             </th>
                             <th class="hideable"></th>
                         </tr>
                         </thead>
                         <tbody>
                         <tr class="clickable">
                             <td></td>
                             <td><a href=".."><svg width="1.5em" height="1em" version="1.1" viewBox="0 0 24 24"><use xlink:href="#go-up"></use></svg>
                 <span class="goup">..</span></a></td>
                             <td>&mdash;</td>
                             <td class="hideable">&mdash;</td>
                             <td class="hideable"></td>
                         </tr>
                 """)

    # sort dirs first
    sorted_entries = sorted(path_top_dir.glob(glob_patt), key=lambda p: (p.is_file(), p.name))

    entry: Path
    for entry in sorted_entries:

        # don't include index.html in the file listing
        if entry.name.lower() == opts.output_file.lower():
            continue

        #  skip .hidden dot files unless explicitly requested
        if not opts.include_hidden and entry.name.startswith('.'):
            continue

        if entry.is_dir() and opts.recursive:
            process_dir(entry, opts)

        # From Python 3.6, os.access() accepts path-like objects
        if (not entry.is_symlink()) and not os.access(str(entry), os.R_OK):
            print(f"*** WARNING *** entry {entry.absolute()} is not readable! SKIPPING!")
            continue
        if opts.verbose:
            print(f'{entry.absolute()}')

        size_bytes = -1  # is a folder
        size_pretty = '&mdash;'
        last_modified = '-'
        last_modified_human_readable = '-'
        last_modified_iso = ''
        try:
            if entry.is_file():
                size_bytes = entry.stat().st_size
                size_pretty = pretty_size(size_bytes)

            if entry.is_dir() or entry.is_file():
                last_modified = datetime.datetime.fromtimestamp(entry.stat().st_mtime).replace(microsecond=0)
                last_modified_iso = last_modified.isoformat()
                last_modified_human_readable = last_modified.strftime("%c")

        except Exception as e:
            print('ERROR accessing file name:', e, entry)
            continue

        entry_path = str(entry.name)

        if entry.is_dir() and not entry.is_symlink():
            entry_type = 'folder'
            if os.name not in ('nt',):
                # append trailing slash to dirs, unless it's windows
                entry_path = os.path.join(entry.name, '')

        elif entry.is_dir() and entry.is_symlink():
            entry_type = 'folder-shortcut'
            print('dir-symlink', entry.absolute())

        elif entry.is_file() and entry.is_symlink():
            entry_type = 'file-shortcut'
            print('file-symlink', entry.absolute())

        else:
            entry_type = 'file'

        index_file.write(f"""
        <tr class="file">
            <td></td>
            <td>
                <a href="{quote(entry_path)}">
                    <svg width="1.5em" height="1em" version="1.1" viewBox="0 0 265 323"><use xlink:href="#{entry_type}"></use></svg>
                    <span class="name">{entry.name}</span>
                </a>
            </td>
            <td data-order="{size_bytes}">{size_pretty}</td>
            <td class="hideable"><time datetime="{last_modified_iso}">{last_modified_human_readable}</time></td>
            <td class="hideable"></td>
        </tr>
""")

    index_file.write("""
            </tbody>
        </table>
    </div>
</div>
""")
    if index_file:
        index_file.close()


# bytes pretty-printing
UNITS_MAPPING = [
    (1024 ** 5, ' PB'),
    (1024 ** 4, ' TB'),
    (1024 ** 3, ' GB'),
    (1024 ** 2, ' MB'),
    (1024 ** 1, ' KB'),
    (1024 ** 0, (' byte', ' bytes')),
]


def pretty_size(bytes, units=UNITS_MAPPING):
    """Human-readable file sizes.

    ripped from https://pypi.python.org/pypi/hurry.filesize/
    """
    for factor, suffix in units:
        if bytes >= factor:
            break
    amount = int(bytes / factor)

    if isinstance(suffix, tuple):
        singular, multiple = suffix
        if amount == 1:
            suffix = singular
        else:
            suffix = multiple
    return str(amount) + suffix


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='''DESCRIPTION:
    Generate directory index files (recursive is OFF by default).
    Start from current dir or from folder passed as first positional argument.
    Optionally filter by file types with --filter "*.py". ''')

    parser.add_argument('top_dir',
                        nargs='?',
                        action='store',
                        help='top folder from which to start generating indexes, '
                             'use current folder if not specified',
                        default=os.getcwd())

    parser.add_argument('--filter', '-f',
                        help='only include files matching glob',
                        required=False)

    parser.add_argument('--output-file', '-o',
                        metavar='filename',
                        default=DEFAULT_OUTPUT_FILE,
                        help=f'Custom output file, by default "{DEFAULT_OUTPUT_FILE}"')

    parser.add_argument('--recursive', '-r',
                        action='store_true',
                        help="recursively process nested dirs (FALSE by default)",
                        required=False)

    parser.add_argument('--include-hidden', '-i',
                        action='store_true',
                        help="include dot hidden files (FALSE by default)",
                        required=False)

    parser.add_argument('--verbose', '-v',
                        action='store_true',
                        help='***WARNING: can take longer time with complex file tree structures on slow terminals***'
                             ' verbosely list every processed file',
                        required=False)

    config = parser.parse_args(sys.argv[1:])
    process_dir(config.top_dir, config)
