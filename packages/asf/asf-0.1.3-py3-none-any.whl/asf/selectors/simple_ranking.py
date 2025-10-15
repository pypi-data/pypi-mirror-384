import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder

from asf.predictors.abstract_predictor import AbstractPredictor
from asf.selectors.abstract_model_based_selector import AbstractModelBasedSelector


class SimpleRanking(AbstractModelBasedSelector):
    """
    Algorithm Selection via Ranking (Oentaryo et al.) + algo features (optional).
    Attributes:
        model_class: The class of the classification model to be used.
        metadata: Metadata containing information about the algorithms.
        classifier: The trained classification model.
    """

    def __init__(self, model_class: AbstractPredictor, **kwargs):
        """
        Initializes the MultiClassClassifier with the given parameters.

        Args:
            model_class: The class of the classification model to be used. Assumes XGBoost API.
            metadata: Metadata containing information about the algorithms.
            hierarchical_generator: Feature generator to be used.
        """
        AbstractModelBasedSelector.__init__(self, model_class, **kwargs)
        self.classifier = None

    def _fit(
        self,
        features: pd.DataFrame,
        performance: pd.DataFrame,
    ):
        """
        Fits the classification model to the given feature and performance data.

        Args:
            features: DataFrame containing the feature data.
            performance: DataFrame containing the performance data.
        """
        if self.algorithm_features is None:
            encoder = OneHotEncoder(sparse_output=False)
            self.algorithm_features = pd.DataFrame(
                encoder.fit_transform(np.array(self.algorithms).reshape(-1, 1)),
                index=self.algorithms,
                columns=[f"algo_{i}" for i in range(len(self.algorithms))],
            )

        performance = performance[self.algorithms]
        features = features[self.features]
        features.index.name = "INSTANCE_ID"

        self.algorithm_features.index.name = "ALGORITHM"

        total_features = pd.merge(
            features.reset_index(), self.algorithm_features.reset_index(), how="cross"
        )

        stacked_performance = performance.stack().reset_index()
        stacked_performance.columns = [
            "INSTANCE_ID",
            "ALGORITHM",
            "PERFORMANCE",
        ]
        merged = total_features.merge(
            stacked_performance,
            right_on=["INSTANCE_ID", "ALGORITHM"],
            left_on=["INSTANCE_ID", "ALGORITHM"],
            how="left",
        )

        gdfs = []
        for group, gdf in merged.groupby("INSTANCE_ID"):
            gdf["rank"] = gdf["PERFORMANCE"].rank(
                ascending=True, method="max" if self.maximize else "min"
            )
            gdfs.append(gdf)
        merged = pd.concat(gdfs)

        total_features = merged.drop(
            columns=[
                "INSTANCE_ID",
                "ALGORITHM",
                "PERFORMANCE",
                "rank",
                self.algorithm_features.index.name,
            ]
        )
        qid = merged["INSTANCE_ID"].values
        encoder = OrdinalEncoder()
        qid = encoder.fit_transform(qid.reshape(-1, 1)).flatten()

        self.classifier = self.model_class()
        self.classifier.fit(
            total_features,
            merged["rank"],
            qid=qid,
        )

    def _predict(self, features: pd.DataFrame):
        """
        Predicts the best algorithm for each instance in the given feature data.

        Args:
            features: DataFrame containing the feature data.

        Returns:
            A dictionary mapping instance names to the predicted best algorithm.
        """

        features = features[self.features]

        total_features = pd.merge(
            features.reset_index(), self.algorithm_features.reset_index(), how="cross"
        )

        predictions = self.classifier.predict(
            total_features[list(self.features) + list(self.algorithm_features.columns)]
        )

        scheds = {}
        for instance_name in features.index.unique():
            ids = total_features[features.index.name] == instance_name
            chosen = predictions[ids].argmin()
            scheds[instance_name] = [
                (
                    total_features.loc[ids].iloc[chosen]["ALGORITHM"],
                    self.budget,
                )
            ]

        return scheds
