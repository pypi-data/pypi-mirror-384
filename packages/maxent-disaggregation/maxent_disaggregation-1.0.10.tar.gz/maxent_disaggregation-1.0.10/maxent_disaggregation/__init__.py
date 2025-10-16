"""maxent_disaggregation."""

from .shares import sample_shares
from .maxent_disaggregation import maxent_disagg
from .maxent_disaggregation import sample_aggregate
from .maxent_disaggregation import plot_samples_hist, plot_covariances
from .maxent_direchlet import find_gamma_maxent


__all__ = (
    "__version__",
    "maxent_disagg",
    "sample_shares",
    "sample_aggregate",
    "plot_samples_hist",
    "plot_covariances",
    "find_gamma_maxent",
    # Add functions and variables you want exposed in `maxent_disaggregation.` namespace here
)

__version__ = "1.0.10"
