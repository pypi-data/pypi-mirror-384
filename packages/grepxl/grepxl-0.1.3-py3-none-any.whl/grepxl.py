import argparse
from importlib.metadata import version

import pandas as pd
from rich import print
from rich_tools import df_to_table

def main():
    """
    Display rows of a dataframe from an Excel file that match a given pattern.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('pattern', help='Regular expression pattern to search for')
    parser.add_argument('excel', help='Excel file')
    parser.add_argument('--version', action='version', version=version('grepxl'))
    args = parser.parse_args()

    pattern = args.pattern
    excel = args.excel

    data = pd.read_excel(excel, engine='calamine').dropna(axis='columns', how='all')
    search = grep(pattern, data)
    print(df_to_table(search, show_index=False))


def grep(pattern:str, data:pd.DataFrame) -> pd.DataFrame:
    """
    Filter rows in a DataFrame that contain the given pattern in any column.
    """
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
