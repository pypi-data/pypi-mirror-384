"""general function to help with modelling (feature selection, ixs,
dimensionality reduction
"""

from collections import OrderedDict

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, pearsonr, rankdata
from sklearn.decomposition import TruncatedSVD
from sklearn.model_selection._search import GridSearchCV

# pylint: disable=invalid-name
# pylint: disable=missing-docstring


def get_time_series_cv_ixs(date, folds=10, start=0.5, stop=1):
    """
    The only way to do legit non-snoopy cross-fold validation - out-of-sample
    examples are always in the future.
    """
    if isinstance(start, float):
        assert (0 <= start) and (start <= 1)
        assert (start <= stop) and (stop <= 1)
    else:
        start_cutoff = np.array([start], dtype=date[0].dtype)
        stop_cutoff = np.array([stop], dtype=date[0].dtype)
        start = np.mean(date < start_cutoff)
        stop = np.mean(date < stop_cutoff)
    return _get_time_series_cv_ixs(date, folds, start, stop)


def _get_time_series_cv_ixs(date, folds, start, stop):
    assert np.all(date == sorted(date)), "df must be in chronological order"

    ixs = OrderedDict()
    chunk_size = (stop - start) / folds

    N = np.arange(len(date))
    for fold in range(folds):
        ix0 = int(np.percentile(N, (start + chunk_size * fold)) * 100)
        ix1 = int(np.percentile(N, (start + chunk_size * (fold + 1)) * 100))

        start_date = date[ix0]
        end_date = date[ix1]
        assert start_date < end_date, "end_date must be after start date"

        train_ix = date <= start_date
        test_ix = (date > start_date) & (date <= end_date)
        assert (
            train_ix.astype("float") + test_ix.astype("float")
        ).max() < 2, "There cannot be overlap between test and train ix"

        ixs[fold] = {"train": train_ix, "val": test_ix}
    return ixs


def apply_svd(df, test=None, n_components=20, n_iter=5):
    svd = TruncatedSVD(n_components=n_components, n_iter=n_iter, random_state=1)
    svd.fit(df)
    train = pd.DataFrame(svd.transform(df))
    if isinstance(test, pd.DataFrame):
        return train, pd.DataFrame(svd.transform(test))

    return train


def ks_feat_selection(
    train, test, threshold=0.05, return_pvals=False, alternative="two-sided"
):
    """the 2 samples are assumed to be continuos
    p-value is high,
    then we cannot reject the hypothesis that the distributions of the
    two samples are the same.
    so, high p-value = feature good
    """
    pcol = []
    pval = []
    for col in train.columns:
        pcol.append(col)
        ks_result = ks_2samp(train[col].values, test[col].values)
        pval.append(abs(ks_result.pvalue))
    ixs = np.array(pval) > threshold
    selected_feats = np.array(pcol)[ixs]
    if return_pvals:
        return selected_feats, pval
    return selected_feats


def pearsonr_feat_selection(df, target, threshold=0.05, return_pvals=False):
    pcol = []
    pcor = []
    pval = []
    for col in df.columns:
        pcol.append(col)
        pearsonr_result = pearsonr(df[col].values, target.values)
        pcor.append(abs(pearsonr_result[0]))
        pval.append(abs(pearsonr_result[1]))
    selected_feats = np.array(pcol)[np.array(pval) < threshold]
    if return_pvals:
        return selected_feats, pval
    return selected_feats


def get_consecutive_fold_ixs(df, n_fold=6):
    """obtain consequtive fold ixs. They have to divide exactly by n
    used by earthquake competition
    """
    n = len(df)
    result = []
    fold_length = int(n / n_fold)
    for i in range(n_fold):
        fold = i + 1
        val_ixs = np.array(range(int(i * fold_length), int(fold_length) * fold))
        train_ixs = np.array(list(set(range(0, n)) - set(val_ixs)))
        assert len(val_ixs) == fold_length
        assert len(train_ixs) == fold_length * (n_fold - 1)
        result.append([fold, (train_ixs, val_ixs)])
    return result


def get_id_fold_ixs(ids, n_fold=5, seed=None):
    if seed:
        np.random.seed(seed)
    result = []
    df = pd.DataFrame({"ids": ids})
    df_unique = pd.DataFrame({"ids": np.unique(ids)})
    df_unique["fold_id"] = np.random.randint(0, n_fold, len(df_unique))
    df = df.merge(df_unique, on="ids", how="inner")
    for i in range(n_fold):
        val_ixs = np.where(df["fold_id"] == i)[0]
        train_ixs = np.where(df["fold_id"] != i)[0]
        result.append([train_ixs, val_ixs])
    return result


def ensemble_predictions(predictions, weights, type_="linear"):
    assert np.isclose(np.sum(weights), 1.0)
    if type_ == "linear":
        res = np.average(predictions, weights=weights, axis=0)
    elif type_ == "harmonic":
        res = np.average([1 / p for p in predictions], weights=weights, axis=0)
        return 1 / res
    elif type_ == "geometric":
        numerator = np.average(
            [np.log(p) for p in predictions], weights=weights, axis=0
        )
        res = np.exp(numerator / sum(weights))
        return res
    elif type_ == "rank":
        res = np.average([rankdata(p) for p in predictions], weights=weights, axis=0)
        return res / (len(res) + 1)
    return res


def nicer_grid_results(grid_search: GridSearchCV) -> pd.DataFrame:
    """For sklearn seacrch grid returns a nice pd dataframe with the results"""
    grid_results = pd.DataFrame(grid_search.cv_results_).sort_values("rank_test_score")
    cols = [col for col in grid_results.columns if "param_" in col]
    cols = ["rank_test_score", "mean_test_score", "std_test_score"] + cols
    return grid_results[cols]


def get_coefs(lin_model, feats: list[str]) -> pd.Series:
    """Obtain coefficients from a skleanr linear model"""
    coef_vals = lin_model.coef_[0]
    coef_df = pd.DataFrame({"coef": coef_vals, "abs_coef": pd.Series(coef_vals).abs()})
    coef_df.index = feats
    is_coef_gt0 = coef_df["abs_coef"] > 0
    print(
        f"Number of features selected by lasso: {(is_coef_gt0).sum()} out of"
        f" {len(feats)}"
    )
    return coef_df.sort_values("abs_coef", ascending=False)["coef"]
