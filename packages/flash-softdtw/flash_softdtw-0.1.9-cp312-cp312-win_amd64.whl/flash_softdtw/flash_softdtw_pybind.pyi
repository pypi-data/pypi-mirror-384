from typing import List

def calc_manhattan_distance(
    input_signal_ptr: int,
    input_signal_lengths: List[int],
    ref_signal_ptr: int,
    ref_signal_length: int,
    distance_matrix_ptr: int,
) -> None:
    """
    Calculate Manhattan distance between input signals and a reference signal.

    This function computes the Manhattan distance between multiple input signals
    and a single reference signal. All data must be in GPU memory and contiguous.

    Args:
        input_signal_ptr: Pointer to the input signal data (float array).
            All input signals are concatenated into one tensor, and its data_ptr
            is passed to this function. These signals must be in GPU memory and contiguous.

        input_signal_lengths: Lengths of each input signal in the concatenated tensor.

        ref_signal_ptr: Pointer to the reference signal data (float array).
            Reference signal is a single tensor. This signal must be in GPU memory
            and contiguous.

        ref_signal_length: Length of the reference signal.

        distance_matrix_ptr: Pointer to the output distance matrix data.
            The size of each distance matrix for each input signal is
            (length of input signal) * (length of reference signal).
            These distance matrices are concatenated into one tensor, and its data_ptr
            is passed to this function. This matrix must be in GPU memory and contiguous.

    Returns:
        None: The function modifies the distance matrix in-place.

    Note:
        All pointer arguments should be obtained from PyTorch tensor's data_ptr() method
        or equivalent GPU memory pointers. The function expects float32 data type.
    """
    ...

def calc_manhattan_distance_gradient(
    input_signal_ptr: int,
    input_signal_lengths: List[int],
    ref_signal_ptr: int,
    ref_signal_length: int,
    gradient_matrix_ptr: int,
    input_gradients_ptr: int,
    ref_gradients_ptr: int,
) -> None:
    """
    Calculate the gradient of the Manhattan distance.

    The gradient will be calculated with respect to the input signals and
    reference signal.

    Args:
        input_signal_ptr: Pointer to the input signal data (float array).
            All input signals are concatenated into one tensor, and its data_ptr
            is passed to this function. These signals must be in GPU memory and contiguous.

        input_signal_lengths: Lengths of each input signal in the concatenated tensor.

        ref_signal_ptr: Pointer to the reference signal data (float array).
            Reference signal is a single tensor. This signal must be in GPU memory
            and contiguous.

        ref_signal_length: Length of the reference signal.

        gradient_matrix_ptr: Pointer to the output gradient matrix data.
            The size of each gradient matrix for each input signal is
            (length of input signal) * (length of reference signal).
            These gradient matrices are concatenated into one tensor, and its data_ptr
            is passed to this function.

        input_gradients_ptr: Pointer to the gradient of the input signals.
            The shape of this tensor is the same as the input signals.

        ref_gradients_ptr: Pointer to the gradient of the reference signal.
            The shape of this tensor is the same as the reference signal.

    Returns:
        None: The function modifies the gradient tensors in-place.
    """
    ...

def calc_softdtw_forward(
    input_signal_lengths: List[int],
    ref_signal_length: int,
    distance_matrix_ptr: int,
    score_matrix_ptr: int,
    scores_ptr: int,
    gamma: float = 1.0,
) -> None:
    """
    Calculate the softDTW forward pass by outputting score matrix and final scores.

    Args:
        input_signal_lengths: Lengths of each input signal in the concatenated tensor.

        ref_signal_length: Length of the reference signal.

        distance_matrix_ptr: Pointer to the output distance matrix data.
            This is already calculated by calc_manhattan_distance function.

        score_matrix_ptr: Pointer to the output score matrix data.
            The shape is same as the distance matrix.

        scores_ptr: Pointer to the output scores data.
            The length of this tensor is the number of input signals.

    Returns:
        None: The function modifies the score matrix and scores tensors in-place.
    """
    ...

