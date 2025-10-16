# implementing torch.nn.Module for soft-DTW.
import torch
from .utils import concat_signals
from .autograd import SoftDTWFunction


class SoftDTWLoss(torch.nn.Module):
    def __init__(
        self,
        reserved_memory_size: int = -1,
        gamma: float = 1.0,
        device: torch.device | str = "cuda",
    ):
        """
        Initialize the SoftDTWLoss module.

        Args:
            reserved_memory_size (int): Size of the reserved memory for all matrix.
                If -1, no reserved memory is used.
            gamma (float): Smoothing parameter for soft-DTW.
            device (torch.device | str): Device on which to perform the calculations.
                Only CUDA devices are supported.
        """
        super(SoftDTWLoss, self).__init__()
        self.reserved_memory_size = reserved_memory_size
        self.gamma = gamma
        self.device = torch.device(device)
        if self.device.type != "cuda":
            raise ValueError("SoftDTWLoss is only supported on CUDA devices.")

        # reserved memory for distance, score, and gradient matrices
        # These matrices will be reused across forward and backward passes
        if self.reserved_memory_size > 0:
            self.distance_matrix = torch.zeros(
                (reserved_memory_size,),
                dtype=torch.float32,
                device=self.device,
            )
            self.score_matrix = torch.zeros_like(self.distance_matrix)
            self.gradient_matrix = torch.zeros_like(self.distance_matrix)
        else:
            self.distance_matrix = None
            self.score_matrix = None
            self.gradient_matrix = None

    def forward(
        self,
        input_signals: list[torch.Tensor] | torch.Tensor,
        ref_signal: torch.Tensor,
        input_signal_lengths: list[int] | None = None,
    ):
        """
        Forward pass for the soft-DTW loss calculation.
        Args:
            input_signals (list[torch.Tensor] | torch.Tensor):
                - If list: List of 1D tensors representing input signals.
                - If tensor: Pre-concatenated input signals.
            ref_signal (torch.Tensor): Reference signal, should be a 1D tensor.
            input_signal_lengths (list[int], optional):
                Required when input_signals is a tensor. Length of each signal.
        Returns:
            score (torch.Tensor): The soft-DTW score. Size is len(input_signals).
            distance_matrix (torch.Tensor): Matrix containing distances between input signals and the reference signal.
            score_matrix (torch.Tensor): Matrix containing scores from the forward pass.
            gradient_matrix (torch.Tensor): Matrix containing gradients of the distance matrix.
        """
        # Handle different input types
        if isinstance(input_signals, list):
            # Original behavior: concatenate signals
            input_signals_concat, input_signal_lengths = concat_signals(
                input_signals, self.device
            )
        else:
            # New behavior: use pre-concatenated signals
            if input_signal_lengths is None:
                raise ValueError(
                    "input_signal_lengths must be provided when input_signals is a tensor"
                )
            input_signals_concat = input_signals.to(self.device)
            # input_signal_lengths = input_signal_lengths.to(self.device)

        ref_signal = ref_signal.to(self.device)

        score, distance_matrix, score_matrix, gradient_matrix = SoftDTWFunction.apply(  # type: ignore
            input_signals_concat,
            input_signal_lengths,
            ref_signal,
            self.distance_matrix,
            self.score_matrix,
            self.gradient_matrix,
            self.gamma,
        )
        return score, distance_matrix, score_matrix, gradient_matrix
