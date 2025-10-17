"""
Utility functions for PyTorch model training and management.
"""
from pathlib import Path
import torch
import json
import yaml


def get_device() -> torch.device:
    """Return the best available device (CUDA > MPS > CPU).

    Returns:
        torch.device: The device to use for training/inference.

    Example:
        >>> device = get_device()
        >>> model = model.to(device)
    """
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    return device


def save_model(
    model: torch.nn.Module,
    fig,
    results: dict,
    save_path: str
):
    """Save a PyTorch model, weights, loss curves, and results to a target directory.

    Args:
        model (torch.nn.Module): PyTorch model to save.
        fig: Matplotlib figure containing the loss curves.
        results (dict): Dictionary containing training results/metrics.
        save_path (str): Path where to save the model artifacts.

    Example:
        >>> save_model(
        >>>     model=model,
        >>>     fig=loss_curve_fig,
        >>>     results=training_results,
        >>>     save_path="experiment_1"
        >>> )
    """
    # Determine model name
    if hasattr(model, 'model_name') and model.model_name is not None:
        model_name = model.model_name
    else:
        model_name = model.__class__.__name__

    # Create target directory
    target_dir_path = Path(f"results/{model_name}/{save_path}")
    target_dir_path.mkdir(parents=True, exist_ok=True)

    # Save artifacts
    print(f"[INFO] Saving model artifacts to: {target_dir_path}")
    try:
        torch.save(obj=model.state_dict(), f=target_dir_path / "weights.pth")
        fig.savefig(target_dir_path / "loss_curves.png")

        # Save results as JSON
        with open(target_dir_path / "results.json", "w") as f:
            json.dump(results, f, indent=2)

        print("[INFO] Successfully saved model, weights, and results")
    except Exception as e:
        print(f"[ERROR] Failed to save: {e}")


def count_parameters(model: torch.nn.Module) -> tuple:
    """Calculate and display the number of parameters in a PyTorch model.

    Args:
        model (torch.nn.Module): The PyTorch model to analyze.

    Returns:
        tuple: (total, trainable, non_trainable) parameter counts.

    Example:
        >>> total, trainable, non_trainable = count_parameters(model)
        ******** Model ********
        [INFO] Number of parameters: 1.23M
        [INFO] Trainable: 1.20M     Non trainable: 30.00K
    """
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    non_trainable = sum(p.numel() for p in model.parameters() if not p.requires_grad)
    total = trainable + non_trainable

    # Get model name
    model_name = getattr(model, 'name', model.__class__.__name__)

    def format_num(num):
        """Format number with K, M, B, T suffixes."""
        units = ["", "K", "M", "B", "T"]
        magnitude = 0
        while abs(num) >= 1000 and magnitude < len(units) - 1:
            num /= 1000.0
            magnitude += 1
        return f"{num:.2f}{units[magnitude]}"

    print(f"{8*'*'}\t{model_name}\t{8*'*'}")
    print(f"[INFO] Number of parameters: {format_num(total)}")
    print(f"[INFO] Trainable: {format_num(trainable)} \t Non trainable: {format_num(non_trainable)}")

    return total, trainable, non_trainable


def set_seeds(seed: int = 42):
    """Set random seeds for reproducibility.

    Args:
        seed (int): Random seed to set. Defaults to 42.

    Example:
        >>> set_seeds(42)
    """
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # For multi-GPU


def load_config(config_path: str) -> dict:
    """Load a YAML configuration file.

    Args:
        config_path (str): Path to the YAML config file.

    Returns:
        dict: Configuration dictionary.

    Example:
        >>> config = load_config('config.yaml')
    """
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def print_config(config: dict):
    """Pretty-print a configuration dictionary.

    Args:
        config (dict): Configuration dictionary to print.

    Example:
        >>> print_config(config)
    """
    print("[INFO] Configuration:")
    for section, params in config.items():
        print(f"  {section}:")
        if isinstance(params, dict):
            for key, value in params.items():
                print(f"    {key}: {value}")
        else:
            print(f"    {params}")
