from collections.abc import Callable

import torch

TensorMapping = Callable[[torch.Tensor], torch.Tensor]
