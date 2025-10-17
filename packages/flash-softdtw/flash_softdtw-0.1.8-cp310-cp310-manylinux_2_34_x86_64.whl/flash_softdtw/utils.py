import torch


def concat_signals(
    input_signals: list[torch.Tensor],
    device: torch.device | str = torch.device("cuda")
    if torch.cuda.is_available()
    else torch.device("cpu"),
):
    """
    Concatenates a list of 1D tensors into a 1D tensor.

    Args:
        input_signals (list[torch.Tensor]): List of 1D tensors to concatenate.
        device (torch.device | str): Device on which to create the concatenated tensor. Defaults to CUDA if available, otherwise CPU.

    Returns:
        input_signals_concat (torch.Tensor): A 1D tensor containing all input signals concatenated.
        input_signal_lengths (list[int]): List of lengths of each input signal.
    """
    input_signal_lengths = [signal.size(0) for signal in input_signals]
    input_signals_concat = torch.cat(input_signals, dim=0).to(device)
    return input_signals_concat, input_signal_lengths


def multiply_matrices(
    concatenated_matrix: torch.Tensor, sizes: list[int], multipliers: torch.Tensor
) -> torch.Tensor:
    start_idx = 0

    for i, size in enumerate(sizes):
        end_idx = start_idx + size
        concatenated_matrix[start_idx:end_idx] *= multipliers[i]
        start_idx = end_idx

    return concatenated_matrix
