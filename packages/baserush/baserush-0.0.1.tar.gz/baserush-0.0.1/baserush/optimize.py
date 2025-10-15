# optimize.py
# Automated feature selection and hyperparamemter tuning tools.
# Author: Chase Kusterer
# Github: https://github.com/chase-kusterer
# =========================================================================== #

# imports 
from __future__ import annotations
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union, Iterable, Set
import numpy  as np                                         # numerical essentials
import pandas as pd                                         # data science essentials
import statsmodels.api as sm                                # p-values
from sklearn.model_selection import train_test_split, KFold # cross validation
from sklearn.metrics import r2_score                        # r-squared
from sklearn.tree import DecisionTreeRegressor              # decision tree regressor
import matplotlib.pyplot as plt                             # graphical essentials

# utility imports
from ._utils import _cv_metrics_for_leaf, _select_top_n_unique, _safe_round

# organizing functions
__all__ = ["quick_lm", "quick_tree", "quick_neighbors", "tuning_results"]


# ---------- public API ---------- #
## quick_lm ##
def quick_lm(
    x_data: pd.DataFrame,
    y_data: Union[pd.Series, np.ndarray, List[float]],
    force_in: list = None,
    threshold_in: float = 0.01,
    threshold_out: float = 0.05,
    max_iter: int = 100,
    verbose: bool = True,
) -> List[str]:
    """
    Builds a linear model using stepwise feature selection based on
    p-values, returning a list of optimal x-features.

    PARAMETERS
    ----------
    x_data : pandas.DataFrame
        DataFrame with candidate features.
    y_data : array-like
        The target variable.
    force_in : list
        X-feature(s) to force into the model.
    threshold_in : float
        Include a feature if its p-value < threshold_in.
    threshold_out : float
        Exclude a feature if its p-value > threshold_out.
    verbose : bool
        Whether to print the sequence of inclusions and exclusions.

    RETURNS
    -------
    list
        The list of selected features.

    Notes
    -----
    - Ensure `threshold_in < threshold_out` for stable behavior.
    - If a candidate leads to singular fits or other errors, it is treated as non-significant.
    """

    # threshold logic check
    if threshold_in >= threshold_out:
        raise ValueError("threshold_in must be strictly less than threshold_out to avoid oscillation.")

    # ensuring DataFrame structure
    if not isinstance(x_data, pd.DataFrame):
        x_data = pd.DataFrame(x_data)

    # preparing feature set
    included: List[str] = force_in if force_in is not None else []

    # setting up iteration counter
    iter_count = 0

    # looping over each x-feature until there are no more significant p-values
    while True:
        changed = False

        # interating counter
        iter_count += 1

        # message and break if iteration limit is reached
        if iter_count > max_iter:
            if verbose:
                print(f"Max iterations ({max_iter}) reached; stopping.")
            break

        # ---------------- forward step ---------------- #
        # forward step: adding an x-feature
        excluded = [col for col in x_data.columns if col not in included]
        new_pvals = pd.Series(dtype = float, index = excluded)


        # fitting model with additional candidate feature
        for new_column in excluded:

            model = sm.OLS(y_data,
                           sm.add_constant(x_data[included + [new_column]])).fit()

            new_pvals[new_column] = model.pvalues[new_column]


        if not new_pvals.empty:
            best_pval = new_pvals.min()
            if best_pval < threshold_in:
                best_feature = new_pvals.idxmin()  # Use idxmin() instead of argmin()
                included.append(best_feature)
                changed = True
                if verbose:
                    print('Add  {:30} with p-value {:.6}'.format(best_feature, best_pval))

        # ---------------- backward step ---------------- #
        # backward step: potentially removing an x-feature
        if included:
            model = sm.OLS(y_data, sm.add_constant(x_data[included])).fit()

            # excluding intercept p-value (first element)
            pvals = model.pvalues.iloc[1:]

            # ensuring the model is not empty
            if not pvals.empty:
                worst_pval = pvals.max()
                if worst_pval > threshold_out:
                    worst_feature = pvals.idxmax()  # Use idxmax() instead of argmax()
                    included.remove(worst_feature)
                    changed = True
                    if verbose:
                        print('Drop {:30} with p-value {:.6}'.format(worst_feature, worst_pval))


        # stopping the loop if optimized
        if not changed:
            break


    # returning stepwise model's x-features
    return included


