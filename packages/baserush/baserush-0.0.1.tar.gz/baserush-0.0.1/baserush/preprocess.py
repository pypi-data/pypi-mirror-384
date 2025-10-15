# preprocess.py
# Utilities to impute, transform, scale, and encode features for scikit-learn workflows.
# Author: Chase Kusterer
# Github: https://github.com/chase-kusterer
# =========================================================================== #

# imports 
from __future__ import annotations
from typing import Iterable, Optional, Sequence, Union, Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, PowerTransformer, OneHotEncoder
from sklearn.impute import SimpleImputer

# utility imports
from ._utils import _ensure_df, _numeric_columns, _rebuild_df

# organizing data types
ArrayLike = Union[pd.DataFrame, pd.Series, np.ndarray, List[float], List[List[float]]]

# organizing functions
__all__ = ["simple_scaler", "transtorm", "simputer", "catcoder"]


# -------------------- public API --------------------

## simple_scaler ##
def simple_scaler(
    df: ArrayLike,
    include: Optional[Sequence[str]] = None,
    with_mean: bool = True,
    with_std: bool = True,
    copy: bool = True,
    return_scaler: bool = False,
) -> Union[pd.DataFrame, Tuple[pd.DataFrame, StandardScaler]]:
    """
    Standardizes a dataset (μ = 0, σ² = 1).
    Requires sklearn.preprocessing.StandardScaler()
    
    PARAMETERS
    ----------
    df            | DataFrame  | data to be used for scaling  | No default.
    include       | list-like  | features to scale            | Default = None
    with_mean     | bool       | scale w/ feature means       | Default = True
    with_std      | bool       | scale w/ standard deviations | Default = True
    copy          | bool       | features to scale            | Default = True
    return_scaler | bool       | returns fitted scaler object | Default = False

    RETURNS
    -------
    DataFrame (and optionally fitted scaler object)
    """
    # ensuring DataFrame structure
    X = _ensure_df(df)

    # selecting features to scale
    cols = _numeric_columns(X, include)

    if not cols:
        return (X.copy(), None) if return_scaler else X.copy()

    # instantiating scaler object
    scaler = StandardScaler(with_mean=with_mean, with_std=with_std, copy=copy)

    # scaling
    x_scaled = scaler.fit_transform(X[cols])

    # storing results
    scaled_df = _rebuild_df(X, x_scaled, cols)

    # returning results and optionally fitted scaler
    return (scaled_df, scaler) if return_scaler else scaled_df


## transtorm ##
def transtorm(
    df: ArrayLike,
    include: Optional[Sequence[str]] = None,
    verbose: bool = True,
    standardize: bool = True,
    return_transformer: bool = False,
) -> Union[pd.DataFrame, Tuple[pd.DataFrame, PowerTransformer]]:
    """
    Performs a Yeo-Johnson transformation on numeric features to reduce
    skewness.

    PARAMETERS
    ----------
    df            | DataFrame | data to be transformed       | No default.
    include       | list-like | features to transform        | Default = None
    verbose       | bool      | print a summary of results   | Default = False
    standardize   | bool      | standardizes each feature    | Default = True
    return_transformer | bool | returns fitted scaler object | Default = False

    RETURNS
    -------
    DataFrame (and optionally fitted transformer object)
    """
    # ensuring DataFrame structure
    X = _ensure_df(df)

    # selecting features to transform
    cols = _numeric_columns(X, include)

    if not cols:
        return (X.copy(), PowerTransformer(method="yeo-johnson", standardize=standardize)) if return_transformer else X.copy()

    # instantiating transformer object
    pt = PowerTransformer(method="yeo-johnson", standardize=standardize)

    # transforming
    transformed = pt.fit_transform(X[cols])

    # storing results
    transformed_df = _rebuild_df(X, transformed, cols)

    # optionally providing summary of results
    if verbose:
        before = X[cols].skew().abs().round(decimals=2)
        after  = transformed_df[cols].skew().abs().round(decimals=2)
        improvement = (before - after).rename("Δ|skew|")
        print("Normality Improvements (Skewness)\n---------------------------------\n" + improvement.to_string())

    # returning results and optionally fitted transformer
    return (transformed_df, pt) if return_transformer else transformed_df


