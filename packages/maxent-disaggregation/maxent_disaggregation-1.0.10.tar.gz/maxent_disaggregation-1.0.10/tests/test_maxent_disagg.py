import numpy as np
import pytest
from maxent_disaggregation import maxent_disagg, sample_aggregate, sample_shares, plot_samples_hist, plot_covariances


def test_maxent_disagg_basic():
    # Test with simple shares and aggregate
    n = 1000
    mean_0 = 10
    shares = [0.5, 0.3, 0.2]
    sd_0 = 2
    samples, gamma = maxent_disagg(n=n, mean_0=mean_0, shares=shares, sd_0=sd_0)
    assert samples.shape == (n, 3)
    # Check that the means are close to expected
    assert np.allclose(samples.mean(axis=0).sum(), mean_0, rtol=0.1)
    # Check that the sum of each row is close to the aggregate
    row_sums = samples.sum(axis=1)
    assert np.allclose(row_sums.mean(), mean_0, rtol=0.1)


def test_sample_aggregate_normal():
    n = 1000
    mean = 5
    sd = 1
    samples = sample_aggregate(n=n, mean=mean, sd=sd, low_bound=-np.inf, high_bound=np.inf, log=False)
    assert np.abs(samples.mean() - mean) < 0.2
    assert np.abs(samples.std() - sd) < 0.2


def test_sample_aggregate_lognormal():
    n = 1000
    mean = 5
    sd = 1
    samples = sample_aggregate(n=n, mean=mean, sd=sd, low_bound=0, high_bound=np.inf, log=True)
    assert samples.min() >= 0
    assert np.abs(samples.mean() - mean) < 1.0  # lognormal mean is biased


def test_sample_shares_dirichlet():
    n = 1000
    shares = [0.6, 0.3, 0.1]
    samples, gamma = sample_shares(n=n, shares=shares)
    assert samples.shape == (n, 3)
    assert np.allclose(samples.mean(axis=0), shares, rtol=0.1)


def test_sample_shares_generalized_dirichlet():
    n = 1000
    shares = [0.5, 0.3, 0.2]
    sds = [0.05, 0.04, 0.03]
    samples, _ = sample_shares(n=n, shares=shares, sds=sds)
    assert samples.shape == (n, 3)
    assert np.allclose(samples.mean(axis=0), shares, rtol=0.1)


def test_plot_samples_hist_runs():
    n = 100
    mean_0 = 10
    shares = [0.5, 0.3, 0.2]
    sd_0 = 2
    samples, gamma = maxent_disagg(n=n, mean_0=mean_0, shares=shares, sd_0=sd_0)
    # Should not raise
    plot_samples_hist(samples, mean_0=mean_0, sd_0=sd_0, shares=shares)


def test_plot_covariances_runs():
    n = 100
    mean_0 = 10
    shares = [0.5, 0.3, 0.2]
    sd_0 = 2
    samples, gamma = maxent_disagg(n=n, mean_0=mean_0, shares=shares, sd_0=sd_0)
    # Should not raise
    plot_covariances(samples)


def test_sample_shares_partial_means():
    n = 1000
    # Partial means: one missing (np.nan)
    shares = [0.5, 0.3, np.nan]
    sds = [0.05, 0.04, 0.03]
    samples, _ = sample_shares(n=n, shares=shares, sds=sds)
    assert samples.shape == (n, 3)
    # Only check means for non-nan shares
    means = np.nan_to_num(shares, nan=0)
    sample_means = samples.mean(axis=0)
    mask = ~np.isnan(shares)
    assert np.allclose(sample_means[mask], means[mask], rtol=0.15)


def test_sample_shares_partial_sds():
    n = 1000
    shares = [0.4, 0.3, 0.3]
    # Partial sds: one missing (np.nan)
    sds = [0.05, np.nan, 0.03]
    samples, _ = sample_shares(n=n, shares=shares, sds=sds)
    assert samples.shape == (n, 3)
    # Check means are close to input shares
    assert np.allclose(samples.mean(axis=0), shares, rtol=0.15)


def test_sample_shares_partial_means_and_sds():
    n = 1000
    shares = [0.4, np.nan, 0.6]
    sds = [0.05, 0.02, np.nan]
    samples, _ = sample_shares(n=n, shares=shares, sds=sds)
    assert samples.shape == (n, 3)
    # Only check means for non-nan shares
    means = np.nan_to_num(shares, nan=0)
    sample_means = samples.mean(axis=0)
    mask = ~np.isnan(shares)
    assert np.allclose(sample_means[mask], means[mask], rtol=0.2)