## tuning_results ##
# works on any supervised model after hp_tuning
def tuning_results(
    cv_results: Union[Mapping[str, Any], Any],
    n: int = 1,
    round_digits: int = 6,
) -> pd.DataFrame:
    """
    Extracts the top-n hyperparameter tuning results from sklearn model
    selection tools (GridSearchCV or RandomizedSearchCV). Outputs an organized
    DataFrame containing:
        * Model Rank       (rank_test_score)
        * Mean Test Score  (mean_test_score)
        * StDev Test Score (std_test_score)
        * Best Parameters  (best_params)

    PARAMETERS
    ----------
    cv_results : dict or fitted search object
        Either the dictionary from `.cv_results_` or a fitted GridSearchCV /
        RandomizedSearchCV object (the function will read `.cv_results_` if
        present).
    n : int, default=1
        The number of top ranks to include. All rows with rank_test_score <= n
        are returned (i.e., ties are included).

    RETURNS
    -------
    pd.DataFrame
    """
    # allow passing the fitted search object directly
    if hasattr(cv_results, "cv_results_"):
        cv_results = cv_results.cv_results_

    # validation - ensuring dict-like object
    if not isinstance(cv_results, Mapping):
        raise TypeError("cv_results must be a dict-like object or a fitted search with .cv_results_")
    
    # validation - checking keys
    required = {"params", "rank_test_score", "mean_test_score"}
    missing = required.difference(cv_results.keys())
    if missing:
        raise KeyError(f"cv_results is missing required keys: {sorted(missing)}")
        
    
    try:
        # instantiating results DataFrame
        df = pd.DataFrame(data = cv_results)[['rank_test_score',
                                              'mean_test_score',
                                              'std_test_score' ,
                                              'params']]

    except:
        # instantiating partial results DataFrame
        df = pd.DataFrame(data = cv_results)[['rank_test_score',
                                              'mean_test_score',
                                              'params']]
        
        # avoiding issue with older/custom scorers
        if "std_test_score" not in df.columns:
            df["std_test_score"] = pd.NA
        
        
        
    # renaming columns
    df = df.rename(columns={"rank_test_score": "Model Rank",
                            "mean_test_score": "Mean Test Score",
                            "std_test_score" : "SD Test Score",
                            "params": "Parameters"})
    
    
    # clamping n and filtering by rank (include ties)
    n = max(int(n), 1)
    top = df.loc[df["Model Rank"] <= n].copy()

    # sorting (highest rank followed by lowest standard deviation
    top = top.sort_values(["Model Rank", "SD Test Score"],
                          ascending=[True, False]).reset_index(drop=True)

    # returning results
    return top


