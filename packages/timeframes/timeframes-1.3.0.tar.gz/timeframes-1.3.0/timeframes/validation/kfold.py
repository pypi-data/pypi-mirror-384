"""
K-Fold cross-validation wrapper for model selection in time series.

Implements standard (non-temporal) K-fold splitting as used for
in-sample (INS) hyperparameter optimization in:

    Goulet-Coulombe, F. (2022)
    "How is Machine Learning Useful for Macroeconomic Forecasting?"

Temporal order is **not enforced** here because folds are drawn
within the in-sample segment only; this stage is for parameter
tuning, not out-of-sample forecast evaluation.

For true forecasting validation, use:
    - timeframes.validation.walkforward   (expanding / moving windows)
    - timeframes.validation.poos          (pseudo-out-of-sample)
"""

from typing import Iterator, Tuple
import numpy as np
from sklearn.model_selection import KFold


def kfold(
    n_splits: int = 5,
    shuffle: bool = True,
    seed: int = 42
) -> KFold:
    """
    Return a configured scikit-learn KFold splitter.

    Parameters
    ----------
    n_splits : int, default=5
        Number of folds.
    shuffle : bool, default=True
        Whether to shuffle before splitting. Recommended True for
        Goulet-Coulombe-style in-sample cross-validation.
    seed : int, default=42
        Random seed for reproducibility (only used if shuffle=True).

    Returns
    -------
    sklearn.model_selection.KFold
        A ready-to-use splitter object.
    """
    if shuffle:
        return KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    else:
        return KFold(n_splits=n_splits, shuffle=False)


if __name__ == "__main__":
    import pandas as pd

    # Example: simple synthetic time series
    df = pd.DataFrame({"y": range(12)})

    print("K-Fold (shuffle=True, n_splits=4):")
    splitter = kfold(n_splits=4, shuffle=True, seed=0)
    for i, (train_idx, val_idx) in enumerate(splitter.split(df)):
        print(f"Fold {i+1}: train={train_idx}, val={val_idx}")

    print("\nK-Fold (shuffle=False, n_splits=4):")
    splitter = kfold(n_splits=4, shuffle=False)
    for i, (train_idx, val_idx) in enumerate(splitter.split(df)):
        print(f"Fold {i+1}: train={train_idx}, val={val_idx}")

    # Typical macro-forecasting workflow
    # ----------------------------------
    # 1. Split your sample into INS (train) and OOS (test) manually.
    # 2. Within INS, call this KFold to tune hyperparameters.
    # 3. Freeze tuned parameters and evaluate with walk-forward / POOS.
