import numpy as np
import pandas as pd
import plotly.express as px
import plotly.offline as pyo
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib_venn import venn2
from sklearn import linear_model, preprocessing
from sklearn.metrics import f1_score, roc_auc_score

from doors.np import rolling_mean


def add_best_fit_curve(x, y, degree, fit_intercept, **kwargs):
    mm = make_polynomial_mm(x=x, degree=degree)
    model = linear_model.LinearRegression(n_jobs=-1, fit_intercept=fit_intercept)
    model.fit(X=mm, y=y)
    predictions = model.predict(X=mm)

    ix = np.argsort(x)
    label = "Best Fit Degree {}".format(degree)
    plt.plot(x[ix], predictions[ix], "--", label=label, **kwargs)


def plot_best_fit(x, y, best_fit_degrees, fit_intercept):
    if not isinstance(best_fit_degrees, list):
        best_fit_degrees = [best_fit_degrees]
    for degree in best_fit_degrees:
        add_best_fit_curve(x, y, degree, fit_intercept)


def plot_rolling_mean(x, window, **matplotlib_kwargs):
    rolling_means = rolling_mean(x, window)
    plt.plot(rolling_means, **matplotlib_kwargs)


def make_polynomial_mm(x, degree):
    if x.ndim == 1:
        x = x[:, np.newaxis]
    poly = preprocessing.PolynomialFeatures(degree=degree, include_bias=False)
    return poly.fit_transform(X=x)


def plot_venn2_primary_secondary(elements_by_group, venn_values, ax):
    """Plot venn diagram of 2 groups
    it needs the elements_by_group (all elements that belong to a group,
    so if "element1" apears in A and B, it will apear in (A, b), (A, ), and (B, )
    venn_values: same as interactions but only shows elements once
    so if "element1" apears in A and B, it will apear only in (A, b)
    """
    A = elements_by_group[("primary",)]
    B = elements_by_group[("backup",)]
    v = venn2([A, B], ["backup", "primary"], ax=ax)

    v.get_label_by_id("11").set_text(
        "\n".join(np.array(list(venn_values[("backup", "primary")])).astype(str))
    )
    v.get_label_by_id("10").set_text(
        "\n".join(np.array(list(venn_values[("primary",)])).astype(str))
    )
    v.get_label_by_id("01").set_text(
        "\n".join(np.array(list(venn_values[("backup",)])).astype(str))
    )
    plt.show()

    return v


def plot_pairplot_in_sections(
    data: pd.DataFrame,
    target_name: str,
    feats: list,
    sample=200,
    n_feats_to_plot=5,
    hue_col=False,
    corner=True,
    legend=True,
):
    for i in range(0, len(feats), n_feats_to_plot):
        start = i
        if i + n_feats_to_plot > len(feats):
            end = len(feats)
        else:
            end = i + n_feats_to_plot
        if hue_col:
            plot_cols = [target_name] + feats[start:end] + [hue_col]
        else:
            plot_cols = [target_name] + feats[start:end]

        g = sns.pairplot(data[plot_cols].sample(sample), hue=hue_col, corner=corner)
        if not legend:
            g._legend.remove()
        print(f"processed {plot_cols}")


def get_actual_vs_prediction_plot(
    actual: np.ndarray | pd.Series,
    predictions: np.ndarray | pd.Series,
    x_values: np.ndarray | pd.Series | None = None,
) -> None:
    """Plot actual vs prodeiction arrays or series"""
    data_dict = {"Actual": actual, "Predictions": predictions}
    if x_values is not None:
        data_dict["X"] = x_values
    data = pd.DataFrame(data_dict)

    fig = px.scatter(
        data,
        x="X",
        y=["Actual", "Predictions"],
        labels={"X": "X-Axis Label", "value": "Value"},
        title="Actual vs. Predictions",
    )

    pyo.iplot(fig)


def plot_roc(truth, preds, title="Receiver Operating Characteristic", threshold=0.5):
    # require extra library:
    from plot_metric.functions import BinaryClassification

    print("AUC: ", np.round(roc_auc_score(truth, preds), 5))
    bc = BinaryClassification(truth, preds, labels=[0, 1], threshold=threshold)
    plt.figure(figsize=(10, 5))
    bc.plot_roc_curve(title=title)
    plt.show()


def plot_precision_recall_curve(
    truth, preds, title="Precision-Recall Curve", threshold=0.5
):
    from plot_metric.functions import BinaryClassification

    print("F1: ", np.round(f1_score(truth, preds > threshold), 8))
    bc = BinaryClassification(truth, preds, labels=[0, 1], threshold=threshold)
    plt.figure(figsize=(10, 5))
    bc.plot_precision_recall_curve(title=title)
    plt.show()
