"""
Callback functions for training control.
"""
import copy
import torch


class EarlyStopping:
    """Early stopping to prevent overfitting. Saves the best model weights during training.

    Args:
        patience (int): Number of epochs to wait for improvement before stopping.
        delta (float): Minimum change in monitored metric to qualify as improvement.
        verbose (bool): If True, prints messages when validation loss improves.

    Example:
        >>> early_stopping = EarlyStopping(patience=5, delta=0.01)
        >>> for epoch in range(num_epochs):
        >>>     train_loss = train_epoch(model, train_loader)
        >>>     val_loss = validate(model, val_loader)
        >>>     early_stopping(val_loss, model, epoch)
        >>>     if early_stopping.early_stop:
        >>>         break
        >>> early_stopping.load_best_model(model)
    """

    def __init__(self, patience: int = 5, delta: float = 0.01, verbose: bool = True):
        self.patience = patience
        self.delta = delta
        self.verbose = verbose
        self.best_score = None
        self.early_stop = False
        self.counter = 0
        self.best_model_state = None
        self.best_epoch = None

    def __call__(self, val_loss: float, model: torch.nn.Module, epoch: int):
        """Check if validation loss has improved.

        Args:
            val_loss (float): Current validation loss.
            model (torch.nn.Module): The model being trained.
            epoch (int): Current epoch number.
        """
        score = -val_loss

        if self.best_score is None:
            self.best_score = score
            self.best_model_state = model.state_dict()
            self.best_epoch = epoch
            if self.verbose:
                print(f"[EarlyStopping] Validation loss improved to {val_loss:.5f}")
        elif score < self.best_score + self.delta:
            self.counter += 1
            if self.verbose:
                print(f"[EarlyStopping] No improvement for {self.counter}/{self.patience} epochs")
            if self.counter >= self.patience:
                self.early_stop = True
                if self.verbose:
                    print("[EarlyStopping] Early stopping triggered")
                self.load_best_model(model)
                if self.verbose:
                    print(f"[EarlyStopping] Loaded best model from epoch {self.best_epoch}")
        else:
            if self.verbose:
                print(f"[EarlyStopping] Validation loss improved to {val_loss:.5f}")
            self.best_score = score
            self.best_model_state = model.state_dict()
            self.counter = 0
            self.best_epoch = epoch

    def load_best_model(self, model: torch.nn.Module):
        """Load the best model weights.

        Args:
            model (torch.nn.Module): The model to load weights into.
        """
        if self.best_model_state is not None:
            model.load_state_dict(self.best_model_state)
