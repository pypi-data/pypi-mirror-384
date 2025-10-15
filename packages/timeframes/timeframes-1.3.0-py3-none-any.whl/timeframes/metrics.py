"""
Metric utilities for time series forecasting.

Uses scikit-learn's built-in metrics for consistency, but wraps them
for a clean and unified API across MAE, RMSE, and SMAPE.
"""

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error

def mae(y_true, y_pred):
    """Mean Absolute Error"""
    return mean_absolute_error(y_true, y_pred)

def rmse(y_true, y_pred):
    """Root Mean Squared Error"""
    return np.sqrt(mean_squared_error(y_true, y_pred))

def smape(y_true, y_pred):
    """Symmetric Mean Absolute Percentage Error (%)"""
    denom = np.abs(y_true) + np.abs(y_pred)
    return 100 * np.mean(2 * np.abs(y_pred - y_true) / np.maximum(denom, 1e-8))

def evaluate_metrics(y_true, y_pred, metrics=None):
    """
    Evaluate a set of forecasting metrics.

    Parameters
    ----------
    y_true, y_pred : array-like
        Ground truth and predictions.
    metrics : list[str] or None
        List of metric names to compute.
        Default = ["mae", "rmse", "smape"]

    Returns
    -------
    dict
        Dictionary with metric names and float values.
    """
    if metrics is None:
        metrics = ["mae", "rmse", "smape"]

    y_true, y_pred = np.array(y_true), np.array(y_pred)
    results = {}

    return {
        "mae": mae(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "smape": smape(y_true, y_pred),
    }


if __name__ == "__main__":
    # Example quick test
    y_true = np.array([3, -0.5, 2, 7])
    y_pred = np.array([2.5, 0.0, 2, 8])
    print(evaluate_metrics(y_true, y_pred))
