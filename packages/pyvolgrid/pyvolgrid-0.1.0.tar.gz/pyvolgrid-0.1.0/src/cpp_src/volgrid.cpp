#include "volgrid.hpp"
#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <limits>
#include <cmath>
#include <algorithm>

double volume_of_spheres(const double* coords, const double* radii, size_t& n_spheres, double& grid_spacing)
{
    // calculate origin and extent of the grid
    TRi extent;
    TRd origin;
    double cushion = grid_spacing + get_max(radii, n_spheres);
    get_grid_params(coords, n_spheres, cushion, grid_spacing, extent, origin);

    // allocate memory for the grid and initialize with zeroes
    int8_t* grid = nullptr;
    size_t n_points = 0;
    try {
        n_points = static_cast<size_t>(extent.x * extent.y * extent.z);
        grid = new int8_t[n_points];
        std::fill(grid, grid + n_points, 0);
    }
    catch (const std::bad_alloc&) {
        throw std::runtime_error("Memory allocation failed for the grid.");
    }

    // loop over all spheres and mark the grid points inside the spheres
    int points_in_spheres = 0;
    for (size_t i = 0; i < n_spheres; ++i) {
        // radius in grid units
        double radius = radii[i] / grid_spacing;
        double radius_squared = radius * radius;

        // center of the sphere in grid units
        // assuming coords is a flat array [x1, y1, z1, x2, y2, z2, ...]
        size_t c_index = 3 * i;
        double cx = (coords[c_index] - origin.x) / grid_spacing;
        double cy = (coords[c_index + 1] - origin.y) / grid_spacing;
        double cz = (coords[c_index + 2] - origin.z) / grid_spacing;

        // determine the bounding box of the sphere in grid coordinates
        size_t x_min = std::max(static_cast<int>(std::floor(cx - radius)), 0);
        size_t x_max = std::min(static_cast<int>(std::ceil(cx + radius)), extent.x);
        size_t y_min = std::max(static_cast<int>(std::floor(cy - radius)), 0);
        size_t y_max = std::min(static_cast<int>(std::ceil(cy + radius)), extent.y);
        size_t z_min = std::max(static_cast<int>(std::floor(cz - radius)), 0);
        size_t z_max = std::min(static_cast<int>(std::ceil(cz + radius)), extent.z);

        // iterate over the bounding box and mark points inside the sphere
        for (size_t x = x_min; x < x_max; ++x) {
            for (size_t y = y_min; y < y_max; ++y) {
                for (size_t z = z_min; z < z_max; ++z) {
                    // calculate the 1D index for the 3D grid point (x, y, z)
                    size_t index = x * extent.y * extent.z + y * extent.z + z;

                    // skip already processed points
                    if (grid[index] == 1) continue;

                    // check if the point is inside the sphere
                    double dx = (x - cx);
                    double dy = (y - cy);
                    double dz = (z - cz);
                    if ((dx * dx + dy * dy + dz * dz) <= radius_squared) {
                        grid[index] = 1;
                        points_in_spheres++;
                    }
                }
            }
        }
    }

    // calculate the total volume
    double total_volume = points_in_spheres * (grid_spacing * grid_spacing * grid_spacing);

    // release grid memory at the end of the function
    delete[] grid;

    return total_volume;
}

double get_max(const double* array, size_t& n)
{
    if (n == 0) {
        throw std::invalid_argument("Cannot find the maximum of an empty array.");
    }

    double max_val = -std::numeric_limits<double>::infinity();
    for (size_t i = 0; i < n; ++i) {
        // assume array is a flat array
        if (array[i] > max_val) {
            max_val = array[i];
        }
    }
    return max_val;
}

void get_grid_params(
    const double* coords, const size_t& n_coords, const double& cushion, const double& grid_spacing,
    TRi& extent, TRd& origin
)
{
    // extent of coordinates in cartesian
    TRd min_coords, max_coords;
    get_extent(coords, n_coords, min_coords, max_coords);

     // calculate extent in grid units
    int a_min = static_cast<int>(floor((min_coords.x - cushion) / grid_spacing));
    int a_max = static_cast<int>(ceil((max_coords.x + cushion) / grid_spacing));
    int b_min = static_cast<int>(floor((min_coords.y - cushion) / grid_spacing));
    int b_max = static_cast<int>(ceil((max_coords.y + cushion) / grid_spacing));
    int c_min = static_cast<int>(floor((min_coords.z - cushion) / grid_spacing));
    int c_max = static_cast<int>(ceil((max_coords.z + cushion) / grid_spacing));

    // number of grid points and origin of the grid
    extent = {a_max - a_min + 1, b_max - b_min + 1, c_max - c_min + 1};
    origin = {a_min * grid_spacing, b_min * grid_spacing, c_min * grid_spacing};
}

void get_extent(const double* coords, const size_t& n_coords, TRd& min_coords, TRd& max_coords)
{
    if (n_coords == 0) {
        throw std::invalid_argument("Cannot determine min/max of an empty array.");
    }

    min_coords.x = min_coords.y = min_coords.z = std::numeric_limits<double>::infinity();
    max_coords.x = max_coords.y = max_coords.z = -std::numeric_limits<double>::infinity();

    for (size_t i = 0; i < n_coords; ++i) {
        // assume coords is a flat array [x1, y1, z1, x2, y2, z2, ...]
        double x = coords[3 * i];
        double y = coords[3 * i + 1];
        double z = coords[3 * i + 2];

        if (x < min_coords.x) min_coords.x = x;
        if (y < min_coords.y) min_coords.y = y;
        if (z < min_coords.z) min_coords.z = z;

        if (x > max_coords.x) max_coords.x = x;
        if (y > max_coords.y) max_coords.y = y;
        if (z > max_coords.z) max_coords.z = z;
    }
}
