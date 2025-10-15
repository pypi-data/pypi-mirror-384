import numpy as np
import timeframes as ts
from timeframes.adapters.base import ModelAdapter


class ReadWriteModel:
    """Model that uses custom read/write instead of fit/predict."""
    def __init__(self):
        self.bias = 0
    def read(self, X, y):
        self.bias = np.mean(y) - np.mean(X)
    def write(self, X):
        base = np.mean(X, axis=1) + self.bias
        return np.column_stack([base, base * 0.9])  # two-step forecast


def test_custom_read_write_adapter():
    """Validate adapter functionality with non-standard methods."""
    df = ts.load_example("ts_components").iloc[:40]
    model = ReadWriteModel()

    adapter = ModelAdapter(model, fit_fn=model.read, predict_fn=model.write)
    metrics, _ = ts.validate(
        adapter, df,
        target_col="Composite",
        input_size=6,
        output_size=2,
        method="walkforward",
        step=2,
        mode="expanding",
        min_train_size=10,
        return_preds=True   # <-- added
    )

    assert all(k in metrics for k in ("mae", "rmse", "smape"))
    assert np.isfinite(metrics["rmse"])
