from typing import Any, Optional

try:
    from ConfigSpace import ConfigurationSpace
    from ConfigSpace.hyperparameters import Hyperparameter

    CONFIGSPACE_AVAILABLE = True
except ImportError:
    CONFIGSPACE_AVAILABLE = False
from typing import Dict
from abc import ABC, abstractmethod


class AbstractPredictor(ABC):
    """
    Abstract base class for all predictors.

    Methods
    -------
    fit(X, Y, **kwargs)
        Fit the model to the data.
    predict(X, **kwargs)
        Predict using the model.
    save(file_path)
        Save the model to a file.
    load(file_path)
        Load the model from a file.
    get_configuration_space(cs)
        Get the configuration space for the predictor.
    get_from_configuration(configuration)
        Get a predictor instance from a configuration.
    """

    def __init__(self):
        """
        Initialize the predictor.
        """
        pass

    @abstractmethod
    def fit(self, X: Any, Y: Any, **kwargs: Any) -> None:
        """
        Fit the model to the data.

        Parameters
        ----------
        X : Any
            Training data.
        Y : Any
            Target values.
        kwargs : Any
            Additional arguments for fitting the model.
        """
        pass

    @abstractmethod
    def predict(self, X: Any, **kwargs: Any) -> Any:
        """
        Predict using the model.

        Parameters
        ----------
        X : Any
            Data to predict on.
        kwargs : Any
            Additional arguments for prediction.

        Returns
        -------
        Any
            Predicted values.
        """
        pass

    @abstractmethod
    def save(self, file_path: str) -> None:
        """
        Save the model to a file.

        Parameters
        ----------
        file_path : str
            Path to the file where the model will be saved.
        """
        pass

    @abstractmethod
    def load(self, file_path: str) -> None:
        """
        Load the model from a file.

        Parameters
        ----------
        file_path : str
            Path to the file from which the model will be loaded.
        """
        pass


if CONFIGSPACE_AVAILABLE:

    @staticmethod
    def get_configuration_space(
        cs: Optional[ConfigurationSpace] = None,
        pre_prefix: str = "",
        parent_param: Optional[Hyperparameter] = None,
        parent_value: Optional[str] = None,
    ) -> Any:
        """
        Get the configuration space for the predictor.

        Parameters
        ----------
        cs : Optional[Any], optional
            The configuration space to add the parameters to. If None, a new configuration space will be created.

        Returns
        -------
        Any
            The configuration space for the predictor.

        Raises
        ------
        NotImplementedError
            If the method is not implemented for the predictor.
        """
        raise NotImplementedError(
            "get_configuration_space() is not implemented for this predictor"
        )

    @staticmethod
    def get_from_configuration(
        configuration: Dict[str, Any], pre_prefix: str = "", **kwargs
    ) -> "AbstractPredictor":
        """
        Get a predictor instance from a configuration.

        Parameters
        ----------
        configuration : Any
            The configuration to create the predictor from.

        Returns
        -------
        AbstractPredictor
            The predictor instance.

        Raises
        ------
        NotImplementedError
            If the method is not implemented for the predictor.
        """
        raise NotImplementedError(
            "get_from_configuration() is not implemented for this predictor"
        )
