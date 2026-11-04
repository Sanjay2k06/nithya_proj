"""
FireNetCNN Model Architecture and Baseline Constructors.
"""

from typing import Dict, Any, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models

from ml.config import NUM_CLASSES


class FireNetCNN(nn.Module):
    """
    FireNet-inspired compact Convolutional Neural Network for real-time
    3-class forest fire, smoke, and normal scene classification.
    """

    def __init__(self, num_classes: int = NUM_CLASSES, dropout_rate: float = 0.3):
        super(FireNetCNN, self).__init__()
        self.num_classes = num_classes

        # Feature Extraction Backbone
        self.features = nn.Sequential(
            # Block 1: 3 -> 16 channels (224x224 -> 112x112)
            nn.Sequential(
                nn.Conv2d(3, 16, kernel_size=3, stride=1, padding=1, bias=False),
                nn.BatchNorm2d(16),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=2, stride=2)
            ),
            # Block 2: 16 -> 32 channels (112x112 -> 56x56)
            nn.Sequential(
                nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=1, bias=False),
                nn.BatchNorm2d(32),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=2, stride=2)
            ),
            # Block 3: 32 -> 64 channels (56x56 -> 28x28)
            nn.Sequential(
                nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1, bias=False),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=2, stride=2)
            ),
            # Block 4: 64 -> 128 channels (28x28 -> 14x14) - Target for Grad-CAM
            nn.Sequential(
                nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1, bias=False),
                nn.BatchNorm2d(128),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=2, stride=2)
            )
        )

        # Global Pooling and Classification Head
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate),
            nn.Linear(64, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass returning raw uncalibrated logits."""
        features = self.features(x)
        pooled = self.avgpool(features)
        logits = self.classifier(pooled)
        return logits

    def predict_probabilities(self, x: torch.Tensor) -> torch.Tensor:
        """Returns softmax-calibrated class probabilities."""
        logits = self.forward(x)
        return F.softmax(logits, dim=1)

    def get_gradcam_target_layer(self) -> nn.Module:
        """Returns the penultimate convolutional layer reference used for Grad-CAM."""
        return self.features[3][0]

    def count_parameters(self) -> int:
        """Returns total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


def create_baseline_model(
    model_name: str = "mobilenet_v3_small",
    num_classes: int = NUM_CLASSES,
    pretrained: bool = False
) -> nn.Module:
    """
    Constructs baseline comparative architectures (ResNet18, MobileNetV3-Small)
    for experimental benchmarking.
    """
    model_name = model_name.lower()
    if model_name == "firenet":
        return FireNetCNN(num_classes=num_classes)
    elif model_name == "mobilenet_v3_small":
        weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
        model = models.mobilenet_v3_small(weights=weights)
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_features, num_classes)
        return model
    elif model_name == "resnet18":
        weights = models.ResNet18_Weights.DEFAULT if pretrained else None
        model = models.resnet18(weights=weights)
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)
        return model
    else:
        raise ValueError(f"Unsupported baseline architecture '{model_name}'. Choose 'firenet', 'mobilenet_v3_small', or 'resnet18'.")
