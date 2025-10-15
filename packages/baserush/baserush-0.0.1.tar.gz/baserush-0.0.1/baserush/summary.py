# summary.py
# Linear, tree-based, and neighbors-based regression model summaries.
# Author: Chase Kusterer
# Github: https://github.com/chase-kusterer
# =========================================================================== #

# imports
from __future__ import annotations
from typing import Iterable, Optional, Sequence, Union, Dict, Any, List
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.model_selection import train_test_split

# utility imports
from ._utils import _safe_round, _resolve_feature_names, _ensure_df, _prefix_params

# organizing data types
ArrayLike = Union[pd.DataFrame, pd.Series, np.ndarray, List[float], List[List[float]]]

# organizing functions
__all__ = ["lr_summary", "tree_summary", "knn_summary"]


# ---------- public API ---------- #
## lr_summary ##
def lr_summary(
    x: ArrayLike,
    y: ArrayLike,
    model: BaseEstimator,
    model_name: str = "",
    results_df: Optional[pd.DataFrame] = None,
    starter: Optional[Dict[str, Any]] = None,
    f_names: Optional[Sequence[str]] = None,
    tts: bool = True,
    test_size: float = 0.25,
    random_state: int = 702,
) -> pd.DataFrame:
    """ 
    This function is designed validate and summarize the following linear
    models from scikit-learn:
        * LinearRegression - OLS regression
        * Lasso            - Lasso regression
        * Ridge            - Ridge regression
        * SGDRegressor     - Stochastic Gradient Descent
        
    This function will:
    1) Split the data into training and validation sets (optional).
    2) Fit a model type to the training data.
    3) Calculate R-Square for the training and validation sets, as well as
       the train-test gap and model coefficients.
    4) Retrun the results as a DataFrame.

    Note: For models with multiple target features, only the first target's
    coefficients will be stored.
    
    PARAMETERS
    ----------
    x            | array     | X-data before train-test split    | No default.
    y            | array     | y-data before train-test split    | No default.
    model        | model     | model object to instantiate       | No default.
    model_name   | str       | model name (recommended)          | Default = ""
    results_df   | DataFrame | optional results df               | Default = None
    starter      | dict      | columns to include/override       | Default = None
    f_names      | list      | full feature names for all x-sets | Default = None
    tts          | bool      | perform train_test_split          | Default = True
    test_size    | float     | test proportion (tts)             | Default = 0.25
    random_state | int       | seed (tts)                        | Default = 702
    
    RETURNS
    -------
    A DataFrame with one row per call; will concatenate over multiple calls.
    """
    # ensuring DataFrame structure
    results_df = _ensure_df(results_df)

    # testing and validation sets
    if tts:
        X_train, X_test, y_train, y_test = train_test_split(x,
                                                            y,
                                                            test_size=test_size,
                                                            random_state=random_state)

    # full dataset
    else:
        X_train = X_test = x
        y_train = y_test = y

    # fitting to training data
    model_fit = model.fit(X_train, y_train)

    # calculating R-Square values
    train_score = _safe_round(model.score(X_train, y_train), 4)

    # results in testing and validation sets are present
    if tts:
        test_score = _safe_round(model.score(X_test, y_test), 4)
        gap = _safe_round(abs(train_score - test_score), 4)

    # results if model was run on full dataset
    else:
        test_score = None
        gap = None

    # feature schema
    feature_names = _resolve_feature_names(X_train, model)
    schema_features = list(f_names) if f_names is not None else feature_names

    row = {
            "Model_Name":  '',
            "Model_Class": '',
            "Model_Type":  '',
            "train_RSQ":   0.0,
            "test_RSQ":    0.0,
            "tt_gap":      0.0,
            "used_tts":    False,
          }

    row.update(
        {
            "Model_Name" : model_name,
            "Model_Class": model.__class__.__module__,
            "Model_Type" : model.__class__.__name__,
            "train_RSQ"  : train_score,
            "test_RSQ"   : test_score,
            "tt_gap"     : gap,
            "used_tts"   : tts,
        }
    )

    # model intercept
    if hasattr(model, "intercept_"):
        intercept = getattr(model, "intercept_")
        if isinstance(intercept, (list, np.ndarray)):
            try:
                intercept = float(np.array(intercept).reshape(-1)[0])
            except Exception:
                pass
        row["Intercept"] = _safe_round(intercept, 6)

    # instantiating model result labels
    for f in schema_features:
        row[f] = 0.0

    # model cefficients
    if hasattr(model, "coef_"):
        coefs = np.asarray(getattr(model, "coef_"))

        # multi-target: using first target's coefs to keep the row 1D
        if coefs.ndim > 1:
            coefs = coefs[0]

        # mapping names to coefficients
        for name, coef in zip(feature_names, coefs):

            if name in row:
                try:
                    row[name] = _safe_round(float(coef), 6)
                except Exception:
                    pass

    # instantiating columns to override/add
    if starter:
        row.update(starter)

    # preparing results
    results_row = pd.DataFrame(data=[row])

    # concatenating to results_df
    if not results_df.empty:
        results_df = pd.concat(objs=[results_df, results_row], axis=0, ignore_index=True)

    else:
        results_df = results_row

    # returning results
    return results_df



