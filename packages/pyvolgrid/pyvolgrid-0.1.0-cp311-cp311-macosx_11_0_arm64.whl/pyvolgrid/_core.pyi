from typing import SupportsFloat

import numpy as np
from numpy.typing import NDArray

def _volume_from_spheres(
    coords: NDArray[np.float64], radii: NDArray[np.float64], grid_spacing: SupportsFloat
) -> float: ...
