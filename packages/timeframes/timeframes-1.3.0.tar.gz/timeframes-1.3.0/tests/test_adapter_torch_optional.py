import pytest
import numpy as np
import timeframes as ts
from timeframes.adapters.base import ModelAdapter

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not installed")
def test_pytorch_model_integration_optional():
    """Ensure ModelAdapter integrates with PyTorch if available."""
    class TinyMLP(nn.Module):
        def __init__(self, input_size, output_size):
            super().__init__()
            self.fc = nn.Linear(input_size, output_size)
        def forward(self, x):
            return self.fc(x)

    def _train(model, X, y, lr=1e-2, epochs=10):
        X = torch.tensor(X, dtype=torch.float32)
        y = torch.tensor(y, dtype=torch.float32)
        if y.ndim == 1:
            y = y.unsqueeze(1)
        opt = optim.Adam(model.parameters(), lr=lr)
        loss_fn = nn.MSELoss()
        for _ in range(epochs):
            opt.zero_grad()
            loss = loss_fn(model(X), y)
            loss.backward()
            opt.step()

    def _predict(model, X):
        with torch.no_grad():
            X = torch.tensor(X, dtype=torch.float32)
            return model(X).numpy()

    df = ts.load_example("ts_components").iloc[:50]
    model = TinyMLP(input_size=18, output_size=2)

    adapter = ModelAdapter(
        model,
        fit_fn=lambda X, y: _train(model, X, y),
        predict_fn=lambda X: _predict(model, X)
    )

    metrics, _ = ts.validate(
        adapter, df,
        target_col="Composite",
        input_size=6,
        output_size=2,
        method="walkforward",
        step=2,
        mode="expanding",
        min_train_size=10
    )

    assert "mae" in metrics
    assert np.isfinite(metrics["rmse"])
