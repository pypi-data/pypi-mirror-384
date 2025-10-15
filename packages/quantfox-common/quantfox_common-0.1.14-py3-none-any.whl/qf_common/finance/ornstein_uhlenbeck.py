import logging
from typing import List, Tuple

import numpy as np
from joblib import Parallel, delayed
from scipy.optimize import minimize


def fit_ou_parameters(zscore: np.ndarray) -> Tuple[float, float, float]:
    """
    Fits Ornstein-Uhlenbeck (OU) process parameters to the given z-scores.

    Args:
    - zscore (np.ndarray): Array of z-scores.

    Returns:
    - Tuple[float, float, float]: The fitted OU parameters (theta, mu, sigma).
    """
    try:
        initial_guess = [1, np.mean(zscore), np.std(zscore)]

        result = minimize(
            ou_neg_log_likelihood, initial_guess, args=(zscore,), method="Powell"
        )
        return result.x
    except Exception as e:
        logging.error(f"Error fitting OU parameters for zscore: {e}")
        raise


def ou_neg_log_likelihood(
    params: Tuple[float, float, float], z_scores: np.ndarray
) -> float:
    """
    Calculates the negative log-likelihood of the Ornstein-Uhlenbeck (OU) process.

    Args:
    - params (Tuple[float, float, float]): The OU parameters (theta, mu, sigma).
    - z_scores (np.ndarray): Array of z-scores.

    Returns:
    - float: The negative log-likelihood.
    """
    try:
        theta, mu, sigma = params
        dt = 1

        x_t = z_scores[:-1]
        x_t_plus_1 = z_scores[1:]

        mean_shift = theta * (mu - x_t) * dt
        residuals = x_t_plus_1 - (x_t + mean_shift)

        n = len(z_scores)
        log_term = -n / 2 * np.log(2 * np.pi * sigma**2)
        residual_sum_squares = np.sum(residuals**2)

        log_likelihood = log_term - 1 / (2 * sigma**2) * residual_sum_squares
        return -log_likelihood
    except Exception as e:
        logging.error(f"Error calculating OU negative log-likelihood: {e}")
        raise


def calculate_theta(zscore_array: List[np.ndarray]) -> List[float]:
    """
    Calculates the theta parameter for an array of z-scores using parallel processing.

    Args:
    - zscore_array (List[np.ndarray]): List of arrays of z-scores.

    Returns:
    - List[float]: List of theta values.
    """
    try:
        ou_parameters = Parallel(n_jobs=1)(
            delayed(fit_ou_parameters)(zscore[::-1]) for zscore in zscore_array
        )
        theta_values = [params[0] for params in ou_parameters]
        return theta_values
    except Exception as e:
        logging.error(f"Error calculating theta values: {e}")
        raise
