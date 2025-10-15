import pandas as pd


class AbstractFeatureGenerator:
    """
    AbstractFeatureGenerator is a base class for generating additional features
    based on a set of base features. Subclasses should implement the methods
    to define specific feature generation logic.
    """

    def __init__(self) -> None:
        """
        Initialize the AbstractFeatureGenerator.
        """
        pass

    def generate_features(self, base_features: pd.DataFrame) -> pd.DataFrame:
        """
        Generate additional features based on the provided base features.

        Parameters
        ----------
        base_features : pd.DataFrame
            The input DataFrame containing the base features.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the generated features.

        Raises
        ------
        NotImplementedError
            If the method is not implemented in a subclass.
        """
        raise NotImplementedError(
            "generate_features() must be implemented in a subclass"
        )
