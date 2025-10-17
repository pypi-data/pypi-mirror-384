"""
Basic training example using PyTorch Essentials.

This example demonstrates how to:
1. Load a configuration file
2. Set up a model, optimizer, and data loaders
3. Train with early stopping
4. Evaluate and visualize results
"""
import sys
from pathlib import Path

# Add parent directory to path to import pytorch_essentials
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from pytorch_essentials import (
    train,
    evaluate_model,
    get_device,
    EarlyStopping,
    save_model,
    plot_loss_curves,
    load_config,
    print_config,
    set_seeds,
    count_parameters,
)


def get_data_loaders(batch_size: int, use_subset: bool = False):
    """Create train and validation data loaders for MNIST.

    Args:
        batch_size: Batch size for data loaders.
        use_subset: If True, use a small subset for quick testing.

    Returns:
        tuple: (train_loader, val_loader)
    """
    # Define transforms
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    # Download and load training data
    train_dataset = datasets.MNIST(
        root='./data',
        train=True,
        download=True,
        transform=transform
    )

    # Download and load test data
    test_dataset = datasets.MNIST(
        root='./data',
        train=False,
        download=True,
        transform=transform
    )

    # Use subset for quick testing
    if use_subset:
        train_dataset = torch.utils.data.Subset(train_dataset, range(1000))
        test_dataset = torch.utils.data.Subset(test_dataset, range(200))

    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader


class SimpleCNN(nn.Module):
    """Simple CNN for MNIST classification."""

    def __init__(self, num_classes: int = 10):
        super(SimpleCNN, self).__init__()
        self.model_name = "SimpleCNN"

        self.features = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 7 * 7, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


def main():
    """Main training function."""
    # Set seeds for reproducibility
    set_seeds(42)

    # Load configuration
    config = load_config(config_path='config.yaml')

    # Extract parameters
    DEBUG = config['flags']['debug']
    EPOCHS = config['hyperparameters']['epochs']
    BATCH_SIZE = config['hyperparameters']['batch_size']
    LEARNING_RATE = float(config['hyperparameters']['learning_rate'])
    USE_SUBSET = config['flags']['use_subset']
    SAVE_MODEL_FLAG = config['flags']['save_model']

    if DEBUG:
        print_config(config)

    # Get device
    device = get_device()
    if DEBUG:
        print(f"[INFO] Training on device: {device}")

    # Create data loaders
    print("[INFO] Loading data...")
    train_loader, val_loader = get_data_loaders(BATCH_SIZE, USE_SUBSET)

    # Create model
    model = SimpleCNN(num_classes=10)
    count_parameters(model)

    # Define loss function and optimizer
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)

    # Optional: Learning rate scheduler
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=3
    )

    # Optional: Early stopping
    early_stopping = EarlyStopping(patience=5, delta=0.001, verbose=True)

    # Train the model
    print(f"\n[INFO] Starting training for {EPOCHS} epochs...")
    results = train(
        model=model,
        train_dataloader=train_loader,
        val_dataloader=val_loader,
        optimizer=optimizer,
        loss_fn=loss_fn,
        num_epochs=EPOCHS,
        device=device,
        config=config,
        early_stopping=early_stopping,
        scheduler=scheduler
    )

    # Plot and save results
    print("\n[INFO] Training complete!")
    print(f"Best epoch: {results['best_epoch']}")
    print(f"Final train loss: {results['train_loss'][-1]:.4f}")
    print(f"Final val loss: {results['test_loss'][-1]:.4f}")

    # Create loss curves
    fig = plot_loss_curves(results)
    fig.savefig('training_curves.png')
    print("[INFO] Saved training curves to 'training_curves.png'")

    # Save model if requested
    if SAVE_MODEL_FLAG:
        save_model(
            model=model,
            fig=fig,
            results=results,
            save_path="mnist_experiment"
        )

    # Evaluate on test set
    print("\n[INFO] Evaluating model on test set...")
    class_names = [str(i) for i in range(10)]
    evaluate_model(
        model=model,
        test_dataloader=val_loader,
        loss_fn=loss_fn,
        device=device,
        class_names=class_names,
        log_to_wandb=config['flags']['use_wandb']
    )

    # Finish wandb run if it was used
    if config['flags']['use_wandb']:
        import wandb
        wandb.finish()


if __name__ == "__main__":
    main()
