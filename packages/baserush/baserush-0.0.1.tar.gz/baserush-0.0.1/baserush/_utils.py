# _utils.py
# Utility functions used throughout baserush.
# Author: Chase Kusterer
# Github: https://github.com/chase-kusterer
# =========================================================================== #

# imports 
from __future__ import annotations
from typing import Iterable, Optional, Sequence, Union, Dict, Any, List
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.model_selection import train_test_split, KFold
from sklearn.metrics import r2_score

# organizing functions
__all__ = ["quick_lm", "quick_tree", "quick_neighbors", "tuning_results"]

# ---------------- #
# summary.py utils #
# ---------------- #
# used in lr_summary | tree_summary | knn_summary | quick_neighbors
def _safe_round(x: Any, ndigits: int = 6) -> Any:
    """Rounds scalars/0-d arrays; return original if not roundable."""
    try:
        if isinstance(x, np.ndarray) and x.shape == ():
            return round(float(x), ndigits)
        return round(x, ndigits)
    except Exception:
        return x


# used in lr_summary | tree_summary | knn_summary
def _resolve_feature_names(
    X: ArrayLike, model: Optional[BaseEstimator] = None
) -> List[str]:
    """
    Feature name resolution:
    1) DataFrame columns,
    2) model.feature_names_in_,
    3) generic names: x0..x{n-1}
    """
    if isinstance(X, pd.DataFrame):
        return list(X.columns)

    if model is not None and hasattr(model, "feature_names_in_"):
        return [str(n) for n in getattr(model, "feature_names_in_")]

    X_arr = np.asarray(X)
    if X_arr.ndim == 1:
        n_features = 1
    elif X_arr.ndim >= 2:
        n_features = X_arr.shape[1]
    else:
        n_features = 1
    return [f"x{i}" for i in range(n_features)]


# used in lr_summary | tree_summary | knn_summary | simple_scaler | transtorm | simputer
def _ensure_df(X: ArrayLike) -> pd.DataFrame:
    """Return a DataFrame (copy=False); if already a Series/ndarray, wrap with default names."""
    try:
        if isinstance(X, pd.DataFrame):
            return X
        if isinstance(X, pd.Series):
            return X.to_frame()
        arr = np.asarray(X)
        n_rows = arr.shape[0]
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        cols = [f"x{i}" for i in range(arr.shape[1])]
        return pd.DataFrame(arr, columns=cols)

    except:
        return X if isinstance(X, pd.DataFrame) else pd.DataFrame()

# used in tree_summary | knn_summary
def _prefix_params(params: Dict[str, Any], prefix: str = "hp_") -> Dict[str, Any]:
    """Avoids key collisions with model info by prefixing hyperparameter keys."""
    return {f"{prefix}{k}": v for k, v in params.items()}


# ----------------- #
# optimize.py utils #
# ----------------- #
# used in quick_tree
def _cv_metrics_for_leaf(
    x_data: np.ndarray,
    y_data: np.ndarray,
    model_type: Optional[Callable[..., object]] = None,
    leaf: int = 200,
    cv_folds: int = 3,
    random_state: int = 702,
) -> dict:
    """
    Helper: compute CV metrics for a given min_samples_leaf value (Stage 1).
    Uses a lightweight DecisionTreeRegressor model.

    RETURNS a dict with: mean_RSS, mean_R2, RSS_range, R2_range
    """

    # Default model type == DecisionTreeRegressor
    if model_type is None:
        from sklearn.tree import DecisionTreeRegressor
        model_type = DecisionTreeRegressor

    x_data = np.asarray(x_data)
    y_data = np.asarray(y_data).ravel()

    kf = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    rss_scores = []
    r2_scores  = []

    for train_idx, val_idx in kf.split(x_data):
        model = model_type(min_samples_leaf = leaf,
                           random_state     = random_state)
        
        model.fit(x_data[train_idx], y_data[train_idx])

        y_val  = y_data[val_idx]
        y_pred = model.predict(x_data[val_idx])

        rss_scores.append(float(np.sum((y_val - y_pred) ** 2)))
        r2_scores.append(float(r2_score(y_val, y_pred)))

    return {
        "min_samples_leaf": int(leaf),
        "mean_RSS":  float(np.mean(rss_scores)),
        "mean_R2":   float(np.mean(r2_scores)),
        "RSS_range": float(np.max(rss_scores) - np.min(rss_scores)),
        "R2_range":  float(np.max(r2_scores)  - np.min(r2_scores)),
    }

# used in quick_tree
def _select_top_n_unique(
    df: pd.DataFrame,
    metric: str,
    n: int,
    asc: bool = True
) -> Iterable[int]:
    """
    Helper: select the top-n unique min_samples_leaf values by a metric.
    direction: 'lower' or 'higher'. Does NOT include ties beyond n.
    Stable secondary sort by min_samples_leaf ascending for determinism.
    """
    
    # sorting results
    ranked = df.sort_values([metric, "min_samples_leaf"],
                             ascending = asc,
                             kind      = "mergesort")

    # returning results    
    return ranked.head(n=n)


# ------------------- #
# preprocess.py utils #
# ------------------- #
# used in simple_scaler | transtorm | simputer
def _numeric_columns(df: pd.DataFrame, include: Optional[Sequence[str]] = None) -> List[str]:
    """Select numeric columns; if `include` provided, intersect with numeric set (preserve order)."""
    if include is None:
        num_cols = list(df.select_dtypes(include=["number"]).columns)
    else:
        include = list(include)
        num_cols = [c for c in include if pd.api.types.is_numeric_dtype(df[c])]
    return num_cols

# used in simple_scaler | transtorm | simputer
def _rebuild_df(
    base_df: pd.DataFrame,
    transformed: np.ndarray,
    cols: Sequence[str],
    dtype: Optional[str] = None,
) -> pd.DataFrame:
    out = base_df.copy()
    tdf = pd.DataFrame(transformed, index=base_df.index, columns=list(cols))
    if dtype is not None:
        try:
            tdf = tdf.astype(dtype)
        except Exception:
            pass
    out.loc[:, cols] = tdf
    return out