## quick_tree ##
def quick_tree(
    x_data,
    y_data: Sequence[float],
    model_type: Callable[..., object] = None,
    max_leaf_samples: int = 50,
    leaf_values: Optional[Sequence[int]] = None,
    max_depth: int = 20,
    depths: Optional[Sequence[int]] = None,
    cv_folds: int = 3,
    n: int = 5,
    random_state: int = 702,
) -> pd.DataFrame:
    """
    Quickly tunes a tree-based model using a two-stage cross-validated
    procedure. Often returns multiple trees since multiple metrics are used in
    evaluating which tree is "best".

    PARAMETERS
    ----------
    x_data            | array-like | feature matrix                               | No default
    y_data            | array-like | target vector                                | No default
    model_type        | model      | tree-based model type                        | Default = DTree (Reg)
    max_leaf_samples  | int        | largest min_samples_leaf if leaf_values None | Default = 50
    leaf_values       | seq[int]   | explicit set of min_samples_leaf candidates  | Default = None
    max_depth         | int        | largest depth tested if depths None          | Default = 20
    depths            | seq[int]   | explicit set of depths to evaluate           | Default = None
    cv_folds          | int        | number of CV folds                           | Default = 3
    n                 | int        | top-n unique per metric (no ties beyond n)   | Default = 5
    random_state      | int        | RNG seed for KFold and models                | Default = 702

    RETURNS
    -------
    DataFrame with:
      * depth
      * min_samples_leaf
      * folds
      * mean_RSS
      * mean_R2
      * RSS_range (max_RSS - min_RSS across folds)
      * R2_range  (max_R2  - min_R2  across folds)
    """
    # Default model type == DecisionTreeRegressor
    if model_type is None:
        from sklearn.tree import DecisionTreeRegressor
        model_type = DecisionTreeRegressor

    # --- Normalize inputs ---
    X = np.asarray(x_data)
    y = np.asarray(y_data).ravel()

    if leaf_values is None:
        leaf_values = range(1, max_leaf_samples + 1)
    if depths is None:
        depths = range(1, max_depth + 1)

    # =========================
    # Stage 1: tune min_samples_leaf (ALWAYS lightweight estimator)
    # =========================
    leaf_rows = []
    for leaf in leaf_values:
        metrics = _cv_metrics_for_leaf(
            X, y,
            model_type=model_type,
            leaf=leaf,
            cv_folds=cv_folds,
            random_state=random_state
        )
        leaf_rows.append(metrics)
    leaf_df = pd.DataFrame(leaf_rows)

    # Select top-n unique leafs per metric
    top_by_mean_rss = _select_top_n_unique(leaf_df, "mean_RSS",  n, asc=True)
    top_by_mean_r2  = _select_top_n_unique(leaf_df, "mean_R2",   n, asc=False)
    top_by_rss_rng  = _select_top_n_unique(leaf_df, "RSS_range", n, asc=True)
    top_by_r2_rng   = _select_top_n_unique(leaf_df, "R2_range",  n, asc=True)

    
    # concatenating results and dropping duplicates
    tuned_leaves = pd.concat(objs = [top_by_mean_rss,
                                     top_by_mean_r2,
                                     top_by_rss_rng,
                                     top_by_r2_rng],
                             axis = 0).drop_duplicates()
    
    
    # preparing leaf values
    tuned_leaf_grid = tuned_leaves['min_samples_leaf']


    # =========================
    # Stage 2: evaluate depth × tuned_leaf_grid with final model_type
    # =========================
    kf = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    rows = []

    for d in depths:
        for leaf in tuned_leaf_grid:
            rss_scores, r2_scores = [], []
            for train_idx, val_idx in kf.split(X):
                model = model_type(
                    max_depth=d,
                    min_samples_leaf=leaf,
                    random_state=random_state
                )
                model.fit(X[train_idx], y[train_idx])

                y_val  = y[val_idx]
                y_pred = model.predict(X[val_idx])

                rss_scores.append(float(np.sum((y_val - y_pred) ** 2)))
                r2_scores.append(float(r2_score(y_val, y_pred)))

            rows.append({
                "depth": int(d),
                "min_samples_leaf": int(leaf),
                "folds": cv_folds,
                "mean_RSS" : float(np.mean(rss_scores)),
                "mean_R2"  :  float(np.mean(r2_scores)),
                "RSS_range": float(np.max(rss_scores) - np.min(rss_scores)),
                "R2_range" :  float(np.max(r2_scores)  - np.min(r2_scores)),
            })

    
    # preparing DataFrame
    depth_df = pd.DataFrame(rows)
    
    # selecting the top models per metric
    top_by_mean_rss = _select_top_n_unique(depth_df, "mean_RSS",  n, asc=True)
    top_by_mean_r2  = _select_top_n_unique(depth_df, "mean_R2",   n, asc=False)
    top_by_rss_rng  = _select_top_n_unique(depth_df, "RSS_range", n, asc=True)
    top_by_r2_rng   = _select_top_n_unique(depth_df, "R2_range",  n, asc=True)
    
    # concatenating results and dropping duplicates
    tuned_depth = pd.concat(objs = [top_by_mean_rss,
                                    top_by_mean_r2 ,
                                    top_by_rss_rng ,
                                    top_by_r2_rng] ,
                            axis = 0).drop_duplicates()\
                                     .sort_values(by='mean_RSS')\
                                     .reset_index(drop=True)
    
    return tuned_depth


