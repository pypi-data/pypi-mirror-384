"""""" # start delvewheel patch
def _delvewheel_patch_1_11_2():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'flash_softdtw.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_11_2()
del _delvewheel_patch_1_11_2
# end delvewheel patch

from .softdtw import softdtw_forward, softdtw_backward
from .manhattan_distance import (
    calc_manhattan_distance,
    calc_manhattan_distance_gradient,
)
from .autograd import SoftDTWFunction
from .module import SoftDTWLoss
from .convert import (
    antidiag_to_square,
    square_to_antidiag,
    split_square_matrices,
    concat_square_matrices,
    visualize_antidiag_matrix,
)

__all__ = [
    "softdtw_forward",
    "softdtw_backward",
    "calc_manhattan_distance",
    "calc_manhattan_distance_gradient",
    "SoftDTWFunction",
    "SoftDTWLoss",
    "antidiag_to_square",
    "square_to_antidiag",
    "split_square_matrices",
    "concat_square_matrices",
    "visualize_antidiag_matrix",
]
