#!/usr/bin/env python

"""
Converts a table file to an Excel file.
"""

import argparse
import sys
import pandas as pd

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("-t", "--table", required=True,
                    help="Input table file; reads from STDIN if '-'")
parser.add_argument("-o", "--ofile", required=True,
                    help="Output Excel file")
parser.add_argument("-w", "--adjust-width", action='store_true',
                    help="Automatically adjust column width; requires pip install xlsxwriter")
parser.add_argument("-s", "--sep", default="\t",
                    help="Delimiter separating input columns, default : <TAB>")
args = parser.parse_args()


def get_filehandle(filename):
    """ Returns a filehandle """
    if filename == "-":
        return sys.stdin
    return open(filename, "r")


ifile = get_filehandle(args.table)
df = pd.read_csv(ifile, sep=args.sep)

w = pd.ExcelWriter(args.ofile)
df.to_excel(w, index=False)

# Auto-adjust columns' width
if args.adjust_width:
    for column in df:
        column_width = max(df[column].astype(str).map(len).max(), len(column))
        col_idx = df.columns.get_loc(column)
        w.sheets['Sheet1'].set_column(col_idx, col_idx, column_width)

w.save()
