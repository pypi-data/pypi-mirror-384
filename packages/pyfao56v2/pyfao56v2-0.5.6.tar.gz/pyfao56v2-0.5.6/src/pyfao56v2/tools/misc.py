import re
import os
from glob import glob
import csv
from openpyxl import load_workbook
import pandas as pd



def natural_sort(l): 
    """
    Sort the given list in natural order.
    """
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)



def nglob(path, **kwargs):
    """
    Glob with natural sorting.
    """
    return natural_sort(glob(path, **kwargs))



def read_comments(filename, sheet="Sheet1"):
    """
    Read comments from an Excel or CSV file.
    """
    ext = os.path.splitext(filename)[1]

    if ext == ".xlsx":
        wb = load_workbook(filename)
        ws = wb[sheet]
        comments = []
        for row in ws.rows:
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith("#"):
                    comments.append(cell.value)
    else: # in this case, the file is assumed to be a csv
        comments = []
        with open(filename, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                for cell in row:
                    if isinstance(cell, str) and cell.startswith("#"):
                        comments.append(cell)

    return comments



def interp_ts(ts, date):
    """
    Get the value of a (sorted) time series at a given date using linear interpolation.
    """
    if isinstance(date, str):
        date = pd.to_datetime(date)
    else:
        assert isinstance(date, pd.Timestamp), f"The date must be a Timestamp. Got {type(date)}"
    assert isinstance(ts, pd.Series), f"The time series must be a Series. Got {type(ts)}"
    assert isinstance(ts.index, pd.DatetimeIndex), f"The index of the time series must be a DatetimeIndex. Got {type(ts.index)}"
    assert ts.isna().sum() == 0, "The time series must not contain NaN values"
    assert ts.index.is_monotonic_increasing, "The index of the time series must be monotonic increasing"

    i = ts.index.searchsorted(date)
    if i == 0:
        return ts.iloc[0]
    elif i == len(ts):
        return ts.iloc[-1]
    else:
        t0, t1 = ts.index[i-1], ts.index[i]
        v0, v1 = ts.iloc[i-1], ts.iloc[i]
        return v0 + (v1-v0)*(date-t0)/(t1-t0)