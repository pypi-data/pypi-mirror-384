"""Functions to help with Exploratory data analysis"""

import pandas as pd

from doors.setup_logger import get_logger

logger = get_logger(__name__)


def get_correlations_for_col(
    data: pd.DataFrame, col: str, method="pearson"
) -> pd.DataFrame:
    corr = data.corr(numeric_only=True, method=method)[col]
    ans = pd.DataFrame(
        {
            "abs": corr.abs(),
            "corr": corr,
        }
    )
    ans.sort_values("abs", ascending=False, inplace=True)
    return ans


def val_counts(df, column):
    """Displays pandas value counts with a %"""
    vc_df = df.reset_index().groupby([column]).size().to_frame("count")
    vc_df["percentage (%)"] = vc_df["count"].div(sum(vc_df["count"])).mul(100)
    vc_df = vc_df.sort_values(by=["percentage (%)"], ascending=False)
    logger.info(f'STATUS: Value counts for "{column}"...')
    return vc_df
