import json
import os
import pickle
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd


def read_epmbench_scenario(
    path: str, load_subsample: bool = False
) -> Union[
    Tuple[pd.DataFrame, List[str], List[str], Optional[pd.DataFrame], Dict[str, Any]],
    Tuple[
        pd.DataFrame,
        List[str],
        List[str],
        Optional[pd.DataFrame],
        Dict[str, Any],
        Dict[str, Any],
    ],
]:
    """
    Reads the EPMBench scenario from the given path.

    Args:
        path (str): Path to the EPMBench scenario directory.
        load_subsample (bool, optional): Whether to load subsample data. Defaults to False.

    Returns:
        Union[Tuple[pd.DataFrame, List[str], List[str], Optional[pd.DataFrame], Dict[str, Any]],
              Tuple[pd.DataFrame, List[str], List[str], Optional[pd.DataFrame], Dict[str, Any], Dict[str, Any]]]:
              If `load_subsample` is False, returns a tuple containing:
                - data (pd.DataFrame): The main dataset.
                - features (List[str]): List of feature names.
                - targets (List[str]): List of target names.
                - groups (Optional[pd.DataFrame]): Group information if available, otherwise None.
                - metadata (Dict[str, Any]): Metadata dictionary.
              If `load_subsample` is True, an additional subsample dictionary is included in the tuple.
    """
    with open(os.path.join(path, "metadata.json"), "r") as f:
        metadata = json.load(f)

    data = pd.read_parquet(os.path.join(path, "data.parquet"))
    if "groups" in metadata:
        groups = data[metadata["groups"]]
        data.drop(columns=[metadata["groups"]], inplace=True)
    else:
        groups = None

    if load_subsample:
        with open(os.path.join(path, "subsamples.pkl"), "rb") as f:
            subsample_dict = pickle.load(f)

    if not load_subsample:
        return data, metadata["features"], metadata["targets"], groups, metadata
    else:
        return (
            data,
            metadata["features"],
            metadata["targets"],
            groups,
            metadata,
            subsample_dict,
        )


def get_cv_fold(
    data: pd.DataFrame,
    fold: int,
    features: List[str],
    target: List[str],
    groups: Optional[pd.DataFrame] = None,
) -> Tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
]:
    """
    Splits the data into training and testing sets based on the specified fold.

    Args:
        data (pd.DataFrame): The dataset.
        fold (int): The fold number.
        features (List[str]): List of feature names.
        target (List[str]): List of target names.
        groups (Optional[pd.DataFrame], optional): Group information if available. Defaults to None.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        A tuple containing:
            - X_train (pd.DataFrame): Training features.
            - y_train (pd.DataFrame): Training targets.
            - X_test (pd.DataFrame): Testing features.
            - y_test (pd.DataFrame): Testing targets.
            - groups_train (Optional[pd.DataFrame]): Training groups if available, otherwise None.
            - groups_test (Optional[pd.DataFrame]): Testing groups if available, otherwise None.
    """
    train_idx = data["cv"] != fold
    test_idx = data["cv"] == fold

    train_data = data[train_idx]
    test_data = data[test_idx]

    X_train = train_data[features]
    y_train = train_data[target]
    X_test = test_data[features]
    y_test = test_data[target]

    if groups is not None:
        groups_train = groups[train_idx]
        groups_test = groups[test_idx]
    else:
        groups_train = None
        groups_test = None

    return X_train, y_train, X_test, y_test, groups_train, groups_test


def get_subsample(
    data: pd.DataFrame,
    iter: int,
    subsample_size: int,
    features: List[str],
    target: List[str],
    subsample_dict: Dict[str, Any],
    groups: Optional[pd.DataFrame] = None,
) -> Tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
]:
    """
    Splits the data into training and testing sets based on the specified subsample iteration.

    Args:
        data (pd.DataFrame): The dataset.
        iter (int): The iteration number.
        subsample_size (int): The size of the subsample.
        features (List[str]): List of feature names.
        target (List[str]): List of target names.
        subsample_dict (Dict[str, Any]): Dictionary containing subsample indices.
        groups (Optional[pd.DataFrame], optional): Group information if available. Defaults to None.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        A tuple containing:
            - X_train (pd.DataFrame): Training features.
            - y_train (pd.DataFrame): Training targets.
            - X_test (pd.DataFrame): Testing features.
            - y_test (pd.DataFrame): Testing targets.
            - groups_train (Optional[pd.DataFrame]): Training groups if available, otherwise None.
            - groups_test (Optional[pd.DataFrame]): Testing groups if available, otherwise None.
    """
    train_idx = subsample_dict["subsamples"][subsample_size][iter]
    test_idx = subsample_dict["test"]

    train_data = data.loc[train_idx]
    test_data = data.loc[test_idx]

    X_train = train_data[features]
    y_train = train_data[target]
    X_test = test_data[features]
    y_test = test_data[target]

    if groups is not None:
        groups_train = groups[train_idx]
        groups_test = groups[test_idx]
    else:
        groups_train = None
        groups_test = None

    return X_train, y_train, X_test, y_test, groups_train, groups_test
