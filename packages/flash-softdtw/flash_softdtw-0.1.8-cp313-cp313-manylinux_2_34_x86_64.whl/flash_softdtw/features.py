"""
Wrapper functions for weighted statistics calculations using normalized gradient matrices.
"""

from typing import List, Dict
import torch
from flash_softdtw import flash_softdtw_pybind as bind


def normalize_gradient_matrix(
    gradient_matrix: torch.Tensor,
    input_signal_lengths: List[int],
    ref_signal_length: int,
) -> torch.Tensor:
    """
    Normalize the gradient matrix by dividing each element by the sum of
    gradients for each reference position.

    Args:
        gradient_matrix: Gradient matrix in anti-diagonal format.
            Must be on CUDA and contiguous.
        input_signal_lengths: List of lengths for each input signal.
        ref_signal_length: Length of the reference signal.

    Returns:
        torch.Tensor: Normalized gradient matrix (modified in-place).

    Example:
        >>> gradient = torch.rand(180, device='cuda')  # For signals [10, 15, 5] x ref_len 6
        >>> normalized = normalize_gradient_matrix(gradient, [10, 15, 5], 6)
        >>> # Each column now sums to 1
    """
    # Validate inputs
    if not gradient_matrix.is_cuda:
        raise ValueError("Gradient matrix must be on CUDA device")
    if not gradient_matrix.is_contiguous():
        gradient_matrix = gradient_matrix.contiguous()

    # Calculate expected size
    expected_size = sum(length * ref_signal_length for length in input_signal_lengths)
    if gradient_matrix.numel() != expected_size:
        raise ValueError(
            f"Matrix size {gradient_matrix.numel()} doesn't match expected size {expected_size}"
        )

    # Create temporary storage for ref_total_grads
    num_signals = len(input_signal_lengths)
    ref_total_grads = torch.zeros(
        num_signals * ref_signal_length, device="cuda", dtype=torch.float32
    )

    # Normalize in-place
    bind.normalize_matrix(
        input_signal_lengths=input_signal_lengths,
        ref_signal_length=ref_signal_length,
        gradient_matrix_ptr=gradient_matrix.data_ptr(),
        ref_total_grads_ptr=ref_total_grads.data_ptr(),
    )

    return gradient_matrix


def calculate_weighted_means(
    input_signals: torch.Tensor,
    gradient_matrix: torch.Tensor,
    input_signal_lengths: List[int],
    ref_signal_length: int,
) -> torch.Tensor:
    """
    Calculate weighted means of input signals using the normalized
    gradient matrix as weights.

    Args:
        input_signals: Concatenated input signals. Must be on CUDA.
        gradient_matrix: Normalized gradient matrix in anti-diagonal format.
            Must be on CUDA and contiguous.
        input_signal_lengths: List of lengths for each input signal.
        ref_signal_length: Length of the reference signal.

    Returns:
        torch.Tensor: Weighted means of shape (num_signals * ref_signal_length).

    Example:
        >>> signals = torch.randn(30, device='cuda')  # [10, 15, 5] concatenated
        >>> gradient = normalize_gradient_matrix(gradient, [10, 15, 5], 6)
        >>> means = calculate_weighted_means(signals, gradient, [10, 15, 5], 6)
        >>> # means.shape = (3 * 6,) = (18,)
    """
    # Validate inputs
    if not input_signals.is_cuda or not gradient_matrix.is_cuda:
        raise ValueError("All tensors must be on CUDA device")
    if not input_signals.is_contiguous():
        input_signals = input_signals.contiguous()
    if not gradient_matrix.is_contiguous():
        gradient_matrix = gradient_matrix.contiguous()

    # Check sizes
    total_signal_length = sum(input_signal_lengths)
    if input_signals.numel() != total_signal_length:
        raise ValueError(
            f"Input signals size {input_signals.numel()} doesn't match "
            f"expected size {total_signal_length}"
        )

    # Create output tensor
    num_signals = len(input_signal_lengths)
    weighted_means = torch.zeros(
        num_signals * ref_signal_length, device="cuda", dtype=torch.float32
    )

    # Calculate weighted means
    bind.calc_weighted_means(
        input_signal_ptr=input_signals.data_ptr(),
        input_signal_lengths=input_signal_lengths,
        ref_signal_length=ref_signal_length,
        gradient_matrix_ptr=gradient_matrix.data_ptr(),
        weighted_means_ptr=weighted_means.data_ptr(),
    )

    return weighted_means


