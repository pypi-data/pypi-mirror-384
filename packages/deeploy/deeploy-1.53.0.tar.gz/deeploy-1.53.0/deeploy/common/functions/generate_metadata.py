import logging
from typing import Optional

import numpy as np
import pandas as pd

from deeploy.enums.metadata import ProblemType

logger = logging.getLogger(__name__)


def generate_metadata(
    df_train: pd.DataFrame, problem_type: Optional[ProblemType] = None, custom_id=None
) -> dict:
    """
    Generate metadata for a given dataframe and input parameters.

    Args:
        df_train (pd.DataFrame): Input pandas dataframe of data used to train model (e.g. X_train)
        problem_type (Optional[ProblemType], optional): Problem type. Defaults to None.
        custom_id (str, optional): Custom ID. Defaults to None.

    Returns:
        dict: Generated metadata.

    Raises:
        TypeError: If df is not a pandas dataframe.
    """

    if not isinstance(df_train, pd.DataFrame):
        raise TypeError("Input should be a pandas dataframe.")

    metadata = {}

    # problemType
    if problem_type:
        metadata["problemType"] = problem_type.value

    # features
    if len(df_train) >= 3:
        metadata["features"] = get_feature_distribution(df_train)
    else:
        metadata["features"] = get_feature_names(df_train)

    if len(df_train) >= 1:
        metadata["exampleInput"] = get_example_data(df_train)
        metadata["inputTensorShape"] = str(get_tensor_shape_data(df_train))

    if custom_id:
        metadata["customId"] = custom_id

    return metadata


def get_example_data(df: pd.DataFrame, data_index=0):
    return {"instances": [df.iloc[data_index].to_list()]}


def get_tensor_shape_data(df: pd.DataFrame):
    return df.iloc[0].shape


def get_feature_names(df: pd.DataFrame):
    data = []
    for column in df.columns:
        data.append({"name": column})
    return data


def get_feature_distribution(df: pd.DataFrame):
    hist_data = []
    for column in df.columns:
        # Calculate histogram data

        is_numeric = pd.api.types.is_numeric_dtype(df[column])

        if is_numeric:
            num_unique_values = len(np.unique(df[column]))

            if num_unique_values <= 10:
                num_bins = num_unique_values
            else:
                # Sturges' formula capped at 30 bins
                num_bins = min(30, int(np.ceil(np.log2(len(df[column])) + 1)))

            hist, bin_edges = np.histogram(df[column].dropna(), bins=num_bins)

            distribution_data = []

            for i, count in enumerate(hist):
                distribution_data.append(
                    {
                        "start": str(np.round(bin_edges[i], 5)),
                        "end": str(np.round(bin_edges[i + 1], 5)),
                        "count": str(count),
                    }
                )

            column_data = {
                "name": column,
                "observedMin": str(np.round(df[column].min(), 5)),
                "observedMax": str(np.round(df[column].max(), 5)),
                "observedMean": str(np.round(df[column].mean(), 5)),
                "distribution": distribution_data,
            }
            hist_data.append(column_data)
        else:
            logger.warning(
                f"Warning: Column {column} contains non-numeric dtypes, not calculating statistical distribution for column {column}."
            )
            column_data = {
                "name": column,
            }
            hist_data.append(column_data)

    return hist_data
