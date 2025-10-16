import numpy as np
import pandas as pd


def generate_valid_time(start="2023-01-02", periods: int = 1, freq="h") -> np.ndarray:
    # Create a ndarray of np.datetime64 from given periods and freq.
    return pd.date_range(
        start=start, periods=periods, freq=freq.lower(), tz=None
    ).to_numpy()


def generate_valid_time_v2(start="2023-01-02", *args) -> np.ndarray:
    # Create a ndarray of np.datetime64 with changing freq.
    arrays: list[np.ndarray] = []
    start_cur = start

    for i, arg in enumerate(args):
        periods = arg[0] + 1 if i > 0 else arg[0]
        array = generate_valid_time(start_cur, periods, arg[1])

        if i > 0:
            array = array[1:]

        arrays.append(array)
        start_cur = array[-1]

    return np.concatenate(arrays)
