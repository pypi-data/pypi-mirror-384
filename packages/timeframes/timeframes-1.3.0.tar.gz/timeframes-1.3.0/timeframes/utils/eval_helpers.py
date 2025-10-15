import numpy as np
from sklearn.base import clone

from timeframes.validation.walkforward import walkforward
from timeframes.validation.kfold import kfold
from timeframes.prep import make_windowed_dataset
from timeframes.adapters.base import ModelAdapter

def _do_splits(X, method, folds=5, **kwargs):
    if method == "walkforward":
        return walkforward(len(X), **kwargs)
    elif method == "kfold":
        return kfold(n_splits=folds).split(np.arange(len(X)))
    else:
        raise ValueError("method must be 'walkforward' or 'kfold'")

def _fit_preds(model, splits, X, y):
    adapter = ModelAdapter(model)  # ✅ harmless for sklearn models
    preds, trues = [], []

    for train_idx, val_idx in splits:
        model_ = adapter.model if hasattr(model, "fit") else adapter
        model_.fit(X[train_idx].reshape(len(train_idx), -1), y[train_idx])
        y_pred = model_.predict(X[val_idx].reshape(len(val_idx), -1))
        preds.append(y_pred)
        trues.append(y[val_idx])

    return preds, trues

def _fit_oos_windows(model, target_col, input_size, output_size, train_df, test_df):
    """
    Fit model on train_df and predict on test_df using window continuity mode.
    Returns y_test, y_pred, and the corresponding datetime index for y_test.
    """
    args = dict(target_col=target_col, input_size=input_size, output_size=output_size)

    # In-sample training windows (no index needed)
    X_train, y_train = make_windowed_dataset(train_df, **args)

    # Out-of-sample windows with continuity from training set
    X_test, y_test, idx_test = make_windowed_dataset(
        test_df, **args, oos_mode=True, history_df=train_df, return_index=True
    )

    # Fit and predict
    adapter = ModelAdapter(model)
    adapter.fit(X_train.reshape(len(X_train), -1), y_train)
    y_pred = adapter.predict(X_test.reshape(len(X_test), -1))

    return y_test, y_pred, idx_test
