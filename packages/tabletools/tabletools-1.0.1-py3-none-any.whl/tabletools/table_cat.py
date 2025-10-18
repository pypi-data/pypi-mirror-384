"""
Concatenate table files that have the same header, similar to the Bash cat
command.
"""

import sys
import argparse
import gzip


def open_filehandle(file, gunzip=False):
    if gunzip:
        return gzip.open(file, "rt")
    else:
        return open(file)


def parse_args(args):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tables", nargs='+',
                        help="Input table file(s)")
    parser.add_argument("-z", "--gunzip", action='store_true',
                        help="Decompress files using gzip")
    return parser.parse_args(args)


def cat_tables(tables, gunzip, out=sys.stdout):
    if len(tables) < 1:
        return "No table provided"

    header = tables[0].readline().strip('\n\r')

    # Loop on all tables to ensure that their header matches the first one.
    for t in tables[1:]:
        if t.readline().strip('\n\r') != header:
            return "File headers are not the same in all input files"

    print(header, file=out)
    for t in tables:
        for line in t:
            print(line.strip('\n\r'), file=out)


def main():
    args = parse_args(sys.argv[1:])

    tables = []
    for f in args.tables:
        tables += [open_filehandle(f, args.gunzip)]

    err = cat_tables(tables, args.gunzip)
    if err is not None:
        print(err, file=sys.stderr)
        sys.exit(1)
