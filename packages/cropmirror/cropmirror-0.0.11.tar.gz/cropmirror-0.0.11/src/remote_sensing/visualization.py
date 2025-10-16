"""Visualization functions for agricultural data."""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
from typing import Dict, Tuple

from .constants import BAND_NAMES


# Set Chinese font support
if platform.system() == 'Windows':
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
elif platform.system() == 'Darwin':
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
else:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

plt.rcParams['font.size'] = 12


def display_bands(data: np.ndarray, band_names: list, window_title: str = "Image Display") -> None:
    """Display multi-band image data or 2D matrix.
    
    Args:
        data: Image data (2D or 3D array).
        band_names: List of band names or single name.
        window_title: Window title.
    """
    # Handle 2D data
    if len(data.shape) == 2:
        fig = plt.figure(figsize=(6, 6))
        fig.canvas.manager.set_window_title(window_title)
        plt.imshow(data, cmap='rainbow')
        plt.title(band_names if isinstance(band_names, str) else band_names[0])
        plt.colorbar()
        plt.show(block=False)
    else:
        # Handle multi-band data
        n_bands = data.shape[0]
        assert n_bands == len(band_names), "Band names list length must match number of bands"
        
        # Calculate rows and columns (max 4 columns per row)
        n_cols = min(n_bands, 4)
        n_rows = (n_bands + n_cols - 1) // n_cols
        
        # Create subplots
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 4 * n_rows))
        fig.canvas.manager.set_window_title(window_title)
        
        # Ensure axes is 2D
        axes = np.atleast_2d(axes)

        # Display each band
        for i in range(n_bands):
            row = i // n_cols
            col = i % n_cols
            ax = axes[row, col]
            
            im = ax.imshow(data[i, :, :], cmap='rainbow')
            ax.set_title(band_names[i])
            fig.colorbar(im, ax=ax)

        # Hide extra subplots
        for j in range(n_bands, n_rows * n_cols):
            fig.delaxes(axes[j // n_cols, j % n_cols])

        plt.tight_layout()
        plt.show(block=False)


def display_results_group(
    results_dict: Dict[str, Tuple[np.ndarray, str]],
    window_title: str,
    ncols: int = 3
) -> None:
    """Display multiple result matrices in one figure.
    
    Args:
        results_dict: Dictionary with {name: (data, display_name)} pairs.
        window_title: Window title.
        ncols: Number of subplots per row.
    """
    n_plots = len(results_dict)
    nrows = (n_plots + ncols - 1) // ncols
    
    fig, axes = plt.subplots(nrows, ncols, figsize=(6*ncols, 5*nrows))
    fig.canvas.manager.set_window_title(window_title)
    
    # Ensure axes is 2D
    axes = np.atleast_2d(axes)
    
    for idx, (name, (data, display_name)) in enumerate(results_dict.items()):
        row = idx // ncols
        col = idx % ncols
        ax = axes[row, col]
        
        im = ax.imshow(data, cmap='rainbow')
        ax.set_title(display_name)
        fig.colorbar(im, ax=ax)
    
    # Hide extra subplots
    for idx in range(n_plots, nrows * ncols):
        fig.delaxes(axes[idx // ncols, idx % ncols])
    
    plt.tight_layout()
    plt.show(block=True)


def plot_all_indices(indices_dict: Dict[str, Tuple[np.ndarray, str]]) -> None:
    """Plot all indices final processing results.
    
    Args:
        indices_dict: Dictionary with index name as key, (data, title) as value.
    """
    n_indices = len(indices_dict)
    n_cols = 3
    n_rows = (n_indices + n_cols - 1) // n_cols
    
    plt.figure(figsize=(15, 5 * n_rows))
    
    for idx, (name, (data, title)) in enumerate(indices_dict.items()):
        plt.subplot(n_rows, n_cols, idx + 1)
        
        # Create masked array to handle NaN values
        masked_data = np.ma.masked_invalid(data)
        
        # Use RdYlBu_r colormap
        im = plt.imshow(masked_data, cmap='RdYlBu_r')
        plt.colorbar(im, label=title)
        plt.title(name)
        plt.axis('off')
    
    plt.tight_layout()
    plt.show()

