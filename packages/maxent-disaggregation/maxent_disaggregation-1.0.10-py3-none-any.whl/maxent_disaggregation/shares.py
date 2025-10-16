"""
This module provides functions for sampling from Dirichlet and generalized Dirichlet distributions,
as well as hybrid approaches, given specified means (shares) and standard deviations (sds) for the shares.
It supports maximum entropy Dirichlet sampling, bias correction, and robust handling of edge cases such as
missing or partially specified parameters.

Functions
---------
- generalized_dirichlet(n, shares, sds):
    Generate random samples from a Generalised Dirichlet distribution with given shares and standard deviations.

- dirichlet_max_ent(n, shares, **kwargs):
    Generate samples from a Dirichlet distribution with maximum entropy given input shares.

- sample_shares(n, shares, sds=None, grad_based=False, threshold_shares=0.1, threshold_sd=0.2, **kwargs):
    This is the main function which handles all the different cases and samples from a distribution of
    shares based on given means and standard deviations, using the appropriate distribution or a hybrid
    approach depending on the completeness of the input information.

- hybrid_dirichlet(shares, size=None, sds=None, max_rel_bias=0.10, max_iter_bias_fix=20, max_iter_beta_sampling=1e3, **kwargs):
    Sample shares in the case of partial mean and sd information using a hybrid Dirichlet distribution with
    iterative bias correction.

- sample_dirichlet(shares, size=None, gamma_par=None, threshold_dirichlet=0.01, force_nonzero_samples=True, **kwargs):
    Wrapper to sample from a Dirichlet distribution with given shares and gamma concentration parameter,
    with pragmatic handling of small shape parameters to avoid numerical issues.

- check_sample_means_and_sds(sample, shares, sds, threshold_shares=0.1, threshold_sd=0.2):
    Check if the sample means and standard deviations deviate more than the specified thresholds from the
    specified shares and standard deviations, raising warnings if so.

- sample_from_beta(n, shares, sds, fix=True, max_iter=1e3):
    Generate random samples from independent Beta distributions with specified means and standard deviations,
    ensuring that the sum of samples across columns does not exceed 1 for each row.

- The module is robust to missing or partially specified input parameters, using uniform priors or hybrid
  approaches as needed.
- Warnings are raised if input parameters are inconsistent or if generated samples deviate significantly
  from specified means or standard deviations.
- The module is intended for probabilistic modeling of compositional data, such as branching ratios or shares
  that sum to one.

"""

import warnings
import numpy as np
from scipy.stats import gamma
import scipy.stats as stats
from .maxent_direchlet import find_gamma_maxent, dirichlet_entropy

# set the warning filter to always show warnings
warnings.simplefilter("always", UserWarning)


def generalized_dirichlet(n, shares, sds):
    """
    Generate random samples from a Generalised Dirichlet distribution
    with given shares and standard deviations.

    Reference:
    ----------------
    Plessis, Sylvain, Nathalie Carrasco, and Pascal Pernot.
    “Knowledge-Based Probabilistic Representations of Branching Ratios in
    Chemical Networks: The Case of Dissociative Recombinations.”
    The Journal of Chemical Physics 133, no. 13 (October 7, 2010): 134110.
    https://doi.org/10.1063/1.3479907.

    Parameters:
    ------------
        n (int): Number of samples to generate.
        shares (array-like): best-guess (mean) values for the shares.
            Must sum to 1!y.
        sds (array-like): Array of standard deviations for the shares.

    Returns:
    ------------
    tuple: A tuple containing:
        - sample (ndarray): An array of shape (n, lentgh(shares)) containing the generated samples.
        - None: Placeholder for compatibility with other functions (always returns None).
    """

    shares = np.asarray(shares)
    sds = np.asarray(sds)
    if not np.isclose(shares.sum(), 1):
        raise ValueError("The shares must sum to 1. Please check your input values.")
    if not np.all(np.isfinite(sds)):
        raise ValueError(
            "The standard deviations must be finite. Please check your input values."
        )
    if shares.shape != sds.shape:
        raise ValueError(
            "The shares and standard deviations must have the same shape. Please check your input values."
        )
    if np.any(sds < 0):
        raise ValueError(
            "The standard deviations must be non-negative. Please check your input values."
        )
    if np.any(shares < 0):
        raise ValueError(
            "The shares must be non-negative. Please check your input values."
        )
    if np.any(shares > 1):
        raise ValueError(
            "The shares must be less than or equal to 1. Please check your input values."
        )

    alpha2 = (shares / sds) ** 2
    beta2 = shares / (sds) ** 2
    k = len(alpha2)
    x = np.zeros((n, k))
    for i in range(k):
        x[:, i] = gamma.rvs(alpha2[i], scale=1 / beta2[i], size=n)
    sample = x / x.sum(axis=1, keepdims=True)
    return sample