## tree_summary ##
def tree_summary(
    x: ArrayLike,
    y: ArrayLike,
    model: BaseEstimator,
    model_name: str = "",
    results_df: Optional[pd.DataFrame] = None,
    f_names: Optional[Sequence[str]] = None,
    tree_params: bool = True,
    tts: bool = True,
    test_size: float = 0.25,
    random_state: int = 702,
) -> pd.DataFrame:
    """
    This function is designed validate and summarize the following tree-based
    models from scikit-learn:
    
    sklearn.tree
        * DecisionTreeRegressor - A decision tree regressor.
        * ExtraTreeRegressor    - An extremely randomized tree regressor.

    sklearn.ensemble
        * RandomForestRegressor     - A random forest regressor.
        * GradientBoostingRegressor - Gradient Boosting for regression.
        * ExtraTreesRegressor       - An extra-trees regressor.
        * RandomTreesEmbedding      - An ensemble of totally random trees.
        
    This function will:
    1) Split the data into training and validation sets (optional).
    2) Fit a model type to the training data.
    3) Calculate R-Square for the training and validation sets, as well as
       the train-test gap and feature importances.
    4) Provide hyperparameter values (optional)
    5) Retrun the results as a DataFrame.

    PARAMETERS
    ----------
    x            | array     | X-data before train-test split     | No default.
    y            | array     | y-data before train-test split     | No default.
    model        | model     | model object to instantiate        | No default.
    model_name   | str       | model name (recommended)           | Default = ""
    results_df   | DataFrame | optional results df                | Default = None
    f_names      | list      | full feature names for all x-sets  | Default = None
    tree_params  | bool      | include hyperparameters in results | Default = True
    tts          | bool      | perform train_test_split           | Default = True
    test_size    | float     | test proportion (tts)              | Default = 0.25
    random_state | int       | seed (tts)                         | Default = 702
        
    RETURNS
    -------
    A DataFrame with one row per call; will concatenate over multiple calls.
    """
    # ensuring DataFrame structure
    results_df = _ensure_df(results_df)

    # testing and validation sets
    if tts:
        X_train, X_test, y_train, y_test = train_test_split(
            x, y, test_size=test_size, random_state=random_state
        )

    # full dataset
    else:
        X_train = X_test = x
        y_train = y_test = y

    # fitting to training data
    model_fit = model.fit(X_train, y_train)

    # calculating R-Square values
    train_score = _safe_round(model.score(X_train, y_train), 4)

    # results in testing and validation sets are present
    if tts:
        test_score = _safe_round(model.score(X_test, y_test), 4)
        gap = _safe_round(abs(train_score - test_score), 4)

    # results if model was run on full dataset
    else:
        test_score = None
        gap = None

    # feature schema
    feature_names = _resolve_feature_names(X_train, model)
    schema_features = list(f_names) if f_names is not None else feature_names

    row = {
            "Model_Name":  '',
            "Model_Class": '',
            "Model_Type":  '',
            "train_RSQ":   0.0,
            "test_RSQ":    0.0,
            "tt_gap":      0.0,
            "used_tts":    False,
          }

    # instantiating model result labels
    row.update(
        {
            "Model_Name": model_name,
            "Model_Class": model.__class__.__module__,
            "Model_Type": model.__class__.__name__,
            "train_RSQ": train_score,
            "test_RSQ": test_score,
            "tt_gap": gap,
            "used_tts": tts,
        }
    )

    # hyperparameters (prefixed)
    if tree_params and hasattr(model, "get_params"):
        row.update(_prefix_params(model.get_params()))


    for f in schema_features:
        row[f] = 0.0

    # feature importances
    if hasattr(model, "feature_importances_"):
        importances = np.asarray(getattr(model, "feature_importances_"))
        for name, imp in zip(feature_names, importances):
            if name in row:
                try:
                    row[name] = _safe_round(float(imp), 6)
                except Exception:
                    pass

    # preparing results
    results_row = pd.DataFrame(data=[row])

    # concatenating to results_df
    if not results_df.empty:
        results_df = pd.concat(objs=[results_df, results_row], axis=0, ignore_index=True)

    else:
        results_df = results_row

    # returning results
    return results_df


