from .flash_softdtw_pybind import calc_softdtw_forward, calc_softdtw_backward
import torch
from logging import getLogger

logger = getLogger(__name__)


def softdtw_forward(
    input_signal_lengths: list[int],
    ref_signal_length: int,
    distance_matrix: torch.Tensor,
    score_matrix: torch.Tensor | None = None,
    gamma: float = 1.0,
):
    """
    Calculating the forward pass of the softDTW algorithm.

    Args:
        input_signal_lengths (list[int]): Lengths of the input signals.
        ref_signal_length (int): Length of the reference signal.
        distance_matrix (torch.Tensor): Matrix containing distances between input signals and the reference signal.
        score_matrix (torch.Tensor | None): Optional matrix to store scores. If None, a new matrix will be created.
    """
    logger.debug("Starting softDTW forward pass")
    device = distance_matrix.device
    logger.debug(f"Device: {device}")
    if device.type != "cuda":
        raise ValueError("softDTW is only supported on CUDA devices.")
    scores = torch.zeros(
        (len(input_signal_lengths),), device=device, dtype=torch.float32
    )

    # required size for score matrix is input_signal_lengths * ref_signal_length
    min_matrix_size = sum(input_signal_lengths) * ref_signal_length
    if score_matrix is None:
        logger.debug(
            "score_matrix is None, creating a new score matrix with size %d",
            min_matrix_size,
        )
        score_matrix = torch.zeros(
            (min_matrix_size,), device=device, dtype=torch.float32
        )
    else:
        # validate the score_matrix
        if score_matrix.device != device:
            raise ValueError(
                "score_matrix must be on the same device as distance_matrix"
            )
        if len(score_matrix.shape) != 1:
            raise ValueError(
                "score_matrix must be a 1D tensor with size equal to input_signal_lengths * ref_signal_length"
            )
        if score_matrix.size(0) < min_matrix_size:
            raise ValueError(
                "score_matrix must be at least of size input_signal_lengths * ref_signal_length"
            )

    calc_softdtw_forward(
        input_signal_lengths,
        ref_signal_length,
        distance_matrix.data_ptr(),
        score_matrix.data_ptr(),
        scores.data_ptr(),
        gamma,
    )

    return scores, score_matrix[:min_matrix_size]


def softdtw_backward(
    input_signal_lengths: list[int],
    ref_signal_length: int,
    distance_matrix: torch.Tensor,
    score_matrix: torch.Tensor,
    gradient_matrix: torch.Tensor | None = None,
    gamma: float = 1.0,
):
    """
    Calculating the backward pass of the soft DTW algorithm.

    Args:
        input_signal_lengths (list[int]): Lengths of the input signals.
        ref_signal_length (int): Length of the reference signal.
        distance_matrix (torch.Tensor): Matrix containing distances between input signals and the reference signal.
        score_matrix (torch.Tensor): Matrix containing scores from the forward pass.
        gradient_matrix (torch.Tensor | None): Optional matrix to store gradients. If None, a new matrix will be created.
    """
    logger.debug("Starting softDTW backward pass")
    device = distance_matrix.device
    logger.debug(f"Device: {device}")
    if device.type != "cuda":
        raise ValueError("softDTW is only supported on CUDA devices.")

    min_matrix_size = sum(input_signal_lengths) * ref_signal_length
    if gradient_matrix is None:
        logger.debug(
            "gradient_matrix is None, creating a new gradient matrix with size %d",
            min_matrix_size,
        )
        gradient_matrix = torch.zeros(
            (min_matrix_size,), device=device, dtype=torch.float32
        )
    else:
        if gradient_matrix.device != device:
            raise ValueError(
                "gradient_matrix must be on the same device as distance_matrix"
            )
        if len(gradient_matrix.shape) != 1:
            raise ValueError(
                "gradient_matrix must be a 1D tensor with size equal to input_signal_lengths * ref_signal_length"
            )
        if gradient_matrix.size(0) < min_matrix_size:
            raise ValueError(
                "gradient_matrix must be at least of size input_signal_lengths * ref_signal_length"
            )

    calc_softdtw_backward(
        input_signal_lengths,
        ref_signal_length,
        distance_matrix.data_ptr(),
        score_matrix.data_ptr(),
        gradient_matrix.data_ptr(),
        gamma,
    )

    return gradient_matrix[:min_matrix_size]
