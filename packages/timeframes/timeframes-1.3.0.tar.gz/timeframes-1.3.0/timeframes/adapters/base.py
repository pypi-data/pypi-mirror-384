"""
ModelAdapter — universal fit/predict wrapper for any model.

Default assumes Scikit-learn .fit/.predict.
You can pass any custom methods (e.g. .read/.write).
"""

import numpy as np
import pandas as pd

class ModelAdapter:
    def __init__(self, model, fit_fn=None, predict_fn=None):
        self.model = model
        self.fit_fn = fit_fn or getattr(model, "fit", None)
        self.predict_fn = predict_fn or getattr(model, "predict", None)

        if not callable(self.fit_fn) or not callable(self.predict_fn):
            raise ValueError(
                f"ModelAdapter requires callable fit/predict methods. "
                f"Got fit={self.fit_fn}, predict={self.predict_fn}"
            )

    def fit(self, X, y):
        return self.fit_fn(X, y)

    def predict(self, X):
        return self.predict_fn(X)


if __name__ == "__main__":
    """
    Demonstration of ModelAdapter with a custom model using .read() and .write().
    Predicts 'Composite' from ['Trend', 'Seasonal', 'Composite'] (multivariate).
    """

    from timeframes.utils.examples import load_example
    from timeframes.validation.split import split
    from timeframes.prep import make_windowed_dataset

    # === Load dataset ===
    df = load_example("ts_components")
    print(df.head(), "\n")

    # --- Split ---
    train, val, test = split(df, ratios=(0.7, 0.2, 0.1))

    # --- Prepare windowed dataset ---
    X, y, idx = make_windowed_dataset(
        train,
        target_col="Composite",
        selected_cols=["Trend", "Seasonal", "Composite"],
        input_size=6,
        output_size=1,
        return_index=True,
    )
    X = X.reshape(len(X), -1)  # flatten for simplicity
    print(f"X shape: {X.shape}, y shape: {y.shape}")


    class EchoSynth:
        """
        The EchoSynth is a minimalist linear learner that 'reads' signals
        (absorbs patterns) and 'writes' echoes (projects predictions).
        It performs a simple least-squares mapping between input features
        and the target column.
        """

        def __init__(self):
            self.coef_ = None
            self.intercept_ = None

        def read(self, X, y):
            """Absorb data and form an echo response via least squares."""
            print("🔊 EchoSynth is reading signals (fitting linear mapping)...")
            X_ = np.hstack([X, np.ones((X.shape[0], 1))])
            w, *_ = np.linalg.lstsq(X_, y, rcond=None)
            self.coef_ = w[:-1]
            self.intercept_ = w[-1]
            print(f"🎛️ Learned {len(self.coef_)} coefficients and an intercept.")

        def write(self, X):
            """Emit predictions — the system's projected echo."""
            print("🎶 EchoSynth is writing echoes (predicting outputs)...")
            return X.dot(self.coef_) + self.intercept_

    # --- Wrap it with adapter ---
    rw_model = EchoSynth()
    adapter = ModelAdapter(rw_model, fit_fn=rw_model.read, predict_fn=rw_model.write)

    # --- Train and predict ---
    adapter.fit(X, y)
    preds = adapter.predict(X)

    # --- Display example output ---
    result = pd.DataFrame({
        "True": y.flatten(),
        "Pred": preds.flatten()
    }, index=idx)
    print("\n✅ Predictions (first 5 rows):")
    print(result.head())
