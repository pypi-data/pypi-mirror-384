try:
    import torch

    TORCH_AVAILABLE = True
    from asf.predictors.utils.datasets import RegressionDataset
    from asf.predictors.utils.mlp import get_mlp
except ImportError:
    TORCH_AVAILABLE = False

import pandas as pd
from sklearn.impute import SimpleImputer

from asf.predictors.abstract_predictor import AbstractPredictor


if TORCH_AVAILABLE:

    class RegressionMLP(AbstractPredictor):
        def __init__(
            self,
            model: torch.nn.Module | None = None,
            loss: torch.nn.modules.loss._Loss | None = torch.nn.MSELoss(),
            optimizer: type[torch.optim.Optimizer] | None = torch.optim.Adam,
            batch_size: int = 128,
            epochs: int = 2000,
            seed: int = 42,
            device: str = "cpu",
            compile: bool = True,
            **kwargs,
        ):
            """
            Initializes the RegressionMLP with the given parameters.

            Args:
                model (torch.nn.Module | None): The PyTorch model to be used. If None, a new MLP model will be created.
                input_size (int | None): The size of the input features. Required if `model` is None.
                loss (torch.nn.modules.loss._Loss | None): The loss function to be used. Defaults to Mean Squared Error Loss.
                optimizer (type[torch.optim.Optimizer] | None): The optimizer class to be used. Defaults to Adam.
                batch_size (int): The batch size for training. Defaults to 128.
                epochs (int): The number of epochs for training. Defaults to 2000.
                seed (int): The random seed for reproducibility. Defaults to 42.
                device (str): The device to run the model on ('cpu' or 'cuda'). Defaults to 'cpu'.
                compile (bool): Whether to compile the model using `torch.compile`. Defaults to True.
                **kwargs: Additional keyword arguments passed to the parent class.
            """
            super().__init__(**kwargs)

            assert TORCH_AVAILABLE, "PyTorch is not available. Please install it."

            torch.manual_seed(seed)

            self.model = model
            self.device = device

            self.loss = loss
            self.batch_size = batch_size
            self.optimizer = optimizer
            self.epochs = epochs
            self.compile = compile

        def _get_dataloader(
            self, features: pd.DataFrame, performance: pd.DataFrame
        ) -> torch.utils.data.DataLoader:
            """
            Creates a DataLoader for the given features and performance data.

            Args:
                features (pd.DataFrame): DataFrame containing the feature data.
                performance (pd.DataFrame): DataFrame containing the performance data.

            Returns:
                torch.utils.data.DataLoader: DataLoader for the dataset.
            """
            dataset = RegressionDataset(features, performance)
            return torch.utils.data.DataLoader(
                dataset, batch_size=self.batch_size, shuffle=True
            )

        def fit(
            self, features: pd.DataFrame, performance: pd.DataFrame, sample_weight=None
        ) -> "RegressionMLP":
            """
            Fits the model to the given feature and performance data.

            Args:
                features (pd.DataFrame): DataFrame containing the feature data.
                performance (pd.DataFrame): DataFrame containing the performance data.

            Returns:
                RegressionMLP: The fitted model instance.
            """
            assert sample_weight is None, "Sample weights are not supported."

            if self.model is None:
                self.model = get_mlp(input_size=features.shape[1], output_size=1)

            self.model.to(self.device)

            if self.compile:
                self.model = torch.compile(self.model)

            features = pd.DataFrame(
                SimpleImputer().fit_transform(features.values),
                index=features.index,
                columns=features.columns,
            )
            dataloader = self._get_dataloader(features, performance)

            optimizer = self.optimizer(self.model.parameters())
            self.model.train()
            for epoch in range(self.epochs):
                total_loss = 0
                for i, (X, y) in enumerate(dataloader):
                    X, y = X.to(self.device), y.to(self.device)
                    X = X.float()
                    y = y.unsqueeze(-1)
                    optimizer.zero_grad()
                    y_pred = self.model(X)
                    loss = self.loss(y_pred, y)
                    total_loss += loss.item()
                    loss.backward()
                    optimizer.step()

            return self

        def predict(self, features: pd.DataFrame) -> pd.DataFrame:
            """
            Predicts the performance of algorithms for the given features.

            Args:
                features (pd.DataFrame): DataFrame containing the feature data.

            Returns:
                pd.DataFrame: DataFrame containing the predicted performance data.
            """
            self.model.eval()

            features = torch.from_numpy(features.values).to(self.device).float()
            predictions = self.model(features).detach().numpy().squeeze(1)

            return predictions

        def save(self, file_path: str) -> None:
            """
            Saves the model to the specified file path.

            Args:
                file_path (str): The path to save the model.
            """
            torch.save(self.model, file_path)

        def load(self, file_path: str) -> None:
            """
            Loads the model from the specified file path.

            Args:
                file_path (str): The path to load the model from.
            """
            self.model = torch.load(file_path)

else:

    class RegressionMLP(AbstractPredictor):
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch is not available. Please install it.")
