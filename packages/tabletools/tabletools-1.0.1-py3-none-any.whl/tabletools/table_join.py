"""
Join the columns of two tables based on given key columns. Assumes that the
input files have a header with column names.
"""

import argparse
import sys
import pandas as pd


def parse_args(args):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-t", "--table1", required=True,
                        help="First table file; reads from STDIN if '-'")
    parser.add_argument("-g", "--table2", required=True,
                        help="Second table file; reads from STDIN if '-'")
    parser.add_argument("-c", "--key1", nargs='+', required=True,
                        help="Name of column(s) to be used as key in first table")
    parser.add_argument("-d", "--key2", nargs='+', required=True,
                        help="Name of column(s) to be used as key in second table")
    parser.add_argument("-x", "--suffix1", default="_x",
                        help="Suffix for overlapping column names (default: %(default)s)")
    parser.add_argument("-y", "--suffix2", default="_y",
                        help="Suffix for overlapping column names (default: %(default)s)")
    parser.add_argument("-s", "--delim", default="\t",
                        help="Delimiter to separate output columns, default : <TAB>")
    parser.add_argument("-k", "--how", default="inner",
                        choices=['left', 'right', 'outer', 'inner', 'cross'],
                        help="Type of join, (default: %(default)s)")
    return parser.parse_args(args)


def get_filehandle(filename):
    """ Returns a filehandle """
    if filename == "-":
        return sys.stdin
    return open(filename, "r")


def join(ifile1, ifile2, key1, key2, suffixes=('_x', '_y'), how='inner'):

    df1 = pd.read_csv(ifile1, sep="\t")
    df2 = pd.read_csv(ifile2, sep="\t")

    return pd.merge(df1, df2, left_on=key1, right_on=key2, how=how,
                    suffixes=suffixes)


def main():
    args = parse_args(sys.argv[1:])

    # Make sure that at least one file does not read from stdin.
    if args.table1 == "-" and args.table2 == "-":
        print("Error: '-' provided as input for both tables", file=sys.stderr)
        sys.exit(1)

    ifile1 = get_filehandle(args.table1)
    ifile2 = get_filehandle(args.table2)

    df = join(ifile1, ifile2, args.key1, args.key2,
              [args.suffix1, args.suffix2], args.how)

    ifile1.close()
    ifile2.close()

    df.to_csv(sys.stdout, index=False, sep=args.delim)
