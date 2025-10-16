import sys
import warnings

import pandas as pd
from rich import print
from rich_tools import df_to_table

def main():
    try:
        pattern, xl = sys.argv[1:]
    except ValueError:
        print("Usage: grepxl <pattern> <file>")
        sys.exit(1)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        data = pd.read_excel(xl, engine='openpyxl').dropna(axis='columns', how='all')
    search = grep(pattern, data)
    print(df_to_table(search, show_index=False))




def grep(pattern, data):
    mask = None
    for col in data.columns:
        if data[col].dtype != object:
            continue
        if mask is None:
            mask = data[col].str.contains(pattern)
        else:
            mask = mask | data[col].str.contains(pattern)

    return data[mask]


if __name__ == "__main__":
    main()
