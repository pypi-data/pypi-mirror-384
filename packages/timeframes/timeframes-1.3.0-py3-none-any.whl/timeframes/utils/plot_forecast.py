"""
Forecast visualization utilities.

Provides simple, publication-quality plots comparing
predictions and ground truth for time series forecasts.
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def plot_forecast(
    y_true,
    y_pred,
    title="Forecast vs Actual",
    output_size: int | None = None,
    start_index: int = 0,
    show_residuals: bool = False,
    figsize=(8, 4),
    savefig: str | None = None,
    dpi: int = 300,
):
    """
    Plot predicted vs actual values for time series forecasts.

    Automatically uses datetime x-axis if available.

    Parameters
    ----------
    y_true : array-like
        Ground truth values.
    y_pred : array-like
        Predicted values.
    title : str, default="Forecast vs Actual"
        Plot title.
    output_size : int, optional
        Forecast horizon (for labeling future steps).
    start_index : int, default=0
        Offset index for labeling the x-axis.
    show_residuals : bool, default=False
        Whether to plot residuals below the main chart.
    figsize : tuple, default=(8, 4)
        Figure size in inches.
    savefig : str, optional
        File path to save the figure (e.g. 'forecast.png'). If None, the plot is not saved.
    dpi : int, default=300
        Dots per inch for saved figure.
    """
    # Convert inputs to arrays, but keep datetime index if present
    if isinstance(y_true, (pd.Series, pd.DataFrame)) and isinstance(y_true.index, pd.DatetimeIndex):
        x = y_true.index
    else:
        y_true = np.array(y_true).flatten()
        x = np.arange(start_index, start_index + len(y_true))

    y_true = np.array(y_true).flatten()
    y_pred = np.array(y_pred).flatten()

    # Residuals toggle
    if show_residuals:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(figsize[0], figsize[1] + 2), height_ratios=[3, 1])
        ax = ax1
    else:
        fig, ax = plt.subplots(figsize=figsize)

    # Main plot
    ax.plot(x, y_true, label="Actual", color="black", lw=1.8)
    ax.plot(x, y_pred, label="Predicted", color="#1f77b4", lw=2.0, alpha=0.9)
    ax.set(title=title, xlabel="Date" if isinstance(x, pd.DatetimeIndex) else "Time index", ylabel="Value")
    ax.legend(frameon=False, fontsize=10)
    ax.grid(alpha=0.3, linestyle="--")

    # Forecast marker
    if output_size:
        k = len(x) - output_size
        ax.axvline(x[k], color="gray", lw=1, linestyle="--", alpha=0.5)
        ax.text(x[k], np.mean(y_true), "Forecast start", fontsize=9, color="gray")

    # Optional residuals plot
    if show_residuals:
        residuals = y_true - y_pred
        ax2.bar(x, residuals, color="tomato", alpha=0.7, width=20 if isinstance(x, pd.DatetimeIndex) else 0.8)
        ax2.axhline(0, color="gray", lw=1)
        ax2.set(title="Residuals", xlabel="Date" if isinstance(x, pd.DatetimeIndex) else "Time index")
        ax2.grid(alpha=0.3, linestyle="--")

    plt.tight_layout()

    # Save figure if requested
    if savefig is not None:
        fig.savefig(savefig, dpi=dpi, bbox_inches="tight")
        print(f"📁 Figure saved to {savefig} (dpi={dpi})")

    plt.show()
