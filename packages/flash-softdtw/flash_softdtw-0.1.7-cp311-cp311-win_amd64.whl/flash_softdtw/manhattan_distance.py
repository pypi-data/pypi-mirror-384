import torch
from .flash_softdtw_pybind import calc_manhattan_distance as _calc_manhattan_distance
from .flash_softdtw_pybind import (
    calc_manhattan_distance_gradient as _calc_manhattan_distance_gradient,
)
from logging import getLogger

logger = getLogger(__name__)


def calc_manhattan_distance(
    input_signals: torch.Tensor,
    input_signal_lengths: list[int],
    ref_signal: torch.Tensor,
    distance_matrix: torch.Tensor | None = None,
):
    """
    CAlculating the Manhattan distance between a list of input signals and a reference signal.

    Args:
        input_signals (torch.Tensor): A 1D tensor containing concatenated input signals.
        input_signal_lengths (list[int]): List of lengths of each input signal.
        ref_signal (torch.Tensor): Reference signal, should be a 1D tensor.
        distance_matrix (torch.Tensor | None): Optional preallocated distance matrix. If None, a new matrix will be created.
    """
    logger.debug("Starting Manhattan distance calculation")

    # input_signals_concat, input_signal_lengths = concat_signals(input_signals)
    ref_signal_length = ref_signal.size(0)
    max_matrix_size = sum(input_signal_lengths) * ref_signal_length
    if distance_matrix is None:
        logger.debug(f"Creating a new distance matrix with size {max_matrix_size}")
        distance_matrix = torch.zeros(
            (max_matrix_size,), dtype=torch.float32, device=input_signals.device
        )
    else:
        if distance_matrix.device != input_signals.device:
            raise ValueError(
                "distance_matrix must be on the same device as input_signals"
            )
        if len(distance_matrix.shape) != 1:
            raise ValueError("distance_matrix must be a 1D tensor")
        if distance_matrix.size(0) < max_matrix_size:
            raise ValueError(
                f"distance_matrix must be at least of size {max_matrix_size}"
            )

    _calc_manhattan_distance(
        input_signals.data_ptr(),
        input_signal_lengths,
        ref_signal.data_ptr(),
        ref_signal_length,
        distance_matrix.data_ptr(),
    )

    return distance_matrix


def calc_manhattan_distance_gradient(
    input_signals: torch.Tensor,
    input_signal_lengths: list[int],
    ref_signal: torch.Tensor,
    gradient_matrix: torch.Tensor,
    input_signal_gradients: torch.Tensor | None = None,
    ref_signal_gradient: torch.Tensor | None = None,
):
    """
    Calculating the gradient of the Manhattan distance with respect to input signals and reference signal.

    Args:
        input_signals (torch.Tensor): A 1D tensor containing concatenated input signals.
        input_signal_lengths (list[int]): List of lengths of each input signal.
        ref_signal (torch.Tensor): Reference signal, should be a 1D tensor.
        distance_matrix (torch.Tensor): Matrix containing distances between input signals and the reference signal.
        gradient_matrix (torch.Tensor): Matrix to store gradients of the distance matrix.
        input_signal_gradients (torch.Tensor | None): Optional tensor to store gradients with respect to input signals. If None, a new tensor will be created.
        ref_signal_gradient (torch.Tensor | None): Optional tensor to store gradient with respect to the reference signal. If None, a new tensor will be created.

    """
    logger.debug("Starting Manhattan distance gradient calculation")

    ref_signal_length = ref_signal.size(0)
    if input_signal_gradients is None:
        input_signal_gradients = torch.zeros_like(
            input_signals, device=input_signals.device
        )
    if ref_signal_gradient is None:
        ref_signal_gradient = torch.zeros_like(ref_signal, device=ref_signal.device)

    _calc_manhattan_distance_gradient(
        input_signals.data_ptr(),
        input_signal_lengths,
        ref_signal.data_ptr(),
        ref_signal_length,
        gradient_matrix.data_ptr(),
        input_signal_gradients.data_ptr(),
        ref_signal_gradient.data_ptr(),
    )

    return input_signal_gradients, ref_signal_gradient
