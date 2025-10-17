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
    data = pd.read_excel(xl, engine='calamine').dropna(axis='columns', how='all')
    search = grep(pattern, data)
    print(df_to_table(search, show_index=False))




def grep(pattern, data):
    mask = None
    for col in data.columns:
        update = data[col].astype(str).str.contains(pattern)
        
        if mask is None:
            mask = update
        else:
            mask = mask | update

    return data[mask]


if __name__ == "__main__":
    main()
