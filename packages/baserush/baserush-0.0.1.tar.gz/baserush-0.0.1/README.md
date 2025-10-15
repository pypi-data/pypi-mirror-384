# baserush

![PyPI](https://img.shields.io/pypi/v/baserush)
![License](https://img.shields.io/github/license/chase-kusterer/baserush)

Stable base modeling made quick and easy.

`baserush` is an easy-to-use regression pipeline for preprocessing, optimizing, and summarizing machine learning models within the `scikit-learn` framework. This package is ideal for efficiently building and comparing **stable models** from different model types.

### Supported Model Types

<u>Linear Models</u>
 * LinearRegression
 * Lasso
 * Ridge
 * SGDRegressor

<u>Neighbors Models</u>
 * KNeighborsRegressor
 * RadiusNeighborsRegressor

<u>CaRT Models</u>
 * DecisionTreeRegressor
 * ExtraTreeRegressor

<u>Ensemble Models</u>
 * RandomForestRegressor
 * GradientBoostingRegressor
 * ExtraTreesRegressor
 * RandomTreesEmbedding


## Package Modules

- `preprocess`: missing values, skewness, standardization, and categorical transformations
- `optimize`: automatic feature selection; hyperparameter analysis
- `summary`: training and validation R-Squared, stability tools; model-specific outputs


---

## `preprocess`ing Features

- `simputer` makes it simple to flag and impute missing values.
- Quickly alleviate skewness with `transtorm`.
- Use `simple_scaler` to seamlessly standardize features.
- Efficiently prepare categorical data for modeling with `catcoder`.

## `optimize`-ation Features
- Base modeling made easy with
  - `quick_lm` (with automated feature selection)
  - `quick_tree`, (includes very fast automated hyperparameter tuning)
  - `quick_neighbors`, (automatically tunes n neighbors)

- Use `tuning_results` to analyze the top n-models after hyperparameter tuning
  with GridSeachCV | RandomizedSearchCV. 


## `summary` Features
`lr_summary`, `tree_summary`, and `knn_summary`
- Automatically instantiate customizable training and validation sets.
- Generate a dataset of model summaries for easy comparison, including:
  * Model Name
  * Model Class
  * Model Type
  * R-Squared (Training Set)
  * R-Squared (Validation Set)
  * Train-Test Gap
  * Model-Specific:
    * Model Coefficients
    * Feature Importance
    * Hyperparameter Values

---

## Installation

Install using pip:

```bash
pip install baserush
```

---

## Example Usage

```python
print("Examples coming soon.")
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.