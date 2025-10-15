import pandas as pd
import numpy as np
from typing import Union, Optional


class AbstractPreSelector:
    """
    Abstract class for pre-selectors.
    """

    def __init__(self, n_algorithms: Optional[int] = None):
        """
        Initialize the pre-selector with the given configuration.

        Args:
            config (dict): Configuration for the pre-selector.
        """
        self.n_algorithms = n_algorithms

    def fit_transform(
        self, performance: Union[pd.DataFrame, np.ndarray]
    ) -> Union[pd.DataFrame, np.ndarray]:
        """
        Fit the pre-selector to the performance data and transform it.
        Args:
            performance (Union[pd.DataFrame, np.ndarray]): Performance data to fit and transform.
        Returns:
            Union[pd.DataFrame, np.ndarray]: Transformed performance data.
        """
        raise NotImplementedError(
            "fit_transform method must be implemented in subclasses."
        )