def calc_softdtw_backward(
    input_signal_lengths: List[int],
    ref_signal_length: int,
    distance_matrix_ptr: int,
    score_matrix_ptr: int,
    gradient_matrix_ptr: int,
    gamma: float = 1.0,
) -> None:
    """
    Calculate the softDTW backward pass by outputting gradient matrix.

    Args:
        input_signal_lengths: Lengths of each input signal in the concatenated tensor.

        ref_signal_length: Length of the reference signal.

        distance_matrix_ptr: Pointer to the output distance matrix data.
            This is already calculated by calc_manhattan_distance function.

        score_matrix_ptr: Pointer to the output score matrix data.
            This is already calculated by calc_softdtw_forward function.

        gradient_matrix_ptr: Pointer to the output gradient matrix data.
            The shape is same as the distance matrix. This matrix also represents
            the alignment matrix.

    Returns:
        None: The function modifies the gradient matrix in-place.
    """
    ...

def normalize_matrix(
    input_signal_lengths: List[int],
    ref_signal_length: int,
    gradient_matrix_ptr: int,
    ref_total_grads_ptr: int,
) -> None:
    """
    Normalize the gradient matrix by dividing each element by the sum of
    gradients for each reference position.

    Args:
        input_signal_lengths: Lengths of each input signal in the concatenated tensor.

        ref_signal_length: Length of the reference signal.

        gradient_matrix_ptr: Pointer to the gradient matrix data.
            The size of each gradient matrix for each input signal is
            (length of input signal) * (length of reference signal).
            These matrices are concatenated. This matrix must be in GPU memory
            and contiguous. This will be modified in-place to contain normalized values.

        ref_total_grads_ptr: Pointer to temporary storage for sum of gradients
            per reference position. The size is (number of input signals) *
            (reference signal length). Must be in GPU memory and contiguous.

    Returns:
        None: The function modifies the gradient matrix in-place.

    Note:
        All pointer arguments should be obtained from PyTorch tensor's data_ptr() method
        or equivalent GPU memory pointers. The function expects float32 data type.
    """
    ...

def calc_weighted_means(
    input_signal_ptr: int,
    input_signal_lengths: List[int],
    ref_signal_length: int,
    gradient_matrix_ptr: int,
    weighted_means_ptr: int,
) -> None:
    """
    Calculate weighted means of input signals using the normalized
    gradient matrix as weights.

    Args:
        input_signal_ptr: Pointer to the input signal data (float array).
            All input signals are concatenated to one tensor. These signals must be
            in GPU memory and contiguous.

        input_signal_lengths: Lengths of each input signal in the concatenated tensor.

        ref_signal_length: Length of the reference signal.

        gradient_matrix_ptr: Pointer to the normalized gradient matrix data.
            The size of each gradient matrix for each input signal is
            (length of input signal) * (length of reference signal).
            These matrices are concatenated. Must be in GPU memory and contiguous.

        weighted_means_ptr: Pointer to the output weighted means data.
            The size is (number of input signals) * (reference signal length).
            Must be in GPU memory and contiguous.

    Returns:
        None: The function modifies the weighted means tensor in-place.

    Note:
        The gradient matrix should be normalized before calling this function.
    """
    ...

def calc_weighted_std(
    input_signal_ptr: int,
    input_signal_lengths: List[int],
    ref_signal_length: int,
    gradient_matrix_ptr: int,
    weighted_means_ptr: int,
    weighted_std_log_ptr: int,
) -> None:
    """
    Calculate weighted standard deviation (in log scale) of input signals
    using the normalized gradient matrix as weights.

    Args:
        input_signal_ptr: Pointer to the input signal data (float array).
            All input signals are concatenated to one tensor. These signals must be
            in GPU memory and contiguous.

        input_signal_lengths: Lengths of each input signal in the concatenated tensor.

        ref_signal_length: Length of the reference signal.

        gradient_matrix_ptr: Pointer to the normalized gradient matrix data.
            The size of each gradient matrix for each input signal is
            (length of input signal) * (length of reference signal).
            These matrices are concatenated. Must be in GPU memory and contiguous.

        weighted_means_ptr: Pointer to the precomputed weighted means data.
            The size is (number of input signals) * (reference signal length).
            Must be in GPU memory and contiguous.

        weighted_std_log_ptr: Pointer to the output weighted standard deviation
            data in log scale. The size is (number of input signals) *
            (reference signal length). Must be in GPU memory and contiguous.
            Values are clamped to [-10, 10] range.

    Returns:
        None: The function modifies the weighted standard deviation tensor in-place.

    Note:
        The weighted means should be precomputed using calc_weighted_means before
        calling this function.
    """
    ...

