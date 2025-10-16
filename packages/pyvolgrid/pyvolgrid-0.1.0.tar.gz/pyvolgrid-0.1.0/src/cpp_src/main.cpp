#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "volgrid.hpp"

namespace py = pybind11;

double calc_vol(
    py::array_t<double, py::array::c_style> coords, py::array_t<double, py::array::c_style> radii, double grid_spacing
) {
    py::buffer_info buf1 = coords.request();
    py::buffer_info buf2 = radii.request();

    // Validate array properties (C-contiguous arrays are enforced by template parameter)
    // Additional shape validation for extra safety
    // if (buf1.ndim != 2 || buf1.shape[1] != 3) {
    //     throw std::runtime_error("Coordinates array must be of shape (N, 3).");
    // }
    // if (buf2.ndim != 1 || buf2.shape[0] != buf1.shape[0]) {
    //     throw std::runtime_error("Radii array must be 1D and match number of coordinates.");
    // }

    // Verify C-contiguous layout by checking strides
    // For C-contiguous arrays, the last dimension should have stride equal to element size
    // and each previous dimension should have stride equal to (stride of next dim * size of next dim)
    // bool coords_contiguous = true;
    // if (buf1.strides[buf1.ndim-1] != sizeof(double)) {
    //     coords_contiguous = false;
    // }
    // for (int i = buf1.ndim - 2; i >= 0; --i) {
    //     if (buf1.strides[i] != buf1.strides[i+1] * buf1.shape[i+1]) {
    //         coords_contiguous = false;
    //         break;
    //     }
    // }
    // if (!coords_contiguous) {
    //     throw std::runtime_error("Coordinates array must be C-contiguous.");
    // }

    // if (buf2.strides[0] != sizeof(double)) {
    //     throw std::runtime_error("Radii array must be C-contiguous.");
    // }

    double* ptr_coords = static_cast<double*>(buf1.ptr);
    double* ptr_radii = static_cast<double*>(buf2.ptr);
    size_t n_spheres = buf1.shape[0];

    double volume = 0.0;
    {
        py::gil_scoped_release release;
        volume = volume_of_spheres(ptr_coords, ptr_radii, n_spheres, grid_spacing);
    }

    return volume;
}

PYBIND11_MODULE(_core, m) {
  m.doc() = "C++ extension for volume calculation using a grid-based approach";

  m.def("_volume_from_spheres", &calc_vol, R"pbdoc(
        Calculate the volume occupied by spheres using a grid-based approach.

        Args:
            coords: N x 3 array of sphere center coordinates (float64, C-contiguous)
            radii: 1D array of sphere radii (float64, length N, C-contiguous)
            grid_spacing: Grid spacing for the volume calculation (float64)

        Returns:
            float: Estimated volume occupied by the spheres

        Notes:
            Arrays must be C-contiguous and float64.
  )pbdoc",
  py::arg("coords").noconvert(), py::arg("radii").noconvert(), py::arg("grid_spacing")
  );
}