def dirichlet_max_ent(n: int, shares: np.ndarray | list, **kwargs):
    """
    Generate samples from a Dirichlet distribution with maximum entropy.
    This function computes the gamma parameter that maximizes the entropy
    of the Dirichlet distribution given the input shares. It then generates
    `n` samples from the resulting Dirichlet distribution.
    Parameters:
        n (int): The number of samples to generate.
        shares (array-like): The input shares (probabilities) that define
            the Dirichlet distribution.
        **kwargs: Additional keyword arguments passed to the `find_gamma_maxent`
            function.
    Returns:
        tuple: A tuple containing:
            - sample (ndarray): An array of shape (n, len(shares)) containing
              the generated samples.
            - gamma_par (float): The computed gamma parameter that maximizes
              the entropy of the Dirichlet distribution.
    """

    gamma_par = find_gamma_maxent(shares, eval_f=dirichlet_entropy, **kwargs)
    sample = sample_dirichlet(shares * gamma_par, size=n, **kwargs)
    return sample, gamma_par


def sample_shares(
    n: int,
    shares: np.ndarray | list,
    sds: np.ndarray | list = None,
    grad_based: bool = False,
    threshold_shares: float = 0.1,
    threshold_sd: float = 0.2,
    **kwargs,
):
    """
    Samples from a distribution of shares based on given means and standard deviations.

    This function generates samples of shares using either a generalized Dirichlet
    distribution, a maximum entropy Dirichlet distribution, or a combination of both,
    depending on the availability of mean and standard deviation inputs.

    Parameters:
    ----------
    n : int
        Number of samples to generate.
    shares : np.ndarray | list
        Array or list of mean values for the shares. These should sum to 1 if fully specified.
    sds : np.ndarray | list, optional
        Array or list of standard deviations for the shares. If not provided, defaults to NaN.
    grad_based : bool, optional
        Whether to use gradient-based optimization for maximum entropy Dirichlet sampling.
        Default is False.
    threshold_shares : float, optional
        Threshold for the relative difference between the sample mean and the
        specified shares. If the difference exceeds this threshold, a warning is raised.
        Default is 0.1 (10%).
    threshold_sd : float, optional
        Threshold for the relative difference between the sample standard deviation and
        the specified sds. If the difference exceeds this threshold, a warning is raised.
        Default is 0.2 (20%).
    **kwargs : dict
        Additional keyword arguments passed to the underlying sampling functions.

    Returns:
    -------
    sample : np.ndarray
        A 2D array of shape (n, K), where K is the number of shares, containing the sampled values.
    gamma_par : np.ndarray
        Parameters of the Dirichlet or generalized Dirichlet distribution used for sampling.

    Notes:
    -----
    - If both means and standard deviations are provided for all shares, the generalized
      Dirichlet distribution is used.
    - If only means are provided, the maximum entropy Dirichlet distribution is used.
    - If no means are provided, a uniform Dirichlet distribution is used.
    - If a mix of known and unknown means/standard deviations is provided, a hierarchical
      approach is used to sample the shares (function called `hybrid_dirichlet`).
    - The function raises warnings if standard deviations are provided without corresponding
      mean values, as this is not recommended.


    """
    gamma_par = None  # set default value for gamma_par

    if sds is None:
        sds = np.full_like(shares, np.nan)
    shares = np.asarray(shares)
    sds = np.asarray(sds)

    K = len(shares)
    have_mean = np.isfinite(shares)
    have_sd = np.isfinite(sds)
    have_mean_only = np.isfinite(shares) & ~np.isfinite(sds)
    have_sd_only = np.isfinite(sds) & ~np.isfinite(shares)
    if np.sum(have_sd_only) > 0:
        warnings.warn(
            "You have standard deviations for shares without a best guess estimate. This is not recommended, please check your inputs. These will be treated as missing values and ignored for the calculation."
        )
    have_both = np.isfinite(shares) & np.isfinite(sds)

    if np.all(have_both):
        # use generalized dirichlet
        sample = generalized_dirichlet(n, shares, sds)
    elif np.all(have_mean_only):
        # maximize entropy for dirichlet
        sample, gamma_par = dirichlet_max_ent(
            n, shares, grad_based=grad_based, **kwargs
        )
    elif np.isfinite(shares).sum() == 0:
        # no information on the shares, use uniform dirichlet
        shares = np.asarray([1 / len(shares)] * len(shares))
        # The maximum entropy concentration parameter for a uniform Dirichlet distribution is gammapar = K
        sample = sample_dirichlet(shares=shares, gamma_par=K, size=n)
        # break out because it does not need to check the means and sd's
        return sample, None

    else:
        # If we have a mix of known and unknown shares, we handle this case using the Hybrid Dirichlet logic.
        sample = hybrid_dirichlet(shares=shares, size=n, sds=sds)

    # check if sample means and standard deviations deviate more than the threshold values:
    check_sample_means_and_sds(
        sample,
        shares,
        sds,
        threshold_shares=threshold_shares,
        threshold_sd=threshold_sd,
    )

    return sample, gamma_par


