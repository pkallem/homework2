"""
Implement the following models for classification.

Feel free to modify the arguments for each of model's __init__ function.
This will be useful for tuning model hyperparameters such as hidden_dim, num_layers, etc,
but remember that the grader will assume the default constructor!
"""

from pathlib import Path

import torch
import torch.nn as nn


class ClassificationLoss(nn.Module):
    def forward(self, logits: torch.Tensor, target: torch.LongTensor) -> torch.Tensor:
        """
        Multi-class classification loss
        Hint: simple one-liner

        Args:
            logits: tensor (b, c) logits, where c is the number of classes
            target: tensor (b,) labels

        Returns:
            tensor, scalar loss
        """
        return nn.functional.cross_entropy(logits, target)


class LinearClassifier(nn.Module):
    def __init__(
        self,
        h: int = 64,
        w: int = 64,
        num_classes: int = 6,
    ):
        """
        Args:
            h: int, height of the input image
            w: int, width of the input image
            num_classes: int, number of classes
        """
        super().__init__()
        self.fc = nn.Linear(3 * h * w, num_classes)
        self._model_name = "linear"

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: tensor (b, 3, H, W) image

        Returns:
            tensor (b, num_classes) logits
        """
        x = x.view(x.size(0), -1)
        return self.fc(x)


class MLPClassifier(nn.Module):
    def __init__(
        self,
        h: int = 64,
        w: int = 64,
        num_classes: int = 6,
        hidden_dim: int = 128,
    ):
        """
        An MLP with a single hidden layer

        Args:
            h: int, height of the input image
            w: int, width of the input image
            num_classes: int, number of classes
            hidden_dim: int, dimension of the hidden layer
        """
        super().__init__()
        self.fc1 = nn.Linear(3 * h * w, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, num_classes)
        self._model_name = "mlp"

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: tensor (b, 3, H, W) image

        Returns:
            tensor (b, num_classes) logits
        """
        x = x.view(x.size(0), -1)
        x = self.relu(self.fc1(x))
        return self.fc2(x)


class MLPClassifierDeep(nn.Module):
    def __init__(
        self,
        h: int = 64,
        w: int = 64,
        num_classes: int = 6,
        hidden_dim: int = 128,
        num_layers: int = 3,
    ):
        """
        An MLP with multiple hidden layers

        Args:
            h: int, height of image
            w: int, width of image
            num_classes: int
            hidden_dim: int, size of hidden layers
            num_layers: int, number of hidden layers (>= 2 for "deep")
        """
        super().__init__()
        self.fc_in = nn.Linear(3 * h * w, hidden_dim)
        self.hidden_layers = nn.ModuleList([
            nn.Linear(hidden_dim, hidden_dim) for _ in range(num_layers - 1)
        ])
        self.relu = nn.ReLU()
        self.fc_out = nn.Linear(hidden_dim, num_classes)
        self._model_name = "mlp_deep"

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: tensor (b, 3, H, W) image

        Returns:
            tensor (b, num_classes) logits
        """
        x = x.view(x.size(0), -1)
        x = self.relu(self.fc_in(x))
        for layer in self.hidden_layers:
            x = self.relu(layer(x))
        return self.fc_out(x)


class MLPClassifierDeepResidual(nn.Module):
    def __init__(
        self,
        h: int = 64,
        w: int = 64,
        num_classes: int = 6,
        hidden_dim: int = 128,
        num_layers: int = 3,
    ):
        """
        MLP with multiple hidden layers and residual connections

        Args:
            h: int, height of image
            w: int, width of image
            num_classes: int
            hidden_dim: int, size of hidden layers
            num_layers: int, number of residual blocks
        """
        super().__init__()
        self.fc_in = nn.Linear(3 * h * w, hidden_dim)
        self.res_blocks = nn.ModuleList([
            nn.Linear(hidden_dim, hidden_dim) for _ in range(num_layers)
        ])
        self.relu = nn.ReLU()
        self.fc_out = nn.Linear(hidden_dim, num_classes)
        self._model_name = "mlp_deep_residual"

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: tensor (b, 3, H, W) image

        Returns:
            tensor (b, num_classes) logits
        """
        x = x.view(x.size(0), -1)
        x = self.relu(self.fc_in(x))
        for block in self.res_blocks:
            residual = x
            x = self.relu(block(x) + residual)
        return self.fc_out(x)


model_factory = {
    "linear": LinearClassifier,
    "mlp": MLPClassifier,
    "mlp_deep": MLPClassifierDeep,
    "mlp_deep_residual": MLPClassifierDeepResidual,
}


def calculate_model_size_mb(model: torch.nn.Module) -> float:
    """
    Args:
        model: torch.nn.Module

    Returns:
        float, size in megabytes
    """
    return sum(p.numel() for p in model.parameters()) * 4 / 1024 / 1024


def save_model(model):
    """
    Use this function to save your model in train.py
    """
    from pathlib import Path

    # Use the model's own name if available
    model_name = getattr(model, "_model_name", None)
    if model_name is None:
        for n, m in model_factory.items():
            if isinstance(model, m):
                model_name = n
                break
    if model_name is None:
        raise ValueError(f"Model type '{str(type(model))}' not supported")
    torch.save(model.state_dict(), Path(__file__).resolve().parent / f"{model_name}.th")


def load_model(model_name: str, with_weights: bool = False, **model_kwargs):
    """
    Called by the grader to load a pre-trained model by name
    """
    from pathlib import Path
    r = model_factory[model_name](**model_kwargs)
    r._model_name = model_name  # ensure the model's name attribute is set
    if with_weights:
        model_path = Path(__file__).resolve().parent / f"{model_name}.th"
        assert model_path.exists(), f"{model_path.name} not found"
        try:
            r.load_state_dict(torch.load(model_path, map_location="cpu"))
        except RuntimeError as e:
            raise AssertionError(
                f"Failed to load {model_path.name}, make sure the default model arguments are set correctly"
            ) from e

    # Limit model sizes since they will be zipped and submitted
    model_size_mb = calculate_model_size_mb(r)
    if model_size_mb > 10:
        raise AssertionError(f"{model_name} is too large: {model_size_mb:.2f} MB")
    print(f"Model size: {model_size_mb:.2f} MB")

    return r
