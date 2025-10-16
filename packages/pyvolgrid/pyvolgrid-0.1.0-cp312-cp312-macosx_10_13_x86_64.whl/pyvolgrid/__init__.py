from importlib.metadata import version, PackageNotFoundError

import numpy as np
from numpy.typing import ArrayLike
from pyvolgrid._core import _volume_from_spheres

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "0.0.0"


def volume_from_spheres(
    coords: ArrayLike,
    radii: ArrayLike | float,
    grid_spacing: float = 0.1,
) -> float:
    """Calculate the volume occupied by a set of spheres using a grid-based method.

    Parameters
    ----------
    coords : array-like
        An array-like object of shape (N, 3) containing the coordinates of the centers.
    radii : array-like or float
        An array-like object of shape (N,) containing the radii of the spheres.
        If a single float is provided, all spheres are assumed to have the same radius.
    grid_spacing : float, optional
        The spacing between grid points. Default is 0.1.

    Returns
    -------
    float
        The total volume occupied by the spheres.

    Notes
    -----
    If necessary, input arrays are automatically converted to C-contiguous float64 numpy arrays
    as required by the underlying C++ implementation.
    """

    # Handle and validate coords
    # If already a C-contiguous float64 array, np.ascontiguousarray returns it unchanged
    coords_array = np.ascontiguousarray(coords, dtype=np.float64)

    if coords_array.ndim != 2 or coords_array.shape[1] != 3:
        raise ValueError(
            f"coords must be convertible to shape (N, 3), got shape {coords_array.shape}"
        )
    if coords_array.shape[0] == 0:
        raise ValueError("coords must contain at least one coordinate")

    # Handle and validate radii
    if np.isscalar(radii):
        radii_array = np.full(coords_array.shape[0], radii, dtype=np.float64)
    else:
        radii_array = np.ascontiguousarray(radii, dtype=np.float64)

    if radii_array.ndim != 1:
        raise ValueError(
            f"radii must be convertible to shape (N,), got shape {radii_array.shape}"
        )
    if radii_array.shape[0] != coords_array.shape[0]:
        raise ValueError(
            f"Number of radii ({radii_array.shape[0]}) must match number of coordinates ({coords_array.shape[0]})"
        )

    # Validate grid spacing
    if grid_spacing <= 0.0:
        raise ValueError("grid_spacing must be greater than 0.0")

    # Call the C++ function with guaranteed C-contiguous float64 arrays
    return _volume_from_spheres(coords_array, radii_array, grid_spacing)


__all__ = ["__version__", "volume_from_spheres"]
