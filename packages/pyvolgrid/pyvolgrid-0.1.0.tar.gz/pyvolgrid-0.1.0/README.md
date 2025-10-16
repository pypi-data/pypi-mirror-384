# PyVolGrid

**PyVolGrid** is a Python package for estimating the **total volume of overlapping spheres** using a **grid-based numerical approach**.
It is intended for applications in computational chemistry, molecular modeling, and structural bioinformatics.

(Besides its potential usefullness, this package also served as a learning project for me to get more familiar with Python packaging and distribution of precompiled wheels.)

---

## Installation

```bash
pip install pyvolgrid
```

Or clone the repository and install manually (requires a C++ compiler such as `clang` or `gcc`, and `cmake` to be installed):

```bash
git clone https://github.com/ugSUBMARINE/pyvolgrid.git
cd pyvolgrid
pip install .
```

---

## Usage

### Basic Example

```python
import numpy as np
from pyvolgrid import volume_from_spheres

# Define sphere centers and radii
coords = [[0, 0, 0], [1.5, 0, 0], [0, 1.5, 0]]
radii = [1.0, 0.8, 0.6]

# Calculate total volume
volume = volume_from_spheres(coords, radii, grid_spacing=0.1)
print(f"Total volume: {volume:.2f} cubic units")
```

### Scalar Radius

Apply the same radius to all spheres by passing a single number:

```python
# All spheres have radius 1.2
coords = [[0, 0, 0], [3, 0, 0], [0, 3, 0]]
radius = 1.2  # Single value for all spheres

volume = volume_from_spheres(coords, radius)
print(f"Volume with uniform radius: {volume:.2f}")
```

### Flexible Input Types

PyVolGrid accepts various input formats - lists, tuples, or numpy arrays:

```python
# Using tuples
coords = ((0, 0, 0), (2, 0, 0))
radii = (1.0, 0.5)
volume = volume_from_spheres(coords, radii)

# Using numpy arrays (any dtype, will be converted automatically)
coords = np.array([[0, 0, 0]], dtype=np.int32)
radius = np.float32(1.0)
volume = volume_from_spheres(coords, radius)

# Mixed types work too
coords = [[0, 0, 0]]  # List
radius = 1  # Integer (converted to float)
volume = volume_from_spheres(coords, radius)
```

### Performance Tips

```python
# For optimal performance, use C-contiguous float64 arrays
coords = np.array([[0, 0, 0], [2, 0, 0]], dtype=np.float64, order='C')
radii = np.array([1.0, 0.5], dtype=np.float64)

# No copying will occur, maximizing performance
volume = volume_from_spheres(coords, radii)
```

### Grid Spacing

Adjust the grid spacing to balance accuracy vs. performance:

```python
coords = [[0, 0, 0]]
radius = 1.0

# Coarse grid (faster, less accurate)
volume_coarse = volume_from_spheres(coords, radius, grid_spacing=0.2)

# Fine grid (slower, more accurate)
volume_fine = volume_from_spheres(coords, radius, grid_spacing=0.05)

print(f"Coarse: {volume_coarse:.2f}, Fine: {volume_fine:.2f}")
```

---

## License

This project is licensed under the MIT License.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request on GitHub.
