# icorr.py

import numpy as np
from typing import Tuple, Union, Sequence


def drop_nan(x: Union[Sequence[float], np.ndarray], y: Union[Sequence[float], np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Removes elements from `x` and `y` where either array has a NaN at the corresponding index.

    Parameters:
    ----------
    x : array-like
        The first input array or sequence of numerical values.
    y : array-like
        The second input array or sequence of numerical values.

    Returns:
    -------
    x, y
        The returned arrays x and y are filtered to only include positions where both input values are valid (non-NaN).
    """
    x, y = np.asarray(x), np.asarray(y)
    mask = ~(np.isnan(x) | np.isnan(y))
    return x[mask], y[mask]


def omega(x: Union[Sequence[float], np.ndarray], y: Union[Sequence[float], np.ndarray]) -> Tuple[int, int, int, int]:
    """
    Counts regulation types between two numerical arrays `x` and `y` after removing NaN entries.

    Regulation types are categorized as follows:
    - N_xy (co-regulation): both x and y are non-zero.
    - N_x0 (dis-regulation x): x is non-zero, y is zero.
    - N_0y (sid-regulation y): x is zero, y is non-zero.
    - N_00 (co-not-regulated): both x and y are zero.

    Parameters
    ----------
    x : array-like
        First input array of numerical values.
    y : array-like
        Second input array of numerical values.

    Returns
    -------
    (N_xy, N_x0, N_0y, N_00)
        The returned omega tuple represents:
        - N_xy : Number of positions where both x and y are non-zero.
        - N_x0 : Number of positions where x is non-zero and y is zero.
        - N_0y : Number of positions where x is zero and y is non-zero.
        - N_00 : Number of positions where both x and y are zero.
    """
    # Filter input arrays x and y.
    x, y = np.asarray(x), np.asarray(y)
    x, y = drop_nan(x, y)

    # Identify not values.
    x_zero, y_zero = (x == 0), (y == 0)

    # Count the 4 cases.
    n_zero = np.sum(x_zero & y_zero)
    n_dis_x = np.sum(~x_zero & y_zero)
    n_dis_y = np.sum(x_zero & ~y_zero)
    n_xy = np.sum(~x_zero & ~y_zero)
    return n_xy, n_dis_x, n_dis_y, n_zero


def identity_correlation(x: Union[Sequence[float], np.ndarray], y: Union[Sequence[float], np.ndarray], loc: bool = True) -> float:
    """
    Computes the identity correlation value between `x` and `y`.

    Parameters
    ----------
    x : array-like
        First input array of numerical values.
    y : array-like
        Second input array of numerical values.
    loc : bool, optional (default=True)
        Whether to mean-center `x` and `y` before computation.
        This is necessary if the data are not already centered around zero (i.e., not Normal(0, σ)).

    Returns
    -------
    icorr: float
        The identity correlation value. Returns NaN if both `x` and `y` are all zeros.

    Comments
    --------
    For more information see Bayer etal. 2025.
    """
    # Filter input arrays `x` and `y`.
    x, y = np.asarray(x), np.asarray(y)
    x, y = drop_nan(x, y)

    # Shift location to 0 if True.
    if loc:
        x, y = x - x.mean(), y - y.mean()

    # Sum of squared deviations from identity line between `x` and `y`.
    diff = np.sum((x - y) ** 2)
    # Sum of squared variability in `x` and `y`.
    var = np.sum(x ** 2) + np.sum(y ** 2)

    # If no variance exists, the icorr is undefined.
    if var == 0.0:
        return np.nan

    # Calculate the icorr value.
    icorr = 1 - (diff / var)
    return icorr