## knn_summary ##
def knn_summary(
    x: ArrayLike,
    y: ArrayLike,
    model: BaseEstimator,
    model_name: str = "",
    results_df: Optional[pd.DataFrame] = None,
    f_names: Optional[Sequence[str]] = None,
    tts: bool = True,
    test_size: float = 0.25,
    random_state: int = 702,
    include_params: bool = True,
) -> pd.DataFrame:
    """
    This function is designed to validate and summarize the following KNN-based
    models from scikit-learn:

    sklearn.neighbors
        * KNeighborsRegressor - K-Nearest Neighbors regressor.
        * RadiusNeighborsRegressor - Regression based on neighbors within a fixed radius.

    This function will:
    1) Split the data into training and validation sets (optional).
    2) Fit a KNN model to the training data.
    3) Calculate R-Square for the training and validation sets, as well as
       the train-test gap.
    4) Provide hyperparameter values (optional).
    5) Return the results as a DataFrame.

    PARAMETERS
    ----------
    x             | array     | X-data before train-test split     | No default.
    y             | array     | y-data before train-test split     | No default.
    model         | model     | model object to instantiate        | No default.
    model_name    | str       | model name (recommended)           | Default = ""
    results_df    | DataFrame | optional results df                | Default = None
    f_names       | list      | full feature names for all x-sets  | Default = None
    tts           | bool      | perform train_test_split           | Default = True
    test_size     | float     | test proportion (tts)              | Default = 0.25
    random_state  | int       | seed (tts)                         | Default = 702
    include_params| bool      | include hyperparameters in results | Default = True

    RETURNS
    -------
    A DataFrame with one row per call; will concatenate over multiple calls.
    """
    # ensuring DataFrame structure
    results_df = _ensure_df(results_df)

    # testing and validation sets
    if tts:
        X_train, X_test, y_train, y_test = train_test_split(
            x, y, test_size=test_size, random_state=random_state
        )

    # full dataset
    else:
        X_train = X_test = x
        y_train = y_test = y

    # fitting to training data
    model_fit = model.fit(X_train, y_train)

    # calculating R-Square values
    train_score = _safe_round(model.score(X_train, y_train), 4)

    # results in testing and validation sets are present
    if tts:
        test_score = _safe_round(model.score(X_test, y_test), 4)
        gap = _safe_round(abs(train_score - test_score), 4)

    # results if model was run on full dataset
    else:
        test_score = None
        gap = None

    # feature schema
    feature_names = _resolve_feature_names(X_train, model)
    schema_features = list(f_names) if f_names is not None else feature_names

    row = {
            "Model_Name":  '',
            "Model_Class": '',
            "Model_Type":  '',
            "train_RSQ":   0.0,
            "test_RSQ":    0.0,
            "tt_gap":      0.0,
            "used_tts":    False,
          }

    # instantiating model result labels
    row.update(
        {
            "Model_Name": model_name,
            "Model_Class": model.__class__.__module__,
            "Model_Type": model.__class__.__name__,
            "train_RSQ": train_score,
            "test_RSQ": test_score,
            "tt_gap": gap,
            "used_tts": tts,
        }
    )

    # hyperparameters (prefixed)
    if include_params and hasattr(model, "get_params"):
        row.update(_prefix_params(model.get_params()))

    # preparing results
    results_row = pd.DataFrame(data=[row])

    # concatenating to results_df
    if not results_df.empty:
        results_df = pd.concat(objs=[results_df, results_row], axis=0, ignore_index=True)

    else:
        results_df = results_row

    # returning results
    return results_df
