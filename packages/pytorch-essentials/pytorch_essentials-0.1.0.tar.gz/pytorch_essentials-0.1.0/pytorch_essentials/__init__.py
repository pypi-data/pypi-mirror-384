"""
PyTorch Essentials - A collection of useful utilities for PyTorch model training.

This package provides:
- Training and evaluation loops
- Early stopping callbacks
- Model saving/loading utilities
- Visualization tools
- Configuration management
"""

__version__ = "0.1.0"

from pytorch_essentials.engine import train, train_step, test_step, evaluate_model
from pytorch_essentials.callbacks import EarlyStopping
from pytorch_essentials.utils import (
    get_device,
    save_model,
    count_parameters,
    set_seeds,
    load_config,
    print_config,
)
from pytorch_essentials.visualization import (
    plot_loss_curves,
    print_train_time,
)

__all__ = [
    # Training functions
    "train",
    "train_step",
    "test_step",
    "evaluate_model",
    # Callbacks
    "EarlyStopping",
    # Utilities
    "get_device",
    "save_model",
    "count_parameters",
    "set_seeds",
    "load_config",
    "print_config",
    # Visualization
    "plot_loss_curves",
    "print_train_time",
]
