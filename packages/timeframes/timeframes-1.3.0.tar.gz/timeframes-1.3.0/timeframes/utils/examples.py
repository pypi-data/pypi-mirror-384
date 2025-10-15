"""
Example datasets bundled with Timeframes.
All datasets are public domain (educational use).
"""

import pandas as pd
from importlib.resources import files
import numpy as np

def load_example(name: str = "air_passengers") -> pd.DataFrame:
    """
    Load an example dataset by name.

    Parameters
    ----------
    name : str
        Dataset name, e.g. "air_passengers".

    Returns
    -------
    pandas.DataFrame
        The requested dataset as a DataFrame.

    Example
    -------
    >>> import timeframes as ts
    >>> df = ts.load_example("air_passengers")
    >>> df.head()
         Month  AirPassengers
    0  1949-01         112
    1  1949-02         118
    2  1949-03         132
    3  1949-04         129
    4  1949-05         121
    """
    name = name.lower()

    if name == "air_passengers":
        data_path = files("timeframes.utils.data") / "air_passengers.csv"
        # Read Month as DatetimeIndex, keep only one column
        df = pd.read_csv(
            data_path,
            index_col=0,           # use Month as index
            parse_dates=True,      # auto-convert to datetime
        )
        df.index.name = "Month"
        df.columns = ["AirPassengers"]  # enforce clean column name
        return df


    elif name == "ts_components":
        return _generate_ts_decomposition()

    elif name == "ts_components_complex":
        return _generate_ts_decomposition(complex=True)
    

    raise ValueError(f"Unknown example dataset: {name}")


def _generate_ts_decomposition(N: int = 120, complex: bool = False, seed: int = 42):
    """Generate a synthetic time series with smooth nonlinear trend, composite seasonality, and white noise."""

    if complex:
        t = np.linspace(0, 1, N)
        trend = -4 * (t ** 2.5) + 0.5 * t                                                          # Nonlinear trend (soft polynomial curve)
        seasonal = np.sin(2 * np.pi * 3 * t) + 0.3 * np.sin(2 * np.pi * 9 * t + np.pi / 4)          # Multi-frequency seasonality (slight beat pattern)
        date_range = pd.date_range("2012-01", periods=N, freq="ME")

    else:
        trend = np.linspace(0, 6, N)
        seasonal = np.sin(np.linspace(0, 10 * np.pi, N))
        date_range = pd.date_range("2000-01", periods=N, freq="ME")

    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 0.25,N)

    # Combine components
    df = pd.DataFrame({
        "Trend": trend,
        "Seasonal": seasonal,
        "Composite": trend + seasonal + noise
    }, index=date_range)

    df.index.name = "Month"
    return df


def list_examples(show: bool = True):
    """
    List all available example datasets in Timeframes.
    """
    examples = [
        {
            "name": "air_passengers",
            "title": "AirPassengers",
            "rows": 144,
            "columns": 1,
            "period": "1949-1960",
            "source": "Public domain (Box & Jenkins, 1976)"
        },
        {
            "name": "ts_components",
            "title": "TS Decomposition (Simple)",
            "rows": 144,
            "columns": 3,
            "period": "2000-2011",
            "source": "Generated (Andrew R. Garcia, 2025)"
        },

        {
            "name": "ts_components_complex",
            "title": "TS Decomposition (Complex)",
            "rows": 144,
            "columns": 3,
            "period": "2000-2011",
            "source": "Generated (Andrew R. Garcia, 2025)"
        },

    ]
    df = pd.DataFrame(examples)
    if show:
        print(df)
    else:
        return df



if __name__ == "__main__":
    import matplotlib.pyplot as plt

    list_examples()

    plt.style.use("seaborn-v0_8-whitegrid")

    # Load both datasets
    air = load_example("air_passengers")
    tsd = load_example("ts_components")
    tsc = load_example("ts_components_complex")

    # --- Plot 1: AirPassengers ---
    fig, ax = plt.subplots(3, 1, figsize=(10, 8), sharex=False)
    air.plot(ax=ax[0], legend=False, color="steelblue")
    ax[0].set_title("AirPassengers Dataset (1949-1960)")
    ax[0].set_ylabel("Passengers (thousands)")

    # --- Plot 2: TS Decomposition ---
    tsd.plot(ax=ax[1])
    ax[1].set_title("TS Simple Decomposition (Trend + Seasonality + Noise)")
    ax[1].set_ylabel("Value")
    ax[1].legend(loc="upper left")

    # --- Plot 3: TS Decomposition but complex ---
    tsc.plot(ax=ax[2])
    ax[2].set_title("TS Complex Decomposition (Trend + Seasonality + Noise)")
    ax[2].set_ylabel("Value")
    ax[2].legend(loc="upper left")


    plt.tight_layout()
    plt.show()

    # Summary info
    print("\n✅ Loaded datasets:")

    print(f"- AirPassengers: {air.shape[0]} points ({air.index.min().date()} → {air.index.max().date()})")
    print(f"- TS Decomposition: {tsd.shape[0]} points ({tsd.index.min().date()} → {tsd.index.max().date()})\n")
