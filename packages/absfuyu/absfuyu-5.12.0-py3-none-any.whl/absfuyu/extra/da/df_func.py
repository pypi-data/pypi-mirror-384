"""
Absfuyu: Data Analysis
----------------------
DF Function

Version: 5.12.0
Date updated: 17/10/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["equalize_df", "compare_2_list", "rename_with_dict"]


# Library
# ---------------------------------------------------------------------------
from itertools import chain

import numpy as np
import pandas as pd


# Function
# ---------------------------------------------------------------------------
def equalize_df(data: dict[str, list], fillna=np.nan) -> dict[str, list]:
    """
    Make all list in dict have equal length to make pd.DataFrame

    :param data: `dict` data that ready for `pd.DataFrame`
    :param fillna: Fill N/A value (Default: `np.nan`)
    """
    max_len = max(map(len, data.values()))
    for _, v in data.items():
        if len(v) < max_len:
            missings = max_len - len(v)
            for _ in range(missings):
                v.append(fillna)
    return data


def compare_2_list(*arr) -> pd.DataFrame:
    """
    Compare 2 lists then create DataFrame
    to see which items are missing

    Parameters
    ----------
    arr : list
        List

    Returns
    -------
    DataFrame
        Compare result
    """
    # Setup
    col_name = "list"
    arr = [sorted(x) for x in arr]  # type: ignore # map(sorted, arr)

    # Total array
    tarr = sorted(list(set(chain.from_iterable(arr))))
    # max_len = len(tarr)

    # Temp dataset
    temp_dict = {"base": tarr}
    for idx, x in enumerate(arr):
        name = f"{col_name}{idx}"

        # convert list
        temp = [item if item in x else np.nan for item in tarr]

        temp_dict.setdefault(name, temp)

    df = pd.DataFrame(temp_dict)
    df["Compare"] = np.where(
        df[f"{col_name}0"].apply(lambda x: str(x).lower())
        == df[f"{col_name}1"].apply(lambda x: str(x).lower()),
        df[f"{col_name}0"],  # Value when True
        np.nan,  # Value when False
    )
    return df


def rename_with_dict(df: pd.DataFrame, col: str, rename_dict: dict) -> pd.DataFrame:
    """
    Version: 2.0.0

    :param df: DataFrame
    :param col: Column name
    :param rename_dict: Rename dictionary
    """

    name = f"{col}_filtered"
    df[name] = df[col]
    rename_val = list(rename_dict.keys())
    df[name] = df[name].apply(lambda x: "Other" if x in rename_val else x)
    return df
