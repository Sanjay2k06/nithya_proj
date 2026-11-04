"""
Training Loop and Optimization Pipeline for FireNetCNN.
"""

from typing import Dict, Any, Optional, Tuple
import time
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ml.config import ModelConfig, CLASS_NAMES
from ml.model import FireNetCNN
from ml.losses import get_loss_criterion
from ml.reproducibility import set_seed, get_device
from ml.checkpoints import save_checkpoint
from ml.metrics import compute_metrics


def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device
) -> Tuple[float, float]:
    """Executes single training epoch. Returns (avg_loss, accuracy)."""
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for images, labels in dataloader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

    epoch_loss = total_loss / max(total, 1)
    epoch_acc = correct / max(total, 1)
    return epoch_loss, epoch_acc


def validate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device
) -> Dict[str, Any]:
    """Evaluates model on validation dataloader. Returns metrics dictionary."""
    model.eval()
    total_loss = 0.0
    y_true = []
    y_pred = []

    with torch.no_grad():
        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            total_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)

            y_true.extend(labels.cpu().tolist())
            y_pred.extend(preds.cpu().tolist())

    total = len(y_true)
    val_loss = total_loss / max(total, 1)
    metrics = compute_metrics(y_true, y_pred, CLASS_NAMES)
    metrics["val_loss"] = val_loss
    return metrics


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    config: ModelConfig,
    save_path: str = "artifacts/checkpoints/firenet_best.pt"
) -> Dict[str, Any]:
    """
    Executes full training protocol with Cosine Annealing and early stopping.
    """
    set_seed(config.seed)
    device = get_device(config.device)
    model.to(device)

    criterion = get_loss_criterion(label_smoothing=config.label_smoothing, device=device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config.epochs)

    best_macro_f1 = -1.0
    patience_counter = 0
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_macro_f1": []}

    print(f"Starting training {config.model_name} on {device} for {config.epochs} epochs...")

    for epoch in range(1, config.epochs + 1):
        t0 = time.time()
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        val_metrics = validate(model, val_loader, criterion, device)
        scheduler.step()

        val_f1 = val_metrics["macro_f1"]
        elapsed = time.time() - t0

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_metrics["val_loss"])
        history["val_macro_f1"].append(val_f1)

        print(
            f"Epoch [{epoch}/{config.epochs}] ({elapsed:.1f}s) - "
            f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.3f} | "
            f"Val Loss: {val_metrics['val_loss']:.4f}, Val Macro-F1: {val_f1:.3f}"
        )

        if val_f1 > best_macro_f1:
            best_macro_f1 = val_f1
            patience_counter = 0
            save_checkpoint(
                model=model,
                save_path=save_path,
                optimizer=optimizer,
                epoch=epoch,
                metrics=val_metrics,
                config=config
            )
            print(f"[*] Checkpoint saved at {save_path} (Best Val Macro-F1: {best_macro_f1:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= config.early_stopping_patience:
                print(f"[!] Early stopping triggered at epoch {epoch}.")
                break

    return {"best_macro_f1": best_macro_f1, "history": history}
