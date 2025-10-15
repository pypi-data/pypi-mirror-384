"""Functions to deal with big Query"""

from typing import Optional

import pandas as pd
from pandas_gbq import read_gbq


def read_bq_data(
    query_or_table: str,
    project_id: str,
    private_key: Optional[str] = None,
    progress_bar_type: str | None = "tqdm",
) -> pd.DataFrame:
    """Read a table from BQ"""
    result_df = read_gbq(
        query_or_table=query_or_table,
        project_id=project_id,
        private_key=private_key,
        dialect="standard",
        progress_bar_type=progress_bar_type,
    )
    return result_df


def bq_val_counts(
    table: str, col: str, project_id: str, private_key: Optional[str] = None
) -> pd.DataFrame:
    """Performs value counts for a table from BQ"""
    query = f"select {col}, count(*) as count from {table} group by {col} "
    result_df = read_bq_data(query, project_id, private_key)
    result_df["percentage (%)"] = (
        result_df["count"].div(sum(result_df["count"])).mul(100)
    )
    result_df = result_df.sort_values(by=["percentage (%)"], ascending=False)

    return result_df


def bq_peak_table(
    table: str, project_id: str, private_key: Optional[str] = None, limit: int = 1000
) -> pd.DataFrame:
    """Obtains top n from a bq table"""
    query = f"select * from {table} limit {limit}"
    result_df = read_bq_data(query, project_id, private_key)
    return result_df


def bq_summary(
    table: str, project_id: str, private_key: Optional[str] = None, limit: int = 1000
) -> pd.DataFrame:
    """Gets summary stats for a table in BQ"""
    table_components = table.split(".")  # Assumes the schema goes first
    schema, table_name = table_components[0], table_components[1]
    query = f"select column_name, data_type FROM {schema}.INFORMATION_SCHEMA.COLUMNS "
    query += f"where table_name = '{table_name}' order by ordinal_position"
    all_cols = read_bq_data(query, project_id, private_key, progress_bar_type=None)
    all_stats = []
    for _, row in all_cols.iterrows():
        type_ = row["data_type"]
        col = row["column_name"]

        query = f"select '{col}' as column, min({col}) as min, max({col}) as max"
        query += f", count(distinct {col}) as nunique, count(*) as count "
        if "INT" in type_ or "FLOAT" in type_:
            query += f", sqrt(var_pop({col})) as std "

        query += f"from {table}"
        col_df = read_bq_data(query, project_id, private_key, progress_bar_type=None)
        all_stats.append(col_df)
    return pd.concat(all_stats)
