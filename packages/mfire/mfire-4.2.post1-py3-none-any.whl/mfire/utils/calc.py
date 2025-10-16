from __future__ import annotations

import time
from functools import reduce, wraps
from itertools import combinations
from typing import Any, Generator, List, Optional, Sequence, Tuple

import numpy as np

import mfire.utils.mfxarray as xr


# Decorator to measure and display the execution time of a function
def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if len(args) > 0 and hasattr(args[0], "__class__"):
            name = f"{args[0].__class__.__name__}.{func.__name__}"
        else:
            name = func.__name__

        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        print(f"Temps d'exécution de {name} : {elapsed_time:.2f} secondes")
        return result

    return wrapper


def peak_memory(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if len(args) > 0 and hasattr(args[0], "__class__"):
            name = f"{args[0].__class__.__name__}.{func.__name__}"
        else:
            name = func.__name__

        import tracemalloc

        tracemalloc.start()
        peak_beginning = tracemalloc.get_traced_memory()[1]
        result = func(*args, **kwargs)
        print(
            f"Pic de mémoire atteint à {name} : "
            f"{(tracemalloc.get_traced_memory()[1] - peak_beginning)/ 10**6:0.2f} Mo"
        )

        return result

    return wrapper


def compute_accumulation(
    da: xr.DataArray, n: int = 6, dim: str = "valid_time"
) -> xr.DataArray:
    """Returns the cumulative RR for the next n steps.

    Args:
        da: The input DataArray containing precipitation values.
        n: The number of steps to compute the cumulative RR. Defaults to 6.
        dim: The dimension along which to compute the cumulative RR.
            Defaults to 'valid_time'.

    Returns:
        xr.DataArray: The cumulative RR for the next n steps.
    """
    nb_step = da[dim].size

    # Compute the cumulative da for the n preceding steps
    previous_cumulative_data = (
        da.rolling({dim: n}, min_periods=1)
        .sum()
        .shift({dim: -n + 1})
        .isel({dim: slice(None, nb_step - n + 1)})
    )

    # Compute the cumulative da for the n following steps
    following_cumulative_data = (
        da.shift({dim: -n + 1})
        .rolling({dim: n}, min_periods=1)
        .sum()
        .isel({dim: slice(nb_step - n + 1, None)})
    )

    # Assign variable names
    previous_cumulative_data.name = da.name
    following_cumulative_data.name = da.name

    # Merge the two arrays and return the result
    result = xr.merge([previous_cumulative_data, following_cumulative_data])[da.name]
    result.attrs["accum_hour"] = n
    return result


def cast_numpy_data(data, cast_type: Optional[type] = None):
    if cast_type is None:
        return data

    if isinstance(data, np.ndarray):
        return cast_type(data) if data.size == 1 else data.astype(cast_type)

    if isinstance(data, (xr.DataArray, xr.Dataset)):
        return data.astype(cast_type)

    return cast_type(data)


def round_to_closest_multiple(x: Any, m: Any, cast_type: Optional[type] = None) -> Any:
    """Return the multiple of m that is closest to x.

    Args:
        x: The value to round.
        m: The multiple to round to.
        cast_type: Optional type for casting the result.

    Returns:
        Any: The multiple of m closest to x.
    """
    return cast_numpy_data(m * ((x + m / 2) // m), cast_type)


def round_to_next_multiple(x: Any, m: Any, cast_type: Optional[type] = None) -> Any:
    """Return the next multiple of m greater than or equal to x.

    Args:
        x: The value to round.
        m: The multiple to round to.
        cast_type: Optional type for casting the result.

    Returns:
        Any: The next multiple of m greater than or equal to x.
    """
    return cast_numpy_data(m * np.ceil(x / m), cast_type)


def round_to_previous_multiple(x: Any, m: Any, cast_type: Optional[type] = None) -> Any:
    """Return the previous multiple of m less than or equal to x.

    If cast_type is None, the returned values has

    Args:
        x: The value to round.
        m: The multiple to round to.
        cast_type: Optional type for casting the result.

    Returns:
        The previous multiple of m less than or equal to x.
    """
    return cast_numpy_data(m * (np.floor_divide(x, m)), cast_type)


def combinations_and_remaining(
    objects: List, r: int
) -> Generator[Tuple[List, List], None, None]:
    """
    Generates all combinations and remaining elements of objects.
    The first element is the generated element of size r, and the second element is
    the remaining objects.

    Args:
        objects: The list of objects.
        r: The size of the generated combinations.

    Yields:
        Tuple containing the generated combination and the remaining objects.
    """
    for c in combinations(objects, r=r):
        diff = [i for i in objects if i not in c]
        yield list(c), diff


def all_combinations_and_remaining(
    objects: List, is_symmetric: bool = False
) -> Generator[Tuple[List, List], None, None]:
    """
    Generates all combinations and remaining objects of a list.
    If the `is_symmetric` argument is True, it only generates (combi, remaining) and
    not (remaining, combi), except for objects of even size and r=len(objects)/2.

    Args:
        objects: The list of objects.
        is_symmetric: Indicates if symmetric combinations should be generated. Defaults
            to False.

    Yields:
        Tuple containing the generated combination and the remaining objects.
    """
    r_max = len(objects) // 2 if is_symmetric else len(objects)
    for r in range(r_max):
        yield from combinations_and_remaining(objects, r + 1)


def bin_to_int(sequence: Sequence[Any]) -> int:
    """Encode a given iterable containing binary values to an integer.

    For instances:
    >>> bin_to_int([1, 0, 1])
    5
    >>> bin_to_int("110")
    6

    Args:
        sequence: (Sequence): Sequence to encode

    Returns:
        int: encoded sequence
    """
    return reduce(lambda x, y: x * 2 + int(y), sequence, 0)


def all_close(a: Any, b: Any):
    def _all_close_func(i, j):
        if any((isinstance(i, str), isinstance(j, str), i is None, j is None)):
            return i == j
        return np.isclose(i, j)

    func = np.frompyfunc(_all_close_func, 2, 1)
    return np.shape(a) == np.shape(b) and np.all(func(a, b))
