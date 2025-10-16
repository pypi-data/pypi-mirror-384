# Implementing autograd Function for soft-DTW.
# Use torch.autograd.function.Function to create a custom autograd function for soft-DTW.
import torch
from torch.autograd.function import Function, FunctionCtx
from .softdtw import softdtw_forward, softdtw_backward
from .manhattan_distance import (
    calc_manhattan_distance,
    calc_manhattan_distance_gradient,
)
from .utils import multiply_matrices


class SoftDTWFunction(Function):
    @staticmethod
    def forward(
        ctx: FunctionCtx,
        input_signals: torch.Tensor,
        input_signal_lengths: list[int],
        ref_signal: torch.Tensor,
        distance_matrix: torch.Tensor | None = None,
        score_matrix: torch.Tensor | None = None,
        gradient_matrix: torch.Tensor | None = None,
        gamma: float = 1.0,
    ):
        """
        Forward pass for the soft-DTW calculation.
        """
        ref_signal_length = ref_signal.size(0)
        distance_matrix = calc_manhattan_distance(
            input_signals, input_signal_lengths, ref_signal, distance_matrix
        )
        scores, score_matrix = softdtw_forward(
            input_signal_lengths,
            ref_signal_length,
            distance_matrix,
            score_matrix,
            gamma,
        )
        gradient_matrix = softdtw_backward(
            input_signal_lengths,
            ref_signal_length,
            distance_matrix,
            score_matrix,
            gradient_matrix,
            gamma,
        )
        ctx.save_for_backward(
            input_signals,
            ref_signal,
            gradient_matrix,
        )
        ctx.input_signal_lengths = input_signal_lengths  # type:ignore
        ctx.ref_signal_length = ref_signal_length  # type:ignore

        return scores, distance_matrix, score_matrix, gradient_matrix

    @staticmethod
    def backward(  # type:ignore
        ctx: FunctionCtx, grad_scores: torch.Tensor, *args: torch.Tensor
    ) -> tuple[torch.Tensor, None, torch.Tensor, None, None, None, None]:  # type:ignore
        """backward pass for the soft-DTW calculation."""
        input_signals, ref_signal, gradient_matrix = ctx.saved_tensors  # type:ignore
        input_signal_lengths = ctx.input_signal_lengths  # type:ignore
        ref_signal_length = ctx.ref_signal_length  # type:ignore

        matrix_size_list = [
            length * ref_signal_length for length in input_signal_lengths
        ]

        gradient_matrix = multiply_matrices(
            gradient_matrix, matrix_size_list, grad_scores
        )

        input_gradients, ref_gradients = calc_manhattan_distance_gradient(
            input_signals,
            input_signal_lengths,
            ref_signal,
            gradient_matrix,
        )

        return input_gradients, None, ref_gradients, None, None, None, None