def hybrid_dirichlet(
    shares,
    size=None,
    sds=None,
    max_rel_bias=0.10,
    max_iter_bias_fix=20,
    max_iter_beta_sampling=1e3,
    **kwargs,
):
    """
    Function to sample in the case of partial mean and sd information using a hybrid
    Dirichlet distribution with iterative bias correction. Samples are generated
    from a combination of beta distributions for shares with both mean and sd,
    and a maximum-entropy Dirichlet distribution for shares with only mean values.
    This function iteratively adjusts the standard deviations of shares that
    exceed a specified relative bias threshold, ensuring that the final samples
    meet the desired accuracy in terms of relative bias.

    Parameters:
    ----------
    shares : array-like
        Array of mean values for the shares. These should sum to 1 if fully specified.
    size : int
        Number of samples to generate.
    sds : array-like, optional
        Array of standard deviations for the shares. If not provided, defaults to NaN.
    max_rel_bias : float, optional
        Maximum relative bias allowed for the generated samples. Default is 0.10 (10%).
    max_iter_bias_fix : int, optional
        Maximum number of iterations for bias correction. Default is 20.
    max_iter_rbeta3 : int, optional
        Maximum number of iterations for beta sampling. Default is 1e3.
    **kwargs : dict
        Additional keyword arguments passed to the underlying sampling functions.


    Returns:
    -------
    sample : np.ndarray
        A 2D array of shape (size, len(shares)) containing the sampled values.
    """
    # make sure that shares and sds are numpy arrays and exist
    shares = np.asarray(shares)
    if sds is None:
        sds = np.full_like(shares, np.nan)
    sds = np.asarray(sds)

    K = len(shares)
    if np.isnan(shares).sum() > 0:
        # fill the unkown means with a uniform prior
        shares[np.isnan(shares)] = (1 - np.nansum(shares)) / np.isnan(shares).sum()

    iter_count = 0
    while iter_count < max_iter_bias_fix:
        iter_count += 1
        sample = np.zeros((size, K))
        have_both = np.isfinite(shares) & np.isfinite(sds)
        have_mean_only = np.isfinite(shares) & ~np.isfinite(sds)

        # 1) Components with mean *and* SD  -->  Beta-truncated sampling
        if np.sum(have_both) > 0:
            sample[:, have_both] = sample_from_beta(
                size,
                shares[have_both],
                sds[have_both],
                fix=True,
                max_iter=max_iter_beta_sampling,
            )

        # 2) Components with mean only --> MaxEnt Dirichlet (rescaled afterwards)
        if np.sum(have_mean_only) > 0:
            alpha2 = shares[have_mean_only] / np.sum(shares[have_mean_only])
            sample_temp, _ = dirichlet_max_ent(size, alpha2, **kwargs)
            sample[:, have_mean_only] = sample_temp * (
                1 - sample[:, have_both].sum(axis=1, keepdims=True)
            )

        # Calculate the relative bias for each share
        rel_bias = np.abs(sample.mean(axis=0) - shares) / shares

        # Check if the relative bias is within the allowed threshold
        if np.all(rel_bias <= max_rel_bias):
            return sample

        ## 3) Bias check on the “have_both” block
        if np.any(have_both):
            if np.all(rel_bias[have_both] <= max_rel_bias):
                return sample  # Success – exit the loop

            # → At least one component is too far off: mark its SD as NaN
            sds[(have_both) & (rel_bias > max_rel_bias)] = np.nan
            warnings.warn(
                f"Relative bias exceeded {max_rel_bias} for component(s): "
                f"{np.where(rel_bias > max_rel_bias)[0]}. Their standard deviations have been set to NaN "
                "and will be handled with a Maximum-Entropy Dirichlet on the next iteration."
            )
        else:
            # If no components with both mean and SD left, we can exit the loop
            return sample


