"""
Basic smoke tests for the Timeframes package.

These are simple integration-level checks that ensure the main
functions work end-to-end without shape or runtime errors.
"""

import numpy as np
import timeframes as ts
from tests.helpers import make_demo_data, make_model


def test_make_windowed_dataset():
    """Basic sanity check for dataset preparation."""
    df = make_demo_data(30)
    X, y = ts.make_windowed_dataset(df, target_col="y", input_size=5, output_size=2)

    assert X.ndim == 3
    assert y.ndim >= 1
    assert X.shape[0] == y.shape[0]
    assert X.shape[1] == 5
    assert y.shape[1] == 2


def test_walkforward_indices_are_sequential():
    """Check that walk-forward indices are in correct order."""
    splits = list(ts.walkforward(
        n_samples=20,
        output_size=2,
        step=2,
        mode="expanding",
        min_train_size=6
    ))

    assert len(splits) > 0
    for train_idx, val_idx in splits:
        assert train_idx[-1] < val_idx[0]
        assert len(val_idx) == 2


def test_validate_produces_metrics_and_equal_shapes():
    """End-to-end validation: training, prediction, metrics."""
    df = make_demo_data(40)
    model = make_model()

    metrics, (y_true, y_pred) = ts.validate(
        model,
        df,
        target_col="y",
        method="walkforward",
        input_size=6,
        output_size=2,
        step=2,
        mode="expanding",
        min_train_size=10,
        return_preds=True,
    )

    assert isinstance(metrics, dict)
    assert set(metrics.keys()) >= {"mae", "rmse", "smape"}
    assert len(y_true) == len(y_pred)
    assert np.all(np.isfinite(list(metrics.values())))


def test_backtest_runs_and_returns_dict():
    """Ensure backtest executes and returns expected metrics."""
    df = make_demo_data(50)
    train, val, test = ts.split(df, ratios=(0.6, 0.2, 0.2))

    model = make_model()
    metrics = ts.backtest(model, train, test, target_col="y", input_size=5, output_size=2, step=2)

    assert isinstance(metrics, dict)
    assert set(metrics.keys()) >= {"mae", "rmse", "smape"}


def test_metrics_are_numeric_and_reasonable():
    """Quick check for metrics' numeric validity."""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.1, 1.9, 3.2])

    result = ts.evaluate_metrics(y_true, y_pred)
    assert all(isinstance(v, float) for v in result.values())
    assert result["rmse"] > 0
    assert 0 <= result["smape"] < 10


def test_plot_forecast_executes_without_error():
    """Smoke test for plotting — checks for runtime errors only."""
    y_true = np.linspace(0, 5, 10)
    y_pred = y_true + np.random.randn(10) * 0.1

    # Plot should run without throwing errors
    ts.plot_forecast(y_true, y_pred, title="Forecast Smoke Test")
