import numpy as np
import pandas as pd
from asf.predictors.ranking_mlp import RankingMLP
from sklearn.preprocessing import OneHotEncoder

from asf.selectors.abstract_model_based_selector import AbstractSelector
from asf.selectors.feature_generator import (
    AbstractFeatureGenerator,
)


class JointRanking(AbstractSelector, AbstractFeatureGenerator):
    """
    JointRanking implements a ranking-based approach for selecting the best-performing
    algorithms for a given set of features. It combines feature generation and model-based
    selection to predict algorithm performance.

    Reference:
        Ortuzk et al. (2022)
    """

    def __init__(
        self,
        model: RankingMLP = None,
        **kwargs,
    ) -> None:
        """
        Initializes the JointRanking selector with the given parameters.

        Args:
            model (RankingMLP, optional): The regression model to be used for ranking.
            **kwargs: Additional arguments passed to the AbstractSelector.
        """
        AbstractSelector.__init__(self, **kwargs)
        AbstractFeatureGenerator.__init__(self)
        self.model: RankingMLP = model

    def _fit(self, features: pd.DataFrame, performance: pd.DataFrame) -> None:
        """
        Fits the regression models to the given features and performance data.

        Args:
            features (pd.DataFrame): DataFrame containing the feature data.
            performance (pd.DataFrame): DataFrame containing the performance data.
        """
        if self.algorithm_features is None:
            encoder = OneHotEncoder(sparse_output=False)
            self.algorithm_features = pd.DataFrame(
                encoder.fit_transform(np.array(self.algorithms).reshape(-1, 1)),
                index=self.algorithms,
                columns=[f"algo_{i}" for i in range(len(self.algorithms))],
            )

        if self.model is None:
            self.model = RankingMLP(
                input_size=len(self.features) + len(self.algorithms)
            )

        self.model.fit(features[self.features], performance, self.algorithm_features)

    def _predict(self, features: pd.DataFrame) -> dict:
        """
        Predicts the performance of algorithms for the given features.

        Args:
            features (pd.DataFrame): DataFrame containing the feature data.

        Returns:
            dict: A dictionary mapping instance names to the predicted best algorithm
                  and the associated budget.
        """
        predictions = self.generate_features(features)

        return {
            instance_name: [
                (
                    self.algorithms[
                        np.argmax(predictions.loc[i])
                        if self.maximize
                        else np.argmin(predictions.loc[i])
                    ],
                    self.budget,
                )
            ]
            for i, instance_name in enumerate(features.index)
        }

    def generate_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        Generates predictions for the given features using the trained models.

        Args:
            features (pd.DataFrame): DataFrame containing the feature data.

        Returns:
            pd.DataFrame: DataFrame containing the predictions for each algorithm.
        """
        predictions = np.zeros((features.shape[0], len(self.algorithms)))

        features = features[self.features]
        for i, algorithm in enumerate(self.algorithms):
            data = features.assign(**self.algorithm_features.loc[algorithm])
            data = data[self.algorithm_features.columns.to_list() + self.features]
            prediction = self.model.predict(data)
            predictions[:, i] = prediction.flatten()

        return pd.DataFrame(predictions, columns=self.algorithms)
