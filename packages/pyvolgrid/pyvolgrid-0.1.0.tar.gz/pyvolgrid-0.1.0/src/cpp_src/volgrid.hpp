#ifndef VOLGRID_HPP
#define VOLGRID_HPP

#include <cstddef>

// Define a struct to hold 3D coordinates
struct TRd {
    double x, y, z;
};

// Define a struct to hold 3D integer coordinates or indexes
struct TRi {
    int x, y, z;
};

// Function declarations
// Calculate the volume occupied by spheres using a grid-based approach
double volume_of_spheres(const double* coords, const double* radii, size_t& n_spheres, double& grid_spacing);

// Get the maximum value from an array of doubles
double get_max(const double* array, size_t& n);

// Calculate grid parameters: extent and origin
void get_grid_params(
    const double* coords, const size_t& n, const double& cushion, const double& grid_spacing,
    TRi& extent, TRd& origin
);

// Get the extent (min and max coordinates) from a list of 3D coordinates
void get_extent(const double* coords, const size_t& n_coords, TRd& min_coords, TRd& max_coords);

#endif
