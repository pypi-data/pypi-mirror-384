# plots.py

from matplotlib import pyplot as plt
import numpy as np

DEFAULT_PALETTE = {'coherent': 'green', 'anti_coherent':'red', 'dis_coherent': 'purple', 'not': 'black'}


def _get_plotting_category_masks(x, y):
    """
    Helper function for plotting_categories
    """
    x, y = np.asarray(x), np.asarray(y)
    x_zero, y_zero = (x == 0), (y == 0)
    x_down, y_down = (x < 0), (y < 0)
    x_up, y_up = (x > 0), (y > 0)

    co_not = (x_zero & y_zero)
    dis_coherent = (~x_zero & y_zero) | (x_zero & ~y_zero)
    anti_coherent = (x_down & y_up) | (x_up & y_down)
    coherent = (x_down & y_down) | (x_up & y_up)

    return {'coherent': coherent, 'anti_coherent':anti_coherent, 'dis_coherent': dis_coherent, 'not': co_not}


def coherence_map(x, y, ax=None, alpha=1.0, dose_resolution=1/2, palette=DEFAULT_PALETTE, **kwargs):
    """
    Plots a potency coherence plot.

    Parameters
    ----------
    x : array-like
        The first input array or sequence of numerical values.
    y : array-like
        The second input array or sequence of numerical values.
    ax : matplotlib axis object, optional (default=None)
        Whether to mean-center `x` and `y` before computation.
        This is necessary if the data are not already centered around zero (i.e., not Normal(0, σ)).
    alpha : float, optional (default=1.0)
        Alpha parameter to tune color alpha of data points.
    dose_resolution : float, optional (default=1/2)
        Experimental dose resolution to tune color alpha of data points.
        If 0, None, or False, the diagonal lines will not be plotted.
    palette : dict, optional (default=DEFAULT_PALETTE)
        Dictionary of color palettes for the different regulation categories.
        DEFAULT_PALETTE = {'coherent': 'green', 'anti_coherent':'red', 'dis_coherent': 'purple', 'not': 'black'}

    Keyword arguments
    -----------------
    x_label, y_label, title, x_lim, y_lim, x_ticks, y_ticks, aspect, ...

    Returns
    -------
    matplotlib axis object
    """
    # Clean input
    x, y = np.asarray(x), np.asarray(y)

    # Plot per cell line for up and down
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 5))

    # Plot the dots over all experiments. order: coherent, anti_coherent, dis_coherent, co_not
    for reg_type, mask in _get_plotting_category_masks(x, y).items():
        color = palette.get(reg_type, 'gray')
        ax.scatter(x[mask], y[mask], zorder=2, alpha=alpha, color=color)

    # Diagonal lines
    ax.axline(slope=1, xy1=(0, 0), color='black', ls='--', zorder=1, lw=0.5)
    ax.axline(slope=-1, xy1=(0, 0), color='black', ls='--', zorder=1, lw=0.5)
    if dose_resolution:
        identity_border = np.sqrt(2) * dose_resolution
        ax.axline(slope=1, xy1=(0, identity_border), color='black', ls='--', zorder=3, lw=0.5)
        ax.axline(slope=1, xy1=(0, -identity_border), color='black', ls='--', zorder=3, lw=0.5)
        ax.axline(slope=-1, xy1=(0, identity_border), color='black', ls='--', zorder=3, lw=0.5)
        ax.axline(slope=-1, xy1=(0, -identity_border), color='black', ls='--', zorder=3, lw=0.5)

    # Zero lines
    ax.axhline(y=0, color='black', zorder=1, ls='-', lw=0.5)
    ax.axvline(x=0, color='black', zorder=1, ls='-', lw=0.5)

    # Labels
    ax.set_xlabel(kwargs.get('x_label', 'X'))
    ax.set_ylabel(kwargs.get('y_label', 'Y'))
    ax.set_title(kwargs.get('title', None))

    # Axes
    ax.set_xlim(* kwargs.get('x_lim', (-6, 6)))
    ax.set_ylim(* kwargs.get('y_lim', (-6, 6)))
    ax.set_xticks(kwargs.get('x_ticks', range(-6, 7)))
    ax.set_xticks(kwargs.get('y_ticks', range(-6, 7)))
    ax.set_aspect(kwargs.get('aspect', 'equal'), adjustable='box')

    return ax