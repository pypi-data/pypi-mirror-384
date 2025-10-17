"""
Wrapper functions for convenient matrix format conversion between anti-diagonal and square formats.
"""

from typing import List, Tuple
import torch
from flash_softdtw import flash_softdtw_pybind as bind

__all__ = [
    "antidiag_to_square",
    "square_to_antidiag",
    "split_square_matrices",
    "concat_square_matrices",
    "visualize_antidiag_matrix",
    "batch_convert_to_antidiag",
]


def antidiag_to_square(
    antidiag_matrix: torch.Tensor,
    input_signal_lengths: List[int],
    ref_signal_length: int,
    output_matrix: torch.Tensor | None = None,
) -> torch.Tensor:
    """
    Convert anti-diagonal matrix format to standard row-major format.

    Args:
        antidiag_matrix: Input tensor in anti-diagonal format.
            Must be on CUDA and contiguous.
        input_signal_lengths: List of lengths for each input signal.
        ref_signal_length: Length of the reference signal.
        output_matrix: Optional pre-allocated output tensor.
            If None, a new tensor will be created.

    Returns:
        torch.Tensor: Matrix in standard row-major format.

    Example:
        >>> # Convert anti-diagonal gradient matrix for visualization
        >>> gradient_antidiag = torch.randn(180, device='cuda')  # 10*6 + 15*6 + 5*6
        >>> gradient_square = antidiag_to_square(
        ...     gradient_antidiag,
        ...     input_signal_lengths=[10, 15, 5],
        ...     ref_signal_length=6
        ... )
        >>> # Now can reshape each matrix
        >>> first_matrix = gradient_square[:60].view(10, 6)
    """
    # Validate inputs
    if not antidiag_matrix.is_cuda:
        raise ValueError("Input matrix must be on CUDA device")
    if not antidiag_matrix.is_contiguous():
        antidiag_matrix = antidiag_matrix.contiguous()

    # Calculate expected size
    expected_size = sum(length * ref_signal_length for length in input_signal_lengths)
    if antidiag_matrix.numel() != expected_size:
        raise ValueError(
            f"Matrix size {antidiag_matrix.numel()} doesn't match expected size {expected_size}"
        )

    # Create output tensor if not provided
    if output_matrix is None:
        output_matrix = torch.zeros_like(antidiag_matrix)
    else:
        if not output_matrix.is_cuda:
            raise ValueError("Output matrix must be on CUDA device")
        if output_matrix.numel() != expected_size:
            raise ValueError(
                f"Output matrix size {output_matrix.numel()} doesn't match expected size {expected_size}"
            )
        if not output_matrix.is_contiguous():
            output_matrix = output_matrix.contiguous()

    # Call the conversion function
    bind.convert_antidiag_to_square(
        input_signal_lengths=input_signal_lengths,
        ref_signal_length=ref_signal_length,
        input_matrix_ptr=antidiag_matrix.data_ptr(),
        output_matrix_ptr=output_matrix.data_ptr(),
    )

    return output_matrix


def square_to_antidiag(
    square_matrix: torch.Tensor,
    input_signal_lengths: List[int],
    ref_signal_length: int,
    output_matrix: torch.Tensor | None = None,
) -> torch.Tensor:
    """
    Convert standard row-major matrix format to anti-diagonal format.

    Args:
        square_matrix: Input tensor in row-major format.
            Must be on CUDA and contiguous.
        input_signal_lengths: List of lengths for each input signal.
        ref_signal_length: Length of the reference signal.
        output_matrix: Optional pre-allocated output tensor.
            If None, a new tensor will be created.

    Returns:
        torch.Tensor: Matrix in anti-diagonal format.

    Example:
        >>> # Convert standard matrices to anti-diagonal format
        >>> matrices = [torch.randn(10, 6, device='cuda'),
        ...             torch.randn(15, 6, device='cuda')]
        >>> square_concat = torch.cat([m.flatten() for m in matrices])
        >>> antidiag = square_to_antidiag(
        ...     square_concat,
        ...     input_signal_lengths=[10, 15],
        ...     ref_signal_length=6
        ... )
    """
    # Validate inputs
    if not square_matrix.is_cuda:
        raise ValueError("Input matrix must be on CUDA device")
    if not square_matrix.is_contiguous():
        square_matrix = square_matrix.contiguous()

    # Calculate expected size
    expected_size = sum(length * ref_signal_length for length in input_signal_lengths)
    if square_matrix.numel() != expected_size:
        raise ValueError(
            f"Matrix size {square_matrix.numel()} doesn't match expected size {expected_size}"
        )

    # Create output tensor if not provided
    if output_matrix is None:
        output_matrix = torch.zeros_like(square_matrix)
    else:
        if not output_matrix.is_cuda:
            raise ValueError("Output matrix must be on CUDA device")
        if output_matrix.numel() != expected_size:
            raise ValueError(
                f"Output matrix size {output_matrix.numel()} doesn't match expected size {expected_size}"
            )
        if not output_matrix.is_contiguous():
            output_matrix = output_matrix.contiguous()

    # Call the conversion function
    bind.convert_square_to_antidiag(
        input_signal_lengths=input_signal_lengths,
        ref_signal_length=ref_signal_length,
        input_matrix_ptr=square_matrix.data_ptr(),
        output_matrix_ptr=output_matrix.data_ptr(),
    )

    return output_matrix