def calculate_weighted_std(
    input_signals: torch.Tensor,
    gradient_matrix: torch.Tensor,
    weighted_means: torch.Tensor,
    input_signal_lengths: List[int],
    ref_signal_length: int,
) -> torch.Tensor:
    """
    Calculate weighted standard deviation (in log scale) of input signals
    using the normalized gradient matrix as weights.

    Args:
        input_signals: Concatenated input signals. Must be on CUDA.
        gradient_matrix: Normalized gradient matrix in anti-diagonal format.
            Must be on CUDA and contiguous.
        weighted_means: Precomputed weighted means from calculate_weighted_means.
            Must be on CUDA.
        input_signal_lengths: List of lengths for each input signal.
        ref_signal_length: Length of the reference signal.

    Returns:
        torch.Tensor: Log-scale weighted standard deviations, clamped to [-10, 10].

    Example:
        >>> signals = torch.randn(30, device='cuda')
        >>> gradient = normalize_gradient_matrix(gradient, [10, 15, 5], 6)
        >>> means = calculate_weighted_means(signals, gradient, [10, 15, 5], 6)
        >>> stds_log = calculate_weighted_std(signals, gradient, means, [10, 15, 5], 6)
        >>> stds = torch.exp(stds_log)  # Convert back from log scale
    """
    # Validate inputs
    if not all(t.is_cuda for t in [input_signals, gradient_matrix, weighted_means]):
        raise ValueError("All tensors must be on CUDA device")
    if not input_signals.is_contiguous():
        input_signals = input_signals.contiguous()
    if not gradient_matrix.is_contiguous():
        gradient_matrix = gradient_matrix.contiguous()
    if not weighted_means.is_contiguous():
        weighted_means = weighted_means.contiguous()

    # Create output tensor
    num_signals = len(input_signal_lengths)
    weighted_std_log = torch.zeros(
        num_signals * ref_signal_length, device="cuda", dtype=torch.float32
    )

    # Calculate weighted std
    bind.calc_weighted_std(
        input_signal_ptr=input_signals.data_ptr(),
        input_signal_lengths=input_signal_lengths,
        ref_signal_length=ref_signal_length,
        gradient_matrix_ptr=gradient_matrix.data_ptr(),
        weighted_means_ptr=weighted_means.data_ptr(),
        weighted_std_log_ptr=weighted_std_log.data_ptr(),
    )

    return weighted_std_log


def calculate_weighted_index_std(
    gradient_matrix: torch.Tensor,
    input_signal_lengths: List[int],
    ref_signal_length: int,
) -> torch.Tensor:
    """
    Calculate weighted standard deviation (in log scale) of index positions
    using the normalized gradient matrix as weights.

    Args:
        gradient_matrix: Normalized gradient matrix in anti-diagonal format.
            Must be on CUDA and contiguous.
        input_signal_lengths: List of lengths for each input signal.
        ref_signal_length: Length of the reference signal.

    Returns:
        torch.Tensor: Log-scale weighted index standard deviations, clamped to [-10, 10].

    Example:
        >>> gradient = normalize_gradient_matrix(gradient, [10, 15, 5], 6)
        >>> index_stds_log = calculate_weighted_index_std(gradient, [10, 15, 5], 6)
        >>> # Measures how spread out the alignment is
    """
    # Validate inputs
    if not gradient_matrix.is_cuda:
        raise ValueError("Gradient matrix must be on CUDA device")
    if not gradient_matrix.is_contiguous():
        gradient_matrix = gradient_matrix.contiguous()

    # Create output tensor
    num_signals = len(input_signal_lengths)
    weighted_index_std_log = torch.zeros(
        num_signals * ref_signal_length, device="cuda", dtype=torch.float32
    )

    # Calculate weighted index std
    bind.calc_weighted_index_std(
        input_signal_lengths=input_signal_lengths,
        ref_signal_length=ref_signal_length,
        gradient_matrix_ptr=gradient_matrix.data_ptr(),
        weighted_index_std_log_ptr=weighted_index_std_log.data_ptr(),
    )

    return weighted_index_std_log


# High-level convenience functions


def compute_all_weighted_stats(
    input_signals: torch.Tensor,
    gradient_matrix: torch.Tensor,
    input_signal_lengths: List[int],
    ref_signal_length: int,
    normalize: bool = True,
) -> Dict[str, torch.Tensor]:
    """
    Compute all weighted statistics at once.

    Args:
        input_signals: Concatenated input signals. Must be on CUDA.
        gradient_matrix: Gradient matrix in anti-diagonal format.
            If normalize=True, will be normalized in-place.
        input_signal_lengths: List of lengths for each input signal.
        ref_signal_length: Length of the reference signal.
        normalize: Whether to normalize the gradient matrix first.

    Returns:
        Dictionary containing:
        - 'gradient_matrix': Normalized gradient matrix
        - 'weighted_means': Weighted means
        - 'weighted_std_log': Log-scale weighted standard deviations
        - 'weighted_index_std_log': Log-scale weighted index standard deviations

    Example:
        >>> stats = compute_all_weighted_stats(
        ...     signals, gradient, [10, 15, 5], 6
        ... )
        >>> means = stats['weighted_means']
        >>> stds = torch.exp(stats['weighted_std_log'])
    """
    # Normalize gradient matrix if requested
    if normalize:
        gradient_matrix = normalize_gradient_matrix(
            gradient_matrix, input_signal_lengths, ref_signal_length
        )

    # Calculate all statistics
    weighted_means = calculate_weighted_means(
        input_signals, gradient_matrix, input_signal_lengths, ref_signal_length
    )

    weighted_std_log = calculate_weighted_std(
        input_signals,
        gradient_matrix,
        weighted_means,
        input_signal_lengths,
        ref_signal_length,
    )

    weighted_index_std_log = calculate_weighted_index_std(
        gradient_matrix, input_signal_lengths, ref_signal_length
    )

    return {
        "gradient_matrix": gradient_matrix,
        "weighted_means": weighted_means,
        "weighted_std_log": weighted_std_log,
        "weighted_index_std_log": weighted_index_std_log,
    }


