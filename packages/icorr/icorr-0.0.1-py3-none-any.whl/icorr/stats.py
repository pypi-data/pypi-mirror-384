# stats.py

from typing import Union, Tuple, Sequence
import numpy as np
from scipy import stats, integrate


def random_sample(omega: Tuple[int, int, int, int], n_draws: int=100000) -> np.ndarray:
    """
    Generates random sample from the identity correlation value Z.

    The omega tuple consists of counts:
    - omega[0] = N_xy : co-regulated (non-zero in both x and y)
    - omega[1] = N_x0 : x non-zero, y zero
    - omega[2] = N_0y : x zero, y non-zero
    - omega[3] = N_00 : both zero (not used in sampling)

    This function constructs a symmetric distribution over [-1, 1] using:
    - `w` from Beta(N_xy/2, N_xy/2), scaled to [-1, 1] as z = 1 - 2w
    - Optionally modulated by another `v` Beta(N_xy, (N_x0 + N_0y)/2) if asymmetric parts exist

    Parameters
    ----------
    omega : Tuple[int, int, int, int]
        A tuple of four counts: (N_xy, N_x0, N_0y, N_00).
    n_draws : int, optional (default=100000)
        Number of random samples to draw.

    Returns
    -------
    np.ndarray
        Array of random identity correlation values defined by the omega configuration.
    """
    k0 = omega[0]  # co-regulated count
    k12 = omega[1] + omega[2]  # dis-regulated counts

    # Draw symmetric Beta samples and map to [-1, 1]
    w = stats.beta.rvs(k0/2, k0/2, size=n_draws)
    z = 1 - 2 * w

    # If asymmetry exists, modulate z with another Beta sample
    if k12 > 0:
        v = stats.beta.rvs(k0, k12/2, size=n_draws)
        z *= v

    return z


def pvalues_numerical_approximation(z: float, omega: Tuple[int, int, int, int], loc: bool=True, eps: float=1e-10) -> float:
    """
    Computes the cumulative distribution function (CDF) of the random identity correlation value Z,
    based on the omega configuration using numerical integration.

    The omega tuple consists of counts:
    - omega[0] = N_xy : co-regulated (non-zero in both x and y)
    - omega[1] = N_x0 : x non-zero, y zero
    - omega[2] = N_0y : x zero, y non-zero
    - omega[3] = N_00 : both zero (not used in sampling)

    The identity-related variable Z is constructed as:
        Z = (1 - 2V) * W
    where:
        - V ~ Beta(N_xy/2, N_xy/2)
        - W ~ Beta(N_xy, (N_x0+N_0y)/2)

    The CDF is given by integrating over w:
        F_Z(z) = ∫ [1 - F_V(0.5 - z/(2w))] · f_W(w) dw

    Parameters
    ----------
    z : float
        The value at which the CDF of Z is evaluated.
    omega : Tuple[int, int, int, int]
        The omega tuple representing (N_xy, N_x0, N_0y, N_00).
    loc : bool, optional (default=True)
        Whether the correlation values are mean-centered.
    eps : float, optional (default=1e-10)
        Relative error tolerance.

    Returns
    -------
    float
        The estimated cumulative probability P(Z ≤ z).
    """
    k0 = omega[0] - int(loc)
    k12 = omega[1] + omega[2]

    def f_w(w: float) -> float:
        if k12 > 0:
            return stats.beta.pdf(w, k0, k12 / 2)
        return 1.0

    def F_v(v: float) -> float:
        return stats.beta.cdf(v, k0 / 2, k0 / 2)

    def integrand_dw(w: float) -> float:
        # Avoid divide-by-zero.
        if w == 0:
            return 0.0
        # calculate v based on z and w from the initial relationship Z = (1 - 2V) * W.
        v = 0.5 - z / (2 * w)
        # calculate probabilities based on `v` and `w` situation.
        if v <= 0:
            return f_w(w)
        elif v >= 1:
            return 0.0
        else:
            return (1 - F_v(v)) * f_w(w)

    # no randomness in the data if k0 == 0, because z=0.
    if k0 <= 0:
        return 1.0

    # no k12 does not need W, because f_w(w==1)=1.
    if k12 <= 0:
        v = (1 - z) / 2
        return F_v(v)

    # Only if k0 and k12 are present, calculate P(Z ≤ z) by integrating over v * dW from 0 to 1.
    result, _ = integrate.quad(integrand_dw, a=0, b=1, epsabs=eps, epsrel=eps, limit=100000)
    p_value = 1 - result
    return p_value


