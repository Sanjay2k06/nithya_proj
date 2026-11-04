"""
Custom Domain Exceptions.
"""


class ModelNotLoadedException(Exception):
    """Raised when an inference is attempted but the model is unavailable and demo mode is disabled."""
    pass


class InvalidMediaException(Exception):
    """Raised when an uploaded image or video is corrupt or unreadable."""
    pass


class CameraStreamException(Exception):
    """Raised when a camera stream cannot be initialized or connection is lost."""
    pass
