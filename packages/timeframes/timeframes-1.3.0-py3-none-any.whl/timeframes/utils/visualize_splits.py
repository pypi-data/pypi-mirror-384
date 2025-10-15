"""
Visualization utilities for time series cross-validation splits.

Provides quick visual inspection of walk-forward or K-fold schemes.
Ideal for teaching, debugging, or including figures in reports.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Iterable, Tuple

def draw_segments(ax, x, y, color, lw=2, marker="o", ms=6, label=None):
    """Draw only consecutive segments as continuous lines."""
    if len(x) == 0:
        return
    x = np.sort(x)
    breaks = np.where(np.diff(x) > 1)[0] + 1
    segments = np.split(x, breaks)
    for seg in segments:
        if len(seg) > 1:
            ax.plot(seg, np.full_like(seg, y, dtype=float),
                    color=color, lw=lw, alpha=0.9)
        ax.scatter(seg, np.full_like(seg, y, dtype=float),
                    color=color, s=55, marker=marker,
                    edgecolor="white", linewidth=0.5,
                    label=label if label else None, zorder=3)
            

def plot_splits(
    splits: Iterable[Tuple[np.ndarray, np.ndarray]],
    n_samples: int,
    title: str = "Cross-Validation Splits",
    figsize: Tuple[int, int] = (9, 5),
    train_color: str = "#3A7DFF",
    val_color: str = "#E74C3C",
) -> None:
    """
    Plot train/validation index patterns over time with automatic line breaks
    for non-consecutive indices and a clean, single-entry legend.
    """
    splits = list(splits)
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_title(title, fontsize=13, pad=12, fontweight="bold")
    ax.set_xlabel("Time Index", fontsize=11)
    ax.set_ylabel("Split Number", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.set_xlim(-1, n_samples)
    ax.set_ylim(-1, len(splits))

    # draw all splits
    for i, (train_idx, val_idx) in enumerate(splits):
        draw_segments(ax, train_idx, i, train_color, label="Train" if i == 0 else None)
        draw_segments(ax, val_idx, i, val_color, marker="D", label="Validation" if i == 0 else None)

    # ✅ deduplicate legend entries
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), frameon=False, loc="upper right", fontsize=10)

    ax.set_yticks(range(len(splits)))
    ax.set_yticklabels([f"Step {j+1}" for j in range(len(splits))])
    ax.invert_yaxis()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    import pandas as pd
    from timeframes.validation import walkforward, kfold

    def see_splits(splits, n_samples, type="kfold", plot_title="K-Fold (shuffle=True)"):
        object = "Fold" if type=="kfold" else "Step"
        for i, (train_idx, val_idx) in enumerate(splits, 1):
            print(f"{object} {i:02d} | train={train_idx} | val={val_idx}")
        plot_splits(splits, n_samples=n_samples, title=plot_title)

    # Simulated time series
    df = pd.DataFrame(
        {"value": range(30)},
        index=pd.date_range("2023-01-01", periods=30, freq="ME")
    )
    n = len(df)

    splits = list(walkforward(n_samples=n, output_size=3, step=3, mode="expanding", min_train_size=10))
    see_splits(splits, type="walkf", n_samples=n, plot_title="Expanding Window")
    print(f"\nExpanding window: {len(splits)} splits generated")

    splits = list(walkforward(n_samples=n, window_size=12, output_size=3, step=3, mode="moving"))
    see_splits(splits, type="walkf", n_samples=n, plot_title="Moving Window")
    print(f"\nMoving window: {len(splits)} splits generated")

    print("\nK-Fold (shuffle=True, n_splits=4):")
    splitter = kfold(n_splits=4, shuffle=True, seed=0)
    splits = list(splitter.split(df))
    see_splits(splits, type="kfold", n_samples=n, plot_title="K-Fold (shuffle=True)")

    print("\nK-Fold (shuffle=False, n_splits=4):")
    splitter = kfold(n_splits=4, shuffle=False)
    splits = list(splitter.split(df))
    see_splits(splits, type="kfold", n_samples=n, plot_title="K-Fold (shuffle=False)")