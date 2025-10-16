"""
ImageSlideViewer - An interactive image viewer for multidimensional numpy arrays.

This package provides a comprehensive image viewer with the following features:
- Navigate through image stacks with slider controls
- Support for complex arrays (magnitude, phase, real, imaginary)
- Contrast and brightness adjustment controls
- Multiple colormap options
- Keyboard shortcuts for navigation
- Compact, professional interface
"""

from .viewer import ImageSlideViewer

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    "ImageSlideViewer",
]


def image_slide(image_stack, title="Image Slide Viewer"):
    """
    Convenience function to quickly launch the image slide viewer.

    Parameters:
    -----------
    image_stack : numpy.ndarray
        3D or 4D numpy array where the first dimension is the image index
        Shape: (n_images, height, width) or (n_images, height, width, channels)
    title : str
        Window title

    Returns:
    --------
    None
        Opens the image viewer GUI

    Example:
    --------
    >>> import numpy as np
    >>> from image_slide_viewer import image_slide
    >>>
    >>> # Create test data
    >>> images = np.random.random((10, 100, 100))
    >>> image_slide(images, "My Images")
    """
    viewer = ImageSlideViewer(image_stack, title)
    viewer.run()
