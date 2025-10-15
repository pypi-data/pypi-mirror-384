#
# Identity correlation analysis - icorr
#

from .icorr import identity_correlation, omega
from .stats import random_sample, pvalues_numerical_approximation, pvalues_beta_approximation, fdr_correction
from .plots import coherence_map

__all__ = ["coherence_map", "fdr_correction", "identity_correlation", "omega", "pvalues_beta_approximation",
           "pvalues_numerical_approximation", "random_sample"]

__version__ = "0.1.0"
__author__ = "Florian P. Bayer"
__email__ = "f.bayer@tum.de"
