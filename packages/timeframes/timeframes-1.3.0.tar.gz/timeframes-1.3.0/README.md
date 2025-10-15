<!-- LOGO -->
<p align="center">
  <img src="https://github.com/user-attachments/assets/c2bb88b8-1edb-4fdc-8b11-3e6966481a88" width="350" alt="timeframes logo"/>
</p>

<p align="center">
  <strong>A lightweight framework for time series validation, backtesting, and visualization.</strong><br/>
Timeframes provides simple and efficient tools for splitting, validating, and evaluating forecasting models — without unnecessary dependencies or boilerplate.
</p>

---

## 🧠 Need help?

Try **[TimeframesGPT](https://chatgpt.com/g/g-68ec3fa47a808191afbe09cbd63ab611-timeframesgpt-v1-0)** —  
a specialized assistant trained on the full Timeframes codices.

---

## Installation

```bash
pip install timeframes
```

---

## Quick Example

```python
import timeframes as ts
from sklearn.linear_model import LinearRegression

# Load example data
df = ts.load_example("air_passengers")  # or "ts_components", "ts_components_complex"

# Split into train, validation, and test
train, val, test = ts.split(df, ratios=(0.7, 0.2, 0.1))

# Validate using walk-forward cross-validation
model = LinearRegression()
report, (y_true, y_pred) = ts.validate(
    model, df, target_col="AirPassengers", method="walkforward", mode="expanding", folds=5, return_preds=True
)

print(report)
# {'mae': 0.213, 'rmse': 0.322, 'smape': 3.9}

# Visualize forecast results
ts.plot_forecast(y_true, y_pred, title="Walk-Forward Forecast", show_residuals=True)
```
<img width="800" alt="example" src="https://github.com/user-attachments/assets/8c1183db-ba37-40b2-8c36-4412d05f3ad2" />

💡 *You can list all built-in datasets with `ts.list_examples()`.*

---

## ✨ Features

* **Minimal** — depends only on NumPy and pandas.
* **Consistent** — unified API for all validation methods.
* **Flexible** — works with any model exposing `.fit()` / `.predict()`.
* **Visual** — built-in `plot_forecast()` with datetime alignment and residuals.
* **Transparent** — every function returns clear, reproducible outputs.

---

## 🧩 Supported Methods

| Function        | Description                                        |
| --------------- | -------------------------------------------------- |
| `ts.split()`    | Single train/validation/test split                 |
| `ts.validate()` | Cross-validation (walk-forward or temporal K-Fold) |
| `ts.backtest()` | Out-of-sample testing                              |
| `ts.evaluate()` | Metric evaluation (MAE, RMSE, sMAPE, rMAE)         |

---

## 📂 Examples

Timeframes includes several runnable demonstrations for validation, backtesting, and visualization:

| Script                              | Description                                    |
| ----------------------------------- | ---------------------------------------------- |
| `examples/forecasts.py`             | Full workflow: validation + backtest + plots   |
| `examples/kfold_demo.py`            | Temporal K-Fold cross-validation               |
| `examples/visualize_splits_demo.py` | Visualize expanding, moving, and K-Fold splits |

Run any example directly:

```bash
python examples/forecasts.py
```

Or run all `__main__` demos automatically (via pytest):

```bash
pytest
```

This executes every example and internal demonstration, ensuring reproducibility across releases.

---

## 🧠 Built-in Datasets

| Name                    | Description                                   | Period    | Source                              |
| ----------------------- | --------------------------------------------- | --------- | ----------------------------------- |
| `air_passengers`        | Classic airline passenger dataset             | 1949–1960 | Public domain (Box & Jenkins, 1976) |
| `ts_components`         | Synthetic trend + seasonality decomposition   | 2000–2011 | Generated (Andrew R. Garcia, 2025)  |
| `ts_components_complex` | Nonlinear trend + multi-frequency seasonality | 2000–2011 | Generated (Andrew R. Garcia, 2025)  |

Load with:

```python
df = ts.load_example("ts_components")
```

List all available datasets:

```python
ts.list_examples()
```

---

## 📈 Visualization Example

```python
ts.plot_forecast(
    y_true, 
    y_pred, 
    title="Out-of-Sample Forecast", 
    show_residuals=True
)
```

Generates a clean, publication-ready figure with automatic datetime indexing and optional residual bars.

---

## License

MIT License © 2025 [Andrew R. Garcia](https://github.com/andrewrgarcia)
