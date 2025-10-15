import numpy as np
import pandas as pd



def make_windowed_dataset(
    df: pd.DataFrame | pd.Series,
    target_col: str | None = None,
    selected_cols: list[str] | None = None,
    input_size: int = 12,
    output_size: int = 1,
    oos_mode: bool = False,
    history_df: pd.DataFrame | None = None,
    return_index: bool = False,
):
    """
    Construct a supervised (X, y) dataset for time series forecasting.

    Optionally returns a DatetimeIndex corresponding to each output window start.
    Handles both:
    - Univariate forecasting (single column Series)
    - Multivariate forecasting (DataFrame with explicit target column)

    Parameters
    ----------
    df : pd.DataFrame or pd.Series
        Input time series data. Must contain `target_col` if multivariate.
    target_col : str, optional
        Target column name (required for multivariate mode).
        If df is a Series, it is treated as univariate.
    selected_cols : list of str, optional
        Predictor column names for multivariate mode.
        Ignored in univariate mode.
    input_size : int, default=12
        Number of past observations (lags) used as input.
    output_size : int, default=1
        Forecast horizon (number of future observations to predict).
    oos_mode : bool, default=False
        If True, append trailing `input_size` rows from `history_df`
        before creating windows (for continuity between in-sample and OOS).
    history_df : pd.DataFrame, optional
        Historical data used for OOS continuity.

    Returns
    -------
    X : np.ndarray
        Input features, shape = (n_samples, input_size, n_features)
    y : np.ndarray
        Targets, shape = (n_samples, output_size)

    Notes
    -----
    - In univariate mode: `X` contains lagged values of the same series.
    - In multivariate mode: predictors come from `selected_cols`,
      and the target column is separated by name.

    Examples
    --------
    >>> s = pd.Series(np.arange(1, 11), name="y")
    >>> X, y = make_windowed_dataset(s, input_size=3, output_size=2)
    >>> X.shape, y.shape
    ((6, 3, 1), (6, 2))

    >>> df = pd.DataFrame({'A': [1,2,3,4,5], 'B': [10,20,30,40,50]})
    >>> X, y = make_windowed_dataset(df, target_col='B', selected_cols=['A'], input_size=2)
    >>> X.shape, y.shape
    ((3, 2, 1), (3,))
    """
    # --- Case 1: Univariate (Series input) ---
    if isinstance(df, pd.Series):
        df = df.to_frame()
        target_col = df.columns[0]
        selected_cols = [target_col]

    # --- Case 2: Multivariate (DataFrame input) ---
    elif isinstance(df, pd.DataFrame):
        if target_col is None:
            raise ValueError("`target_col` must be specified for multivariate DataFrame input.")
        if selected_cols is None:
            selected_cols = [c for c in df.columns]

    else:
        raise TypeError("`df` must be a pandas Series or DataFrame.")

    # --- OOS continuity ---
    if oos_mode and history_df is not None:
        df = pd.concat([history_df.tail(input_size), df])

    # --- Core window logic ---
    data = df[selected_cols + [target_col]].values
    X, y, indices = [], [], []

    for i in range(len(data) - input_size - output_size + 1):
        X.append(data[i:i + input_size, :-1])
        y.append(data[i + input_size:i + input_size + output_size, -1])
        if return_index:
            # timestamp corresponding to forecast start (first predicted value)
            indices.append(df.index[i + input_size])

    X, y = np.array(X), np.array(y)

    # --- Squeeze last dim for 1-step forecasts ---
    if y.ndim > 1 and y.shape[-1] == 1:
        y = y.squeeze(-1)

    if return_index:
        return X, y, np.array(indices)
    return X, y


if __name__ == "__main__":

    def run_univariate():
        s = pd.Series(np.arange(1, 11), name="y")
        horizon = 2
        input_size = 4

        X, y = make_windowed_dataset(s,input_size=input_size, output_size=horizon)
        print("Univariate example:")
        print("Horizon:", horizon)
        print("Input Size:", input_size)
        print("X shape:", X.shape, "y shape:", y.shape)
        print("First sample:\n", X[0], "→", y[0])

    def run_multivariate():
        df = pd.DataFrame({letter:np.arange(1, 11) for letter in list("ABC")})

        horizon = 3
        target_col="B"
        selected = list("ABC")
        input_size = 7
        X, y = make_windowed_dataset(
            df,
            target_col=target_col,
            selected_cols=selected,
            input_size=input_size,
            output_size=horizon
        )
        print("Multivariate example:")
        print("Horizon:", horizon)
        print("Input Size:", input_size)
        print("Selected Predictors:", selected)
        print("Target:", target_col)
        print("X shape:", X.shape, "y shape:", y.shape)
        print(f"First sample:\n {X[0]} → {y[0]}")



    run_univariate()
    print()
    run_multivariate()
