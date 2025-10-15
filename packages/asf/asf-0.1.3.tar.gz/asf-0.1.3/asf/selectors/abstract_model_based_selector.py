from asf.selectors.abstract_selector import AbstractSelector
from asf.predictors import SklearnWrapper
from sklearn.base import ClassifierMixin, RegressorMixin
from asf.predictors.abstract_predictor import AbstractPredictor
from functools import partial
from typing import Type, Callable, Any, Union
from pathlib import Path
import joblib


class AbstractModelBasedSelector(AbstractSelector):
    """
    An abstract base class for selectors that utilize a machine learning model
    for selection purposes. This class provides functionality to initialize
    with a model class, save the selector to a file, and load it back.

    Attributes:
        model_class (Callable): A callable that represents the model class to
            be used. If the provided model_class is a subclass of
            `ClassifierMixin` or `RegressorMixin`, it is wrapped using
            `SklearnWrapper`.

    Methods:
        save(path: Union[str, Path]) -> None:
            Saves the current instance of the selector to the specified file path.
        load(path: Union[str, Path]) -> "AbstractModelBasedSelector":
            Loads a previously saved instance of the selector from the specified file path.
    """

    def __init__(self, model_class: Type[AbstractPredictor], **kwargs: Any) -> None:
        """
        Initializes the AbstractModelBasedSelector.

        Args:
            model_class (Union[Type, Callable]): The model class or a callable
                that returns a model instance. If a scikit-learn compatible
                class is provided, it's wrapped with SklearnWrapper.
            **kwargs (Any): Additional keyword arguments passed to the
                parent class initializer.
        """
        super().__init__(**kwargs)

        if isinstance(model_class, type) and issubclass(
            model_class, (ClassifierMixin, RegressorMixin)
        ):
            self.model_class: Callable = partial(SklearnWrapper, model_class)
        else:
            self.model_class: Callable = model_class

    def save(self, path: Union[str, Path]) -> None:
        """
        Saves the selector instance to the specified file path.

        Args:
            path (Union[str, Path]): The file path to save the selector.
        """
        joblib.dump(self, path)

    @staticmethod
    def load(path: Union[str, Path]) -> "AbstractModelBasedSelector":
        """
        Loads a selector instance from the specified file path.

        Args:
            path (Union[str, Path]): The file path to load the selector from.

        Returns:
            AbstractModelBasedSelector: The loaded selector instance.
        """
        return joblib.load(path)
