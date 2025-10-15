import numpy as np
from typing import Iterator, Tuple

"""
Walk-forward validation for time series forecasting.

This module provides expanding and moving window strategies for evaluating
forecasting models over time. In each iteration, a model is trained on a
training window and validated on a future segment of the data. 

Use expanding windows when the training set should grow with each step, and
moving windows when a fixed-size history is preferred.

Modes
-----
- "expanding" : Uses all available data up to each step as the training window.
- "moving"    : Uses a fixed-size sliding window for the training data.

Typical workflow
----------------
1. Fit or tune your model on each (train, validation) split.
2. Collect validation losses or forecast errors over time.
3. Use results for robust evaluation or hyperparameter selection.
"""


def walkforward(
    n_samples: int,
    window_size: int | None = None,
    output_size: int = 1,
    step: int = 1,
    mode: str = "expanding",
    min_train_size: int | None = None
) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
    """
    Generate sequential (train_idx, val_idx) pairs for walk-forward validation.

    Parameters
    ----------
    n_samples : int
        Total number of observations.
    window_size : int | None, default=None
        Size of the training window for 'moving' mode.
        Ignored for 'expanding' mode.
    output_size : int, default=1
        Number of future samples in each validation window.
    step : int, default=1
        Step size (how far forward the window moves each iteration).
    mode : {'expanding', 'moving'}, default='expanding'
        - 'expanding': uses all available past data up to each fold.
        - 'moving': uses a fixed-size training window.
    min_train_size : int | None, default=None
        Minimum initial training size for expanding windows. If None, defaults to output_size.

    Yields
    ------
    (train_idx, val_idx) : tuple of np.ndarray
        Arrays of integer indices for training and validation sets.
    """

    if mode not in ("expanding", "moving"):
        raise ValueError("mode must be either 'expanding' or 'moving'")

    if output_size <= 0 or step <= 0:
        raise ValueError("horizon and step must be positive integers")

    if mode == "moving" and window_size is None:
        raise ValueError("window_size must be provided for 'moving' mode")

    if min_train_size is None:
        min_train_size = output_size

    if n_samples <= min_train_size + output_size:
        raise ValueError("Not enough samples for given parameters")

    if mode == "expanding":
        for end_val in range(min_train_size, n_samples - output_size + 1, step):
            train_idx = np.arange(0, end_val)
            val_idx = np.arange(end_val, end_val + output_size)
            yield train_idx, val_idx

    elif mode == "moving":
        for end_val in range(window_size, n_samples - output_size + 1, step):
            start_train = end_val - window_size
            train_idx = np.arange(start_train, end_val)
            val_idx = np.arange(end_val, end_val + output_size)
            yield train_idx, val_idx


if __name__ == "__main__":
    import pandas as pd

    df = pd.DataFrame({"y": range(12)})

    print("Expanding window example:")
    for i, (train_idx, val_idx) in enumerate(
        walkforward(len(df), output_size=2, step=3, mode="expanding", min_train_size=4)
    ):
        print(f"Step {i+1:02d} | train={train_idx} | val={val_idx}")

    print("\nMoving window example:")
    for i, (train_idx, val_idx) in enumerate(
        walkforward(len(df), window_size=5, output_size=2, step=2, mode="moving")
    ):
        print(f"Step {i+1:02d} | train={train_idx} | val={val_idx}")
