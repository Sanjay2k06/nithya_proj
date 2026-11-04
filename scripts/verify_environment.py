"""
Environment and Dependency Verification Script.
"""

import sys
import platform
import torch
import torchvision
import cv2
import sklearn
import fastapi
import sqlalchemy
import pydantic


def verify() -> bool:
    print("=" * 60)
    print("ENVIRONMENT & DEPENDENCY VERIFICATION")
    print("=" * 60)
    print(f"Platform:           {platform.platform()}")
    print(f"Python Version:     {sys.version.split()[0]}")
    print(f"PyTorch Version:    {torch.__version__}")
    print(f"Torchvision:        {torchvision.__version__}")
    print(f"OpenCV Version:     {cv2.__version__}")
    print(f"Scikit-Learn:       {sklearn.__version__}")
    print(f"FastAPI Version:    {fastapi.__version__}")
    print(f"SQLAlchemy:         {sqlalchemy.__version__}")
    print(f"Pydantic Version:   {pydantic.__version__}")
    print(f"CUDA Available:     {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA Device Name:   {torch.cuda.get_device_name(0)}")
    print("=" * 60)
    print("[SUCCESS] All required dependencies successfully imported and verified.")
    return True


if __name__ == "__main__":
    verify()