def sample_dirichlet(
    shares,
    size=None,
    gamma_par=None,
    threshold_dirichlet=0.01,
    force_nonzero_samples=True,
    **kwargs,
):
    """
    A wrapper function to sample from a Dirichlet distribution with a
    given set of shares and gamma concentration parameter.

    It differs from the default Dirichlet distroibution in that when the

    For each variable i whose mean value (alpha_i = gamma_par * share_i)
    that is below a `threshold`, a fallback parametrization of the Gamma distribution
    (which is used for sampling from the Dirichlet distribution) is applied to avoid
    zero or near-zero sampling. This is especially useful for very
    small shape parameters, which can cause numerical issues in in the dirichlet sampling.
    The following pragmatic workaround is used that sets:
        - alpha_i = 1 (shape) for shares below `threshold`
        - rate = 1 / alpha_i ensuring less extreme values.

    For more details, see the discussion in [rgamma()] under "small shape values" and
    the references there. This approach helps mitigate issues where numeric precision
    can push small Gamma-distributed values to zero (see
    https://stat.ethz.ch/R-manual/R-devel/library/stats/html/GammaDist.html).
    Note however that fix changes the expectation values (means) of the sampled parameters
    such that they can deviate from the inputed shares. If this is undesired
    set force_nonzero_samples=False.



    Parameters:
    -----------
    size : int
        The number of samples to generate.
    shares : array-like
        The input shares (probabilities) that define the Dirichlet distribution.
    gamma_par : float
        The gamma parameter that scales the shares for the Dirichlet distribution.
    threshold : float
        The threshold below which the shares are adjusted to avoid zero sampling.
    force_nonzero_samples : bool
        If True, forces non-zero samples by adjusting alphas and rate/scale within
        the gamma distribution. This may lead to biased means of the samples.
        If False, uses the original scipy implementation of the Dirichlet distribution.
        Note that in the case of very small alphas, this may lead to a large number zeros
        in the samples due to numerical issues. The means are unbiased though.

    Methods:
    --------
    sample():
        Generates samples from the Dirichlet distribution.
    """

    if gamma_par is None:
        alpha = np.asarray(shares)
    else:
        alpha = np.asarray(shares) * gamma_par

    if not force_nonzero_samples:
        print("Using scipy dirichlet!!!!!")
        return stats.dirichlet.rvs(alpha, size=size)
    else:
        l = len(alpha)
        rate = np.ones(l)
        rate[alpha < threshold_dirichlet] = 1 / alpha[alpha < threshold_dirichlet]
        alpha[alpha < threshold_dirichlet] = 1
        x = gamma.rvs(alpha, scale=1 / rate, size=(size, l))
        sample = x / x.sum(axis=1, keepdims=True)
        return sample


