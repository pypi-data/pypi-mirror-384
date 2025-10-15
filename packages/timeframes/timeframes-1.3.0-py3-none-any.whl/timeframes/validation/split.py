import numpy as np
import pandas as pd

def split(df, ratios=(0.7, 0.2, 0.1), shuffle=False):
    """
    Split a time series DataFrame into train, validation, and test sets.

    Parameters
    ----------
    df : pd.DataFrame
        Time-indexed DataFrame.
    ratios : tuple of floats
        Fractions for (train, validation, test).
        Must sum to 1.0 or less (remaining ignored).
    shuffle : bool, default=False
        If True, randomize rows (not typical for time series).

    Returns
    -------
    train_df, val_df, test_df : pd.DataFrame
    """
    assert isinstance(df, pd.DataFrame), "Input must be a pandas DataFrame"
    assert abs(sum(ratios) - 1.0) < 1e-6, "Ratios must sum to 1.0"

    n = len(df)
    n_train = int(ratios[0] * n)
    n_val   = int(ratios[1] * n)
    n_test  = n - n_train - n_val

    if shuffle:
        df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)

    train = df.iloc[:n_train]
    val   = df.iloc[n_train:n_train + n_val]
    test  = df.iloc[n_train + n_val:]

    return train, val, test
