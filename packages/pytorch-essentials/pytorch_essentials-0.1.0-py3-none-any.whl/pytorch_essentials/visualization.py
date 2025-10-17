"""
Visualization functions for training metrics and results.
"""
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


def print_train_time(start: float, end: float, device=None) -> float:
    """Print the difference between start and end time.

    Args:
        start (float): Start time of computation (in seconds).
        end (float): End time of computation (in seconds).
        device: Device that compute is running on. Defaults to None.

    Returns:
        float: Time between start and end in seconds.

    Example:
        >>> import time
        >>> start = time.time()
        >>> # ... training code ...
        >>> end = time.time()
        >>> print_train_time(start, end, device='cuda')
    """
    total_time = end - start
    print(f"\nTrain time on {device}: {total_time:.3f} seconds")
    return total_time


def plot_loss_curves(results: dict) -> Figure:
    """Plot training curves from a results dictionary.

    Args:
        results (dict): Dictionary containing training metrics with keys:
            - "train_loss": List of training losses per epoch
            - "train_acc": List of training accuracies per epoch
            - "test_loss": List of validation/test losses per epoch
            - "test_acc": List of validation/test accuracies per epoch
            - "best_epoch": (Optional) Epoch number with best validation performance

    Returns:
        matplotlib.figure.Figure: Figure containing the loss and accuracy plots.

    Example:
        >>> results = {
        >>>     "train_loss": [2.0, 1.5, 1.0],
        >>>     "train_acc": [0.4, 0.6, 0.8],
        >>>     "test_loss": [2.1, 1.6, 1.2],
        >>>     "test_acc": [0.35, 0.55, 0.75],
        >>>     "best_epoch": 2
        >>> }
        >>> fig = plot_loss_curves(results)
        >>> fig.savefig('training_curves.png')
    """
    loss = results["train_loss"]
    test_loss = results["test_loss"]
    accuracy = results["train_acc"]
    test_accuracy = results["test_acc"]

    epochs = range(1, len(loss) + 1)

    # Create figure and axes
    fig, ax = plt.subplots(1, 2, figsize=(15, 7))

    # Plot loss
    ax[0].plot(epochs, loss, label="Train Loss", marker='o')
    ax[0].plot(epochs, test_loss, label="Test Loss", marker='o')
    ax[0].set_title("Loss", fontsize=14, fontweight='bold')
    ax[0].set_xlabel("Epochs")
    ax[0].set_ylabel("Loss")
    ax[0].legend()
    ax[0].grid(True, alpha=0.3)

    # Plot accuracy
    ax[1].plot(epochs, accuracy, label="Train Accuracy", marker='o')
    ax[1].plot(epochs, test_accuracy, label="Test Accuracy", marker='o')
    ax[1].set_title("Accuracy", fontsize=14, fontweight='bold')
    ax[1].set_xlabel("Epochs")
    ax[1].set_ylabel("Accuracy")
    ax[1].legend()
    ax[1].grid(True, alpha=0.3)

    # Mark best epoch if available
    best_epoch = results.get("best_epoch")
    if best_epoch is not None:
        for a in ax:
            a.axvline(
                x=best_epoch + 1,
                color='green',
                linestyle='--',
                linewidth=2,
                label='Best Epoch',
                alpha=0.7
            )
        ax[0].legend()
        ax[1].legend()

    # Adjust layout
    fig.tight_layout(pad=2.0)

    return fig
