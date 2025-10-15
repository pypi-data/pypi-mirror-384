import numpy as np

def flatten_stepwise(y_true: np.ndarray, step: int, output_size: int) -> np.ndarray:
    """
    Flatten a rolling (n_windows × output_size) array stepwise according to
    forecast output_size and step size.

    Example
    -------
    For step=2, output_size=4:
      take y[0][:2], then y[1][:2], y[2][:2], ...,
      and finally the remaining tail from the last window.

    Parameters
    ----------
    y_true : np.ndarray
        Array of shape (n_windows, output_size).
    step : int
        Step size used in the walkforward procedure.
    output_size : int
        Forecast horizon .

    Returns
    -------
    flat : np.ndarray
        1D vector reconstructed stepwise without repeats.
    """
    n_windows = y_true.shape[0]
    result = []

    for i in range(n_windows):
        # take first `step` elements of each window
        result.extend(y_true[i, :step])
    # append the final uncovered tail from the last window
    tail_start = n_windows * step - (n_windows - 1) * step
    result.extend(y_true[-1, step:])  # ensures full coverage of last forecast
    return np.array(result[: (n_windows - 1) * step + output_size])


def _aggregate_overlaps(y_seq, y_pred_seq, step: int, output_size: int):
    """
    Combine overlapping multi-step forecasts using step-aware averaging.
    """
    timeline = {}
    start_idx = 0

    for y_true, y_pred in zip(y_seq, y_pred_seq):
        seq_len = min(output_size, len(y_true), len(y_pred))
        for i in range(seq_len):
            idx = start_idx + i
            if idx not in timeline:
                timeline[idx] = {"truth": [], "pred": []}
            timeline[idx]["truth"].append(y_true[i])
            timeline[idx]["pred"].append(y_pred[i])
        start_idx += step  # advance window respecting walkforward step

    # Average overlapping predictions per index
    y_true_flat, y_pred_flat = [], []
    for i in sorted(timeline.keys()):
        y_true_flat.append(np.mean(timeline[i]["truth"]))
        y_pred_flat.append(np.mean(timeline[i]["pred"]))

    return np.array(y_true_flat), np.array(y_pred_flat)


def _handle_overlaps(output_size, method, preds, trues=None, is_validation=True, **kwargs):
    """
    Handle overlapping forecasts for both validation and backtesting routines.

    Args:
        output_size (int): Forecast horizon.
        method (str): Validation method (e.g., 'walkforward', 'kfold').
        preds (array-like): Predicted sequences.
        trues (array-like, optional): True sequences (only for validation).
        is_validation (bool): Whether this call is from validation (default: True).
        **kwargs: Additional parameters (e.g., step).

    Returns:
        tuple: (y_true, y_pred) aligned for metric computation.
    """
    step = kwargs.get("step", 1)

    if output_size > 1 and method == "walkforward":
        if is_validation:
            # Chronologically flatten true and predicted sequences
            y_pred = flatten_stepwise(np.array(preds), step=step, output_size=output_size)
            y_true = flatten_stepwise(np.array(trues), step=step, output_size=output_size)

            # Aggregate overlaps (aligns sequences)
            y_true, y_pred = _aggregate_overlaps(y_true, y_pred, step, output_size)

            # Align lengths
            min_len = min(len(y_true), len(y_pred))
            y_true = y_true[:min_len]
            y_pred = y_pred[:min_len]
        else:
            # Backtesting overlap handling
            y_true, y_pred = _aggregate_overlaps(trues, preds, step, output_size)
    else:
        if is_validation:
            y_true = np.concatenate(trues)
            y_pred = np.concatenate(preds)
        else:
            y_true, y_pred = trues, preds

    return y_true, y_pred