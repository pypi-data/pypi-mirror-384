"""
Validation and backtesting routines for time series forecasting.
"""

import numpy as np
import pandas as pd

from timeframes.metrics import evaluate_metrics
from timeframes.prep import make_windowed_dataset
from timeframes.utils.flattening import _handle_overlaps
from timeframes.utils.eval_helpers import _do_splits, _fit_oos_windows, _fit_preds

def validate(model, df, target_col, method="walkforward", folds=5,
             input_size=12, output_size=1, return_preds=False, **kwargs):
    """
    Run cross-validation (walk-forward or K-Fold) using windowed datasets.
    Automatically returns datetime-aligned predictions if return_preds=True.
    """
    # Prepare full supervised dataset with datetime indices
    X, y, idx = make_windowed_dataset(
        df,
        target_col=target_col,
        input_size=input_size,
        output_size=output_size,
        return_index=True,
    )

    splits = _do_splits(X, method, folds=folds, **kwargs)
    preds, trues = _fit_preds(model, splits, X, y)

    y_true, y_pred = _handle_overlaps(
        output_size, method, preds, trues, is_validation=True, **kwargs
    )
    metrics = evaluate_metrics(y_true, y_pred)

    if return_preds:
        # Align datetime index to final overlapping window length
        start = len(idx) - len(y_true)
        time_index = pd.DatetimeIndex(idx[start:])
        y_true = pd.Series(y_true, index=time_index, name="y_true")
        y_pred = pd.Series(y_pred, index=time_index, name="y_pred")
        return metrics, (y_true, y_pred)

    return metrics


def backtest(model, train_df, test_df, target_col, method="walkforward",
             input_size=12, output_size=1, return_preds=False, **kwargs):
    """
    Perform true out-of-sample (OOS) testing using continuity mode.
    Returns metrics and, optionally, datetime-aligned true/predicted series.
    """
    # Fit model and obtain test data, predictions, and corresponding timestamps
    y_test_seq, y_pred_seq, idx_test = _fit_oos_windows(
        model, target_col, input_size, output_size, train_df, test_df
    )

    # Handle multi-step overlaps
    y_true, y_pred = _handle_overlaps(
        output_size, method, y_test_seq, y_pred_seq, is_validation=False, **kwargs
    )

    metrics = evaluate_metrics(y_true, y_pred)

    if not return_preds:
        return metrics

    # --- Index alignment ---
    # idx_test is per-window; each step covers part of the timeline.
    # We reconstruct the equivalent full-length timestamp sequence.
    freq = pd.infer_freq(test_df.index) or "ME"
    time_index = pd.date_range(
        start=idx_test[0], periods=len(y_true), freq=freq
    )

    y_true = pd.Series(y_true, index=time_index, name="y_true")
    y_pred = pd.Series(y_pred, index=time_index, name="y_pred")

    return metrics, (y_true, y_pred)


if __name__ == "__main__":
    """
    Demonstration of Timeframes' validation and backtesting pipeline.
    """

    import random
    from sklearn.linear_model import LinearRegression
    from timeframes.validation.split import split
    from timeframes.utils.plot_forecast import plot_forecast
    from timeframes.utils.examples import load_example

    SEED = 42
    np.random.seed(SEED)
    random.seed(SEED)

    df =load_example("ts_components")
    print(df.head(), "\n")


    train, val, test = split(df, ratios=(0.6, 0.2, 0.2))
    print(f"Train: {len(train)} | Val: {len(val)} | Test: {len(test)}\n")

    model = LinearRegression()
    horizon = 6

    shared = {"model": model, "target_col": "Composite", "input_size": 6, "output_size": horizon, "step": 3, "return_preds": True}

    print("=== Walk-forward cross-validation ===")
    metrics_val, (y_true_val, y_pred_val) = validate(
        df=train, method="walkforward", mode="expanding", min_train_size=10, **shared
    )
    print("Validation metrics:", metrics_val, "\n")


    print("=== True out-of-sample backtest ===")
    train_val_df = pd.concat([train, val])
    metrics_test, (y_true_test, y_pred_test) = backtest(
        train_df=train_val_df, test_df=test, **shared
    )
    print("Backtest metrics:", metrics_test, "\n")

    print("Plotting forecast results...")
    plot_forecast(
        y_true_val,
        y_pred_val,
        title="Walk-Forward Validation Forecasts",
        show_residuals=True
    )
    plot_forecast(
        y_true_test,
        y_pred_test,
        title="True Out-of-Sample Forecast",
        show_residuals=True
    )
