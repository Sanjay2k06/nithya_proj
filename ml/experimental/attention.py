"""Lightweight CBAM blocks for isolated fire/smoke model experiments."""

import torch
from torch import Tensor, nn


class ChannelAttention(nn.Module):
    def __init__(self, channels: int, reduction: int = 16) -> None:
        super().__init__()
        hidden_channels = max(1, channels // reduction)
        self.shared_mlp = nn.Sequential(
            nn.Conv2d(channels, hidden_channels, kernel_size=1, bias=False),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden_channels, channels, kernel_size=1, bias=False),
        )
        self.activation = nn.Sigmoid()

    def forward(self, features: Tensor) -> Tensor:
        average = torch.mean(features, dim=(2, 3), keepdim=True)
        maximum = torch.amax(features, dim=(2, 3), keepdim=True)
        weights = self.activation(self.shared_mlp(average) + self.shared_mlp(maximum))
        return features * weights


class SpatialAttention(nn.Module):
    def __init__(self, kernel_size: int = 7) -> None:
        super().__init__()
        if kernel_size not in (3, 7):
            raise ValueError("Spatial attention kernel size must be 3 or 7.")
        self.projection = nn.Conv2d(
            2,
            1,
            kernel_size=kernel_size,
            padding=kernel_size // 2,
            bias=False,
        )
        self.activation = nn.Sigmoid()

    def forward(self, features: Tensor) -> Tensor:
        average = torch.mean(features, dim=1, keepdim=True)
        maximum = torch.amax(features, dim=1, keepdim=True)
        weights = self.activation(self.projection(torch.cat((average, maximum), dim=1)))
        return features * weights


class CBAM(nn.Module):
    """Convolutional Block Attention Module for experimental model variants."""

    def __init__(self, channels: int, reduction: int = 16, kernel_size: int = 7) -> None:
        super().__init__()
        if channels < 1:
            raise ValueError("CBAM requires a positive channel count.")
        self.channel_attention = ChannelAttention(channels, reduction)
        self.spatial_attention = SpatialAttention(kernel_size)

    def forward(self, features: Tensor) -> Tensor:
        return self.spatial_attention(self.channel_attention(features))
