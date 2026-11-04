"""
Grad-CAM (Gradient-weighted Class Activation Mapping) Implementation.
"""

from typing import Optional, Tuple
import numpy as np
import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F


class GradCAM:
    """
    Computes Grad-CAM heatmaps for arbitrary PyTorch convolutional layers
    to provide visual explanations of model decisions.
    """

    def __init__(self, model: nn.Module, target_layer: Optional[nn.Module] = None):
        self.model = model
        self.model.eval()

        if target_layer is None:
            if hasattr(model, "get_gradcam_target_layer"):
                self.target_layer = model.get_gradcam_target_layer()
            else:
                raise ValueError("Target layer must be specified if model does not implement get_gradcam_target_layer().")
        else:
            self.target_layer = target_layer

        self.activations: Optional[torch.Tensor] = None
        self.gradients: Optional[torch.Tensor] = None
        self._handles = []
        self._register_hooks()

    def _register_hooks(self) -> None:
        """Attaches forward and backward hooks to the target convolutional layer."""
        def forward_hook(module, input, output):
            self.activations = output

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0]

        self._handles.append(self.target_layer.register_forward_hook(forward_hook))
        self._handles.append(self.target_layer.register_full_backward_hook(backward_hook))

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        target_class_idx: Optional[int] = None
    ) -> np.ndarray:
        """
        Generates normalized 2D Grad-CAM heatmap array in range [0, 1].

        Args:
            input_tensor: Preprocessed tensor of shape (1, 3, H, W).
            target_class_idx: Class index to explain. If None, uses top predicted class.

        Returns:
            2D numpy array of shape (H, W) with values in [0, 1].
        """
        self.model.zero_grad()
        logits = self.model(input_tensor)

        if target_class_idx is None:
            target_class_idx = int(torch.argmax(logits, dim=1).item())

        score = logits[0, target_class_idx]
        score.backward(retain_graph=True)

        if self.gradients is None or self.activations is None:
            # Fallback uniform heatmap if gradients failed
            return np.zeros((input_tensor.shape[2], input_tensor.shape[3]), dtype=np.float32)

        # Global average pooling of gradients
        gradients = self.gradients.detach()
        activations = self.activations.detach()

        # Channel-wise alpha weights: shape (1, C, 1, 1)
        weights = torch.mean(gradients, dim=(2, 3), keepdim=True)

        # Weighted combination of activation maps
        cam = torch.sum(weights * activations, dim=1, keepdim=True)

        # Apply ReLU to keep only features that positively correlate with class
        cam = F.relu(cam)

        # Interpolate to input tensor spatial dimensions
        cam = F.interpolate(
            cam,
            size=(input_tensor.shape[2], input_tensor.shape[3]),
            mode="bilinear",
            align_corners=False
        )

        cam_np = cam.squeeze().cpu().numpy()

        # Min-max normalization
        cam_min, cam_max = cam_np.min(), cam_np.max()
        if cam_max - cam_min > 1e-8:
            cam_np = (cam_np - cam_min) / (cam_max - cam_min)
        else:
            cam_np = np.zeros_like(cam_np)

        return cam_np.astype(np.float32)

    @staticmethod
    def overlay_heatmap(
        original_image_bgr: np.ndarray,
        heatmap: np.ndarray,
        alpha: float = 0.5,
        colormap: int = cv2.COLORMAP_JET
    ) -> np.ndarray:
        """
        Overlays 2D Grad-CAM heatmap onto original BGR image.

        Args:
            original_image_bgr: OpenCV BGR image of shape (H, W, 3).
            heatmap: 2D float array in range [0, 1].
            alpha: Opacity blending factor.
            colormap: OpenCV colormap constant.

        Returns:
            Blended BGR image of shape (H, W, 3).
        """
        h, w = original_image_bgr.shape[:2]
        resized_heatmap = cv2.resize(heatmap, (w, h), interpolation=cv2.INTER_LINEAR)
        heatmap_uint8 = np.uint8(255 * np.clip(resized_heatmap, 0, 1))

        colored_heatmap = cv2.applyColorMap(heatmap_uint8, colormap)
        blended = cv2.addWeighted(colored_heatmap, alpha, original_image_bgr, 1 - alpha, 0)
        return blended

    def close(self) -> None:
        """Removes registered PyTorch hooks to prevent memory leaks."""
        for handle in self._handles:
            handle.remove()
        self._handles.clear()

    def __del__(self):
        self.close()
