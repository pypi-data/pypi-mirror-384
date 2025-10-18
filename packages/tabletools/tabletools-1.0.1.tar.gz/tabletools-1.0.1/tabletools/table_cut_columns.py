import sys
import argparse
import pandas as pd


def main():
    """
    "Cut selected columns from table. Assumes that the input file has a
    header line with column names"
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--table", required=True,
                        help="Input table file. Reads from STDIN if '-'")
    parser.add_argument("-c", "--col-name", nargs='+',
                        help="Column name(s); selects column(s)")
    parser.add_argument("-o", "--col-name-as", nargs='+', required=False,
                        help="Optional output column name. Equal times and same order as col-name")
    parser.add_argument("-d", "--sep", default="\t",
                        help="Column separator character, (default: <TAB>)")

    args = parser.parse_args()

    def get_filehandle(filename):
        """ Returns a filehandle """
        if filename == "-":
            return sys.stdin
        return open(filename, "r")

    ifile = get_filehandle(args.table)

    df = pd.read_csv(ifile, sep=args.sep)

    df_out = df[args.col_name]

    if (args.col_name_as):
        if len(args.col_name) != len(args.col_name_as):
            print("col-name and col-name-as options are not equal")
            sys.exit(1)
        else:
            zipped_names = zip(args.col_name, args.col_name_as)
            for oldname, newname in zipped_names:
                df_out.rename(columns={oldname: newname}, inplace=True)

    df_out.to_csv(sys.stdout, index=False, sep=args.sep)