def calc_weighted_index_std(
    input_signal_lengths: List[int],
    ref_signal_length: int,
    gradient_matrix_ptr: int,
    weighted_index_std_log_ptr: int,
) -> None:
    """
    Calculate weighted standard deviation (in log scale) of index positions
    using the normalized gradient matrix as weights.

    Args:
        input_signal_lengths: Lengths of each input signal in the concatenated tensor.

        ref_signal_length: Length of the reference signal.

        gradient_matrix_ptr: Pointer to the normalized gradient matrix data.
            The size of each gradient matrix for each input signal is
            (length of input signal) * (length of reference signal).
            These matrices are concatenated. Must be in GPU memory and contiguous.

        weighted_index_std_log_ptr: Pointer to the output weighted index
            standard deviation data in log scale. The size is (number of input signals)
            * (reference signal length). Must be in GPU memory and contiguous.
            Values are clamped to [-10, 10] range.

    Returns:
        None: The function modifies the weighted index standard deviation tensor in-place.

    Note:
        This function calculates the standard deviation of index positions rather
        than signal values, which is useful for measuring signal spread.
    """
    ...

def convert_antidiag_to_square(
    input_signal_lengths: List[int],
    ref_signal_length: int,
    input_matrix_ptr: int,
    output_matrix_ptr: int,
) -> None:
    """
    Convert anti-diagonal matrix format to standard row-major format.

    This function is useful for debugging and compatibility with standard
    PyTorch operations that expect row-major matrix layout.

    Args:
        input_signal_lengths: Lengths of each input signal in the concatenated tensor.

        ref_signal_length: Length of the reference signal.

        input_matrix_ptr: Pointer to the input matrix data in anti-diagonal format.
            The size of each matrix for each input signal is (length of input signal)
            * (length of reference signal). These matrices are concatenated.
            Must be in GPU memory and contiguous.

        output_matrix_ptr: Pointer to the output matrix data in row-major format.
            The size and structure is the same as input, but stored in standard
            row-major order. Must be in GPU memory and contiguous.

    Returns:
        None: The function modifies the output matrix in-place.

    Note:
        This conversion has performance overhead and should only be used when
        necessary for compatibility or debugging purposes. The anti-diagonal
        format is optimized for memory access patterns in the main algorithms.

    Example:
        >>> # Convert anti-diagonal matrix to standard format for visualization
        >>> antidiag_matrix = torch.zeros(total_size, device='cuda')
        >>> square_matrix = torch.zeros(total_size, device='cuda')
        >>> convert_antidiag_to_square(
        ...     input_signal_lengths=[10, 15],
        ...     ref_signal_length=20,
        ...     input_matrix_ptr=antidiag_matrix.data_ptr(),
        ...     output_matrix_ptr=square_matrix.data_ptr()
        ... )
        >>> # Now square_matrix can be reshaped and used with standard PyTorch ops
    """
    ...

def convert_square_to_antidiag(
    input_signal_lengths: List[int],
    ref_signal_length: int,
    input_matrix_ptr: int,
    output_matrix_ptr: int,
) -> None:
    """
    Convert standard row-major matrix format to anti-diagonal format.

    This function converts matrices from standard PyTorch row-major layout
    to the optimized anti-diagonal format used by the CUDA kernels.

    Args:
        input_signal_lengths: Lengths of each input signal in the concatenated tensor.

        ref_signal_length: Length of the reference signal.

        input_matrix_ptr: Pointer to the input matrix data in row-major format.
            The size of each matrix for each input signal is (length of input signal)
            * (length of reference signal). These matrices are concatenated.
            Must be in GPU memory and contiguous.

        output_matrix_ptr: Pointer to the output matrix data in anti-diagonal format.
            The size and structure is the same as input, but stored in anti-diagonal
            order for optimized memory access. Must be in GPU memory and contiguous.

    Returns:
        None: The function modifies the output matrix in-place.

    Note:
        Anti-diagonal format provides better memory access patterns for the
        DTW algorithms. Use this when preparing external data for processing.
        All other functions in this library expect matrices in anti-diagonal format.

    Example:
        >>> # Convert standard PyTorch matrix to anti-diagonal format
        >>> square_matrix = torch.randn(10, 20, device='cuda').flatten()
        >>> antidiag_matrix = torch.zeros_like(square_matrix)
        >>> convert_square_to_antidiag(
        ...     input_signal_lengths=[10],
        ...     ref_signal_length=20,
        ...     input_matrix_ptr=square_matrix.data_ptr(),
        ...     output_matrix_ptr=antidiag_matrix.data_ptr()
        ... )
        >>> # Now antidiag_matrix can be used with other CUDA functions
    """
    ...
