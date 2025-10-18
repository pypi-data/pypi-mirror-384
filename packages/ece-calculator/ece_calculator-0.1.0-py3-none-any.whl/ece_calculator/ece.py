import numpy as np
from scipy.stats import norm


def get_ece(y_true: np.ndarray, mu: np.ndarray, sigma: np.ndarray, n_levels: int = 1000):
    """
    Regression Expected Calibration Error (ECE).

    Parameters
    y_true : np.ndarray
        True target values (N,)
    mu : np.ndarray
        Predicted means (N,)
    sigma : np.ndarray
        Predicted standard deviations (N,)
    n_levels : int
        Number of confidence levels to evaluate (default = 1000, higher = smoother).

    Returns
    float
        ECE in percentage. Smaller is better (0 = perfect calibration).
    """
    confidence_levels = np.linspace(1e-10, 1 - 1e-10, n_levels)
    coverage_differences = []

    for conf_level in confidence_levels:
        expected_coverage = conf_level

        z_value = norm.ppf(1 - (1 - conf_level) / 2)
        lower = mu - z_value * sigma
        upper = mu + z_value * sigma

        actual_coverage = np.mean((y_true >= lower) & (y_true <= upper))
        coverage_differences.append(np.abs(expected_coverage - actual_coverage))

    return 100 * np.mean(coverage_differences)