def reshape_weighted_stats(
    stats_tensor: torch.Tensor,
    num_signals: int,
    ref_signal_length: int,
) -> torch.Tensor:
    """
    Reshape flattened weighted statistics to (num_signals, ref_signal_length).

    Args:
        stats_tensor: Flattened statistics tensor of size (num_signals * ref_signal_length).
        num_signals: Number of input signals.
        ref_signal_length: Length of reference signal.

    Returns:
        Reshaped tensor of shape (num_signals, ref_signal_length).

    Example:
        >>> means_flat = calculate_weighted_means(signals, gradient, lengths, ref_len)
        >>> means_2d = reshape_weighted_stats(means_flat, len(lengths), ref_len)
        >>> # Now means_2d[i, j] is the weighted mean for signal i at reference position j
    """
    if stats_tensor.numel() != num_signals * ref_signal_length:
        raise ValueError(
            f"Tensor size {stats_tensor.numel()} doesn't match "
            f"expected size {num_signals * ref_signal_length}"
        )

    return stats_tensor.view(num_signals, ref_signal_length)


def extract_signal_stats(
    stats_tensor: torch.Tensor,
    signal_index: int,
    num_signals: int,
    ref_signal_length: int,
) -> torch.Tensor:
    """
    Extract statistics for a specific signal.

    Args:
        stats_tensor: Flattened statistics tensor.
        signal_index: Index of the signal to extract.
        num_signals: Total number of signals.
        ref_signal_length: Length of reference signal.

    Returns:
        Statistics for the specified signal, shape (ref_signal_length,).

    Example:
        >>> means = calculate_weighted_means(signals, gradient, [10, 15, 5], 6)
        >>> signal_0_means = extract_signal_stats(means, 0, 3, 6)
        >>> # signal_0_means.shape = (6,)
    """
    if signal_index >= num_signals:
        raise ValueError(f"Signal index {signal_index} out of range")

    start = signal_index * ref_signal_length
    end = start + ref_signal_length
    return stats_tensor[start:end]


# Batch processing function
def batch_process_weighted_stats(
    signal_batches: List[torch.Tensor],
    gradient_matrices: List[torch.Tensor],
    ref_signal_length: int,
    normalize: bool = True,
) -> List[Dict[str, torch.Tensor]]:
    """
    Process multiple batches of signals and their gradient matrices.

    Args:
        signal_batches: List of concatenated signal tensors.
        gradient_matrices: List of corresponding gradient matrices.
        ref_signal_length: Common reference signal length.
        normalize: Whether to normalize gradient matrices.

    Returns:
        List of dictionaries containing statistics for each batch.

    Example:
        >>> batches = [torch.randn(30, device='cuda'), torch.randn(45, device='cuda')]
        >>> gradients = [grad1, grad2]
        >>> all_stats = batch_process_weighted_stats(batches, gradients, 6)
    """
    if len(signal_batches) != len(gradient_matrices):
        raise ValueError(
            "Number of signal batches must match number of gradient matrices"
        )

    results = []

    for signals, gradient in zip(signal_batches, gradient_matrices):
        # Infer signal lengths (assuming equal length signals in each batch)
        # This is a simplified assumption - in practice, you'd pass lengths explicitly
        total_length = signals.numel()
        matrix_size = gradient.numel()
        num_signals = matrix_size // (total_length * ref_signal_length)
        signal_length = total_length // num_signals

        input_signal_lengths = [signal_length] * num_signals

        stats = compute_all_weighted_stats(
            signals, gradient, input_signal_lengths, ref_signal_length, normalize
        )
        results.append(stats)

    return results


__all__ = [
    "normalize_gradient_matrix",
    "calculate_weighted_means",
    "calculate_weighted_std",
    "calculate_weighted_index_std",
    "compute_all_weighted_stats",
    "reshape_weighted_stats",
    "extract_signal_stats",
    "batch_process_weighted_stats",
]