def pvalues_beta_approximation(
    z: float,
    omega: Union[Tuple[int, int, int, int], Sequence[Tuple[int, int, int, int]]],
    loc: bool=True,
) -> np.ndarray:
    """
    Computes the cumulative distribution function (CDF) of the random identity correlation value Z,
    based on the omega configuration using a single symmetric beta distribution U with approximated parameters
    alpha = beta 0 f_approx(omega).

    The omega tuple consists of counts:
    - omega[0] = N_xy : co-regulated (non-zero in both x and y)
    - omega[1] = N_x0 : x non-zero, y zero
    - omega[2] = N_0y : x zero, y non-zero
    - omega[3] = N_00 : both zero (not used in sampling)

    The identity-related variable Z is approximated as:
        Z = (1 - 2U)
    where:
        - U ~ Beta(f_approx(omega), f_approx(omega))

    Parameters
    ----------
    z : float
        The value at which the CDF of Z is evaluated.
    omega : Tuple[int, int, int, int] or Sequence[omegas, ...]
        The omega tuple representing (N_xy, N_x0, N_0y, N_00).
    loc : bool, optional (default=True)
        Whether the correlation values are mean-centered.

    Returns
    -------
    float or np.ndarray
        The estimated cumulative probabilities P(Z ≤ z).
    """
    def f_approx(
        omega: Union[Tuple[int, int, int, int], Sequence[Tuple[int, int, int, int]]],
        loc: bool,
    ) -> float:
        omega = np.atleast_2d(omega)
        k0 = omega[:, 0]
        k12 = omega[:, 1] + omega[:, 2]
        parameter = (k0 - int(loc))/2 + k12/2 + (k12 ** 1.951) / (2 * np.pi * k0)
        return parameter

    # Compute p_values from shifted beta distribution on [-1, 1]
    dofs = f_approx(omega, loc=loc)
    p_values = stats.beta.sf(z, a=dofs, b=dofs, loc=-1, scale=2)
    return p_values


def fdr_correction(pvals: Union[float, Sequence]) -> np.ndarray:
    """
    Adjusts p-values using the Benjamini-Hochberg FDR correction procedure.

    Parameters
    ----------
    pvals : array_like, 1D
        List or array of p-values from individual hypothesis tests.

    Returns
    -------
    np.ndarray
        P-values adjusted for false discovery rate (FDR). NaNs are preserved.
    """
    pvals = np.asarray(pvals)
    assert pvals.ndim == 1, "pvals must be 1-dimensional, shape (n,)"

    # Initialize output with NaNs
    out = np.full_like(pvals, np.nan, dtype=np.float64)

    # Mask valid (non-NaN) entries
    nan_mask = ~np.isnan(pvals)
    valid_pvals = pvals[nan_mask]
    if valid_pvals.size == 0:
        return out  # all NaNs, return early

    # Sort and get original indices
    sort_idx = np.argsort(valid_pvals)
    sorted_pvals = valid_pvals[sort_idx]

    # Apply Benjamini-Hochberg procedure
    n = len(sorted_pvals)
    correction_factor = np.arange(1, n + 1) / float(n)
    adjusted_pvals = sorted_pvals / correction_factor
    adjusted_pvals = np.minimum.accumulate(adjusted_pvals[::-1])[::-1]
    adjusted_pvals = np.clip(adjusted_pvals, 0, 1)

    # Map adjusted p-values back to original indices
    adjusted_pvals_sorted = np.empty_like(adjusted_pvals)
    adjusted_pvals_sorted[sort_idx] = adjusted_pvals
    out[nan_mask] = adjusted_pvals_sorted
    return out