def check_sample_means_and_sds(
    sample,
    shares,
    sds,
    threshold_shares=0.1,
    threshold_sd=0.2,
):
    """
    Check if the sample means and standard deviations deviate more than the specified thresholds
    from the specified shares and standard deviations. If they do, a warning is raised.
    Parameters:
    ----------
    sample : np.ndarray
        The generated samples from the Dirichlet distribution.
    shares : np.ndarray
        The specified shares (mean values) for the Dirichlet distribution.
    sds : np.ndarray
        The specified standard deviations for the shares.
    threshold_shares : float, optional
        The threshold for the relative difference between the sample mean and the specified shares.
        If the difference exceeds this threshold, a warning is raised. Default is 0.1 (10%).
    threshold_sd : float, optional
        The threshold for the relative difference between the sample standard deviation and the specified sds.
        If the difference exceeds this threshold, a warning is raised. Default is 0.2 (20%).
    """
    if not isinstance(sample, np.ndarray):
        raise TypeError("Sample must be a numpy array.")
    if not isinstance(shares, np.ndarray):
        shares = np.asarray(shares)
    if not isinstance(sds, np.ndarray):
        sds = np.asarray(sds)

    sample_mean = np.mean(sample, axis=0)
    sample_sd = np.std(sample, axis=0)
    diff_mean = np.abs(sample_mean - shares) / shares
    diff_sd = np.abs(sample_sd - sds) / sds
    means_above_threshold = diff_mean > threshold_shares
    indices_above_threshold = np.where(means_above_threshold)[0]
    if np.any(means_above_threshold):
        warnings.warn(
            f"The generated samples for the shares have a mean that is more than {threshold_shares*100}% different from the specified shares. Please check your inputs. Reasons for this could be large relative uncertainties for the shares, or a small number of samples. To surpress this warning you can set a higher threshold_shares."
        )
        print(
            f"Shares above threshold: {diff_mean[means_above_threshold]},\
             shares: {shares[means_above_threshold]}, sample_mean: {sample_mean[means_above_threshold]},\
             indices: {indices_above_threshold}"
        )
    sds_above_threshold = diff_sd > threshold_sd
    indices_above_threshold = np.where(sds_above_threshold)[0]
    if np.any(sds_above_threshold):
        warnings.warn(
            f"The generated samples for the shares have a standard deviation that is more than {threshold_sd*100}% different from the specified sd's. Please note that the specified sd's might be incompetibale with the other constraints. Please check your inputs. To surpress this warning you can set a higher threshold_sd."
        )
        print(
            f"Sds above threshold: {diff_sd[sds_above_threshold]},\
             sds: {sds[sds_above_threshold]}, sample_sd: {sample_sd[sds_above_threshold]},\
             indices: {indices_above_threshold}"
        )


def sample_from_beta(n, shares, sds, fix=True, max_iter=1e3):
    """
    Generate random samples from independent Beta distributions with specified means (shares) and standard deviations (sds), ensuring that the sum of samples across columns does not exceed 1 for each row.

    Parameters
    ----------
    n : int
        Number of samples to generate.
    shares : array-like
        Array of mean values (between 0 and 1) for each Beta distribution.
    sds : array-like
        Array of standard deviations for each Beta distribution.
    fix : bool, optional (default=True)
        If True, automatically adjust invalid variance values to the maximum allowed for the given mean. If False, raise a ValueError when invalid parameter combinations are detected.
    max_iter : int, optional (default=1e3)
        Maximum number of iterations to attempt resampling rows where the sum exceeds 1.

    Returns
    -------
    x : ndarray
        An (n, k) array of samples, where k is the length of `shares`, such that each row sums to less than or equal to 1.

    Raises
    ------
    ValueError
        If the provided standard deviation is too large for the given mean (unless `fix=True`), or if a valid sample cannot be generated within `max_iter` iterations.

    Notes
    -----
    The function ensures that for each sample (row), the sum across all Beta-distributed variables does not exceed 1 by resampling as needed.

    """
    var = sds**2
    undef_comb = (shares * (1 - shares)) < var
    if not np.all(~undef_comb):
        if fix:
            var[undef_comb] = shares[undef_comb] ** 2
        else:
            raise ValueError(
                "The beta distribution is not defined for the parameter combination you provided! sd must be smaller or equal sqrt(shares*(1-shares))"
            )

    alpha = shares * (((shares * (1 - shares)) / var) - 1)
    beta = (1 - shares) * (((shares * (1 - shares)) / var) - 1)

    k = len(shares)
    x = np.zeros((n, k))
    for i in range(k):
        x[:, i] = np.random.beta(alpha[i], beta[i], size=n)

    larger_one = x.sum(axis=1) > 1
    count = 0
    while np.sum(larger_one) > 0:
        for i in range(k):
            x[larger_one, i] = np.random.beta(
                alpha[i], beta[i], size=np.sum(larger_one)
            )
        larger_one = x.sum(axis=1) > 1
        count += 1
        if count > max_iter:
            raise ValueError(
                "max_iter is reached. the combinations of shares and sds you provided does allow to generate `n` random samples that are not larger than 1. Either increase max_iter, or change parameter combination."
            )
    return x