## quick neighbors ##
def quick_neighbors(x_data: ArrayLike,
                    y_data: ArrayLike,
                    model_type: BaseEstimator = None,
                    max_neighbors: int = 50,
                    power_p: Union[int, float] = 2,
                    threshold: float = 0.05,
                    standardize: bool = True,
                    visualize: bool = True,
                    verbose: bool = True,
                    tts: bool = True,
                    test_size: float = 0.25,
                    random_state: int = 702):    
    """
    This function optimizes the number of neighbors for the following
    algorithms, based the training and testing gap (R-Square):
        * KNeighborsRegressor
        * RadiusNeighborsRegressor

    PARAMETERS
    ----------
    x_data        | array   | X-data before train-test split  | No default.
    y_data        | array   | y-data before train-test split  | No default.
    model_type    | model   | model object to instantiate     | KNeighborsRegressor
    max_neighbors | int     | max neighbors to evaluate       | Default = 50
    power_p       | numeric | power parameter for Minkowski   | Default = 2
    threshold     | float   | tt gap threshold between (0, 1) | Default = 0.05
    standardize   | bool    | standardizes x_data (μ=0, σ²=1) | Default = True
    visualize     | bool    | renders a line graph of results | Default = True
    verbose       | bool    | prints optimal neigbors results | Default = True
    tts           | bool    | perform train_test_split        | Default = True
    test_size     | float   | test proportion (tts)           | Default = 0.25
    random_state  | int     | random seed (tts)               | Default = 702

    RETURNS
    -------
    A fitted neighbors model optimized for n neighbors.
    """
    # standardizing x_data
    if standardize == True:

        # importing simple_scaler
        from .preprocess import simple_scaler

        # applying standardization
        x_data = simple_scaler(df = x_data)

    # default model type == KNeighborsRegressor
    if model_type is None:
        from sklearn.neighbors import KNeighborsRegressor
        model_type = KNeighborsRegressor
    
    # minimizing code changes
    model = model_type
    
    # testing and validation sets
    if tts:
        X_train, X_test, y_train, y_test = train_test_split(x_data,
                                                            y_data,
                                                            test_size=test_size,
                                                            random_state=random_state)

    # full dataset
    else:
        X_train = X_test = x
        y_train = y_test = y

    # lists to store metrics
    train_rsq = []
    test_rsq  = []
    tt_gap    = []
    
    # creating range object for neighbors
    neighbors = range(max_neighbors)
    
    # calculating results
    for n_neighbors in neighbors:

        # instantiating KNN
        clf = model(n_neighbors = n_neighbors + 1,
                    p = power_p)

        # fitting to the data
        clf.fit(X_train, y_train)

        # training scores
        train_rsq.append(clf.score(X_train, y_train))

        # testing scores
        test_rsq.append(clf.score(X_test, y_test))

        # train-test gap
        tt_gap.append(abs(clf.score(X_train, y_train) - clf.score(X_test, y_test)))

    # visualizing results
    if visualize == True:
        fig, ax = plt.subplots(figsize=(12,8))
        plt.plot(neighbors, train_rsq, label = "R-Square (Training Set)")
        plt.plot(neighbors, test_rsq,  label = "R-Square (Testing Set)")
        plt.ylabel(ylabel = "Coefficient of Determination")
        plt.xlabel(xlabel = "Number of Neighbors")
        plt.legend()
        plt.show()

    # gap test
    gap_pass = [i for i, x in enumerate(tt_gap) if x <= threshold]

    # stable results
    test_pass = [test_rsq[i] for i in gap_pass]

    # finding the optimal number of neighbors
    opt_neighbors = test_rsq.index(max(test_pass)) + 1
    
    # pringint results
    if verbose == True:
        print(f"""
    The optimal number of neighbors is {opt_neighbors}.
    Training R-Square: {_safe_round(train_rsq[opt_neighbors - 1], 4)}
    Testing  R-Square: {_safe_round(test_rsq[opt_neighbors  - 1], 4)}
    Train-Test Gap:    {_safe_round(tt_gap[opt_neighbors    - 1], 4)}
""")
    
    # returning fitted model
    return clf