def split_square_matrices(
    square_matrix: torch.Tensor,
    input_signal_lengths: List[int],
    ref_signal_length: int,
) -> List[torch.Tensor]:
    """
    Split concatenated square matrices into individual matrices.

    Args:
        square_matrix: Concatenated matrices in row-major format.
        input_signal_lengths: List of lengths for each input signal.
        ref_signal_length: Length of the reference signal.

    Returns:
        List of individual matrices, each with shape (signal_length, ref_length).

    Example:
        >>> concat_matrix = antidiag_to_square(antidiag, lengths, ref_len)
        >>> matrices = split_square_matrices(concat_matrix, lengths, ref_len)
        >>> for i, matrix in enumerate(matrices):
        ...     print(f"Matrix {i} shape: {matrix.shape}")
    """
    matrices = []
    offset = 0

    for length in input_signal_lengths:
        size = length * ref_signal_length
        matrix = square_matrix[offset : offset + size].view(length, ref_signal_length)
        matrices.append(matrix)
        offset += size

    return matrices


def concat_square_matrices(
    matrices: List[torch.Tensor],
    flatten: bool = True,
) -> Tuple[torch.Tensor, List[int], int]:
    """
    Concatenate individual matrices into a single tensor.

    Args:
        matrices: List of 2D tensors to concatenate.
        flatten: If True, flatten each matrix before concatenation.

    Returns:
        Tuple of:
        - Concatenated tensor
        - List of signal lengths
        - Reference signal length

    Example:
        >>> matrices = [torch.randn(10, 6, device='cuda'),
        ...             torch.randn(15, 6, device='cuda')]
        >>> concat, lengths, ref_len = concat_square_matrices(matrices)
        >>> antidiag = square_to_antidiag(concat, lengths, ref_len)
    """
    if not matrices:
        raise ValueError("Matrix list is empty")

    # Extract dimensions
    input_signal_lengths = [m.shape[0] for m in matrices]
    ref_signal_length = matrices[0].shape[1]

    # Check consistency
    for i, m in enumerate(matrices):
        if m.shape[1] != ref_signal_length:
            raise ValueError(
                f"Matrix {i} has inconsistent reference length: "
                f"{m.shape[1]} vs {ref_signal_length}"
            )

    # Concatenate
    if flatten:
        concatenated = torch.cat([m.flatten() for m in matrices])
    else:
        concatenated = torch.cat(matrices, dim=0)

    return concatenated, input_signal_lengths, ref_signal_length


# Convenience functions for common use cases


def visualize_antidiag_matrix(
    antidiag_matrix: torch.Tensor,
    input_signal_lengths: List[int],
    ref_signal_length: int,
    signal_index: int = 0,
) -> torch.Tensor:
    """
    Extract a single matrix from anti-diagonal format for visualization.

    Args:
        antidiag_matrix: Matrix in anti-diagonal format.
        input_signal_lengths: List of lengths for each input signal.
        ref_signal_length: Length of the reference signal.
        signal_index: Index of the signal to extract (default: 0).

    Returns:
        2D tensor of shape (signal_length, ref_length) for the specified signal.

    Example:
        >>> # Visualize the first signal's alignment matrix
        >>> matrix = visualize_antidiag_matrix(
        ...     gradient_antidiag,
        ...     lengths,
        ...     ref_len,
        ...     signal_index=0
        ... )
        >>> plt.imshow(matrix.cpu())
    """
    if signal_index >= len(input_signal_lengths):
        raise ValueError(f"Signal index {signal_index} out of range")

    # Convert to square format
    square_matrix = antidiag_to_square(
        antidiag_matrix, input_signal_lengths, ref_signal_length
    )

    # Extract the specific matrix
    offset = sum(
        input_signal_lengths[i] * ref_signal_length for i in range(signal_index)
    )
    length = input_signal_lengths[signal_index]
    matrix = square_matrix[offset : offset + length * ref_signal_length].view(
        length, ref_signal_length
    )

    return matrix


def batch_convert_to_antidiag(
    matrices: List[torch.Tensor],
) -> Tuple[torch.Tensor, List[int], int]:
    """
    Convert a list of standard matrices to concatenated anti-diagonal format.

    Args:
        matrices: List of 2D tensors in row-major format.

    Returns:
        Tuple of:
        - Concatenated tensor in anti-diagonal format
        - List of signal lengths
        - Reference signal length

    Example:
        >>> matrices = [torch.randn(10, 6, device='cuda') for _ in range(3)]
        >>> antidiag, lengths, ref_len = batch_convert_to_antidiag(matrices)
    """
    concat, lengths, ref_len = concat_square_matrices(matrices, flatten=True)
    antidiag = square_to_antidiag(concat, lengths, ref_len)
    return antidiag, lengths, ref_len
