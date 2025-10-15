import numpy as np
from scipy.optimize import minimize


def nelson_siegel(tau, beta0, beta1, beta2, lambd):
    """
    Compute the Nelson-Siegel yield curve.

    Parameters:
    - tau (array-like): Maturities (in years).
    - beta0 (float): Long-term interest rate level.
    - beta1 (float): Short-term component (slope).
    - beta2 (float): Medium-term component (curvature).
    - lambd (float): Decay factor that determines the exponential decay speed.

    Returns:
    - np.ndarray: Fitted yields for the given maturities.
    """
    term1 = beta0
    term2 = beta1 * ((1 - np.exp(-tau / lambd)) / (tau / lambd))
    term3 = beta2 * (
        ((1 - np.exp(-tau / lambd)) / (tau / lambd)) - np.exp(-tau / lambd)
    )
    return term1 + term2 + term3


def ns_loss(params, maturities, yields):
    """
    Loss function for fitting the Nelson-Siegel model.

    Parameters:
    - params (list): List of parameters [beta0, beta1, beta2, lambd].
    - maturities (array-like): Bond maturities.
    - yields (array-like): Observed bond yields corresponding to the maturities.

    Returns:
    - float: Sum of squared errors between observed and model yields.
    """
    beta0, beta1, beta2, lambd = params
    fitted = nelson_siegel(maturities, beta0, beta1, beta2, lambd)
    return np.sum((yields - fitted) ** 2)


def fit_nelson_siegel(maturities, yields):
    """
    Fit the Nelson-Siegel yield curve model to observed market data.

    Parameters:
    - maturities (array-like): Bond maturities (in years).
    - yields (array-like): Observed yields for each maturity.

    Returns:
    - np.ndarray: Optimal parameters [beta0, beta1, beta2, lambd] minimizing the loss.
    """
    initial_guess = [0.03, -0.02, 0.02, 2.0]
    bounds = [(-1, 1), (-1, 1), (-1, 1), (0.01, 10)]
    result = minimize(ns_loss, initial_guess, args=(maturities, yields), bounds=bounds)
    return result.x