## simputer ##
def simputer(
    df: ArrayLike,
    include: Optional[Sequence[str]] = None,
    strategy: str = "mean",
    fill_value: Optional[Any] = None,
    add_indicator: bool = False,
    return_imputer: bool = False,
) -> Union[pd.DataFrame, Tuple[pd.DataFrame, SimpleImputer]]:
    """
    Imputes missing values on numeric columns (default: mean). Strategies
    include: 'mean'|'median'|'most_frequent'|'constant'.

    PARAMETERS
    ----------
    df             | DataFrame | data to be imputed            | No default.
    include        | list-like | features to impute            | Default = None
    strategy       | str       | imputation strategy to apply  | Default = "mean"
    fill_value     | numeric   | fill for strategy='constant'  | Default = None
    flag_feature   | bool      | binary flag identifying an    | Default = False
                   |           | originally missing value      |
    return_imputer | bool      | returns fitted imputer object | Default = False

    RETURNS
    -------
    DataFrame (and optionally fitted imputer object)
    """
    # ensuring DataFrame structure
    X = _ensure_df(df)

    # selecting features to impute
    cols = _numeric_columns(X, include)

    if not cols:
        imp = SimpleImputer(strategy=strategy, fill_value=fill_value, add_indicator=add_indicator)
        return (X.copy(), imp.fit(np.empty((len(X), 0)))) if return_imputer else X.copy()

    # instantiating imputer object
    imp = SimpleImputer(strategy=strategy, fill_value=fill_value, add_indicator=add_indicator)

    # imputing
    transformed = imp.fit_transform(X[cols])

    if add_indicator and hasattr(imp, "indicator_") and imp.indicator_ is not None:

        # building feature names for indicators
        ind_names = [f"m_{c}" for c in cols]

        # when indicators present, contains [imputed_values | indicators]
        n_vals = len(cols)
        vals   = transformed[:, :n_vals]
        inds   = transformed[:, n_vals:]
        out    = _rebuild_df(X, vals, cols)
        ind_df = pd.DataFrame(data=inds, index=X.index, columns=ind_names).astype(int)
        out    = pd.concat(objs=[out, ind_df], axis=1)

    else:
        out = _rebuild_df(X, transformed, cols)

    # returning results and optionally fitted imputer
    return (out, imp) if return_imputer else out


## catcoder ##
def catcoder(data: ArrayLike,
             min_samples: int = 100,
             drop_most:   bool = False
) -> pd.DataFrame:
    """
    Encodes categorical features for use in machine learning models.
    
    PARAMETERS
    ----------
    data          | DF|Series | feature(s) to be categorically encoded  | No default.
    min_samples   | numeric   | minimum samples required for each new   | Default = 100
                              | categorical feature.                    |
    drop_most     | bool      | drops most frequent categorical feature | Default = False
    
    RETURNS
    -------
    A DataFrame containing categorically-encoded features.
    """
    # ensuring DataFrame (accepts Series or 1D array-like)
    if isinstance(data, pd.Series):
        data = data.to_frame(name=data.name if data.name is not None else "feature")
    elif not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)

    # placeholder for mulitple one-hot encodings
    one_hot_lst = []

    # looping over each categorical feature
    for feature in pd.DataFrame(data=data):

        # counts per category
        cat_count = data[feature].value_counts().rename("count").to_frame()

        # placeholder lists
        infrequent_lst = []
        category_lst   = []

        # checking data sizes
        for index, row in cat_count.iterrows():

            # excluding NaNs
            if pd.isna(index):
                continue

            # sparse categories
            if cat_count.loc[index, "count"] < min_samples:

                # appending for later
                infrequent_lst.append(index)
                
            # non-sparse categories
            else:
                category_lst.append(index)

        # one hot encoding (prefix with feature)
        one_hot_df = pd.get_dummies(data[feature],
                                    prefix   = feature,
                                    dtype    = int,
                                    dummy_na = False)

        # mapping category names to dummy column names
        infreq_cols = [f"{feature}_{val}" for val in infrequent_lst]
        

        # instantiating "Other" column if pooled infrequent bucket has enough samples
        infrequent_cnt = cat_count.loc[infrequent_lst, "count"].sum() if infrequent_lst else 0
        
        # if enough sparse samples
        if infrequent_lst and infrequent_cnt >= min_samples:

            # placeholder column (vectorized)
            other_col = f"{feature}__Other"
            one_hot_df[other_col] = (one_hot_df[infreq_cols].sum(axis=1) > 0).astype(int)

        # dropping sparse categories
        one_hot_df.drop(labels  = infreq_cols,
                        axis    = 1,
                        inplace = True,
                        errors  = "ignore")

        ## dropping options ##
        if drop_most and one_hot_df.shape[1] > 0:

            # most frequent column (within this feature block)
            mfc = one_hot_df.sum().sort_values(ascending=False).index[0]
            one_hot_df.drop(labels  = mfc,
                            axis    = 1,
                            inplace = True,
                            errors  = "ignore")

        # collecting encoded block
        one_hot_lst.append(one_hot_df)

    # returning one-hot encoded data
    return (pd.concat(one_hot_lst, axis = 1)
            if one_hot_lst
            else pd.DataFrame(index=data.index))