import random

import numpy as np
import torch


class RNG:
    """Random number generator manager."""

    _seed: int | None = None
    _np_generator: np.random.Generator | None = None

    @staticmethod
    def initialize(seed: int = 1) -> None:
        """Set global RNG seed for reproducibility.

        Args:
            seed (int): Random number generator seed. Defaults to 1.

        """
        RNG._seed = seed

        random.seed(seed)

        # NumPy
        RNG._np_generator = np.random.default_rng(seed)

        # PyTorch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        torch.use_deterministic_algorithms(mode=True)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    @staticmethod
    def is_initialized() -> bool:
        """Check whether a global RNG seed has been set (via RNG.initialize(...)).

        Returns:
            bool: True if RNG.initialize(...) has been called, else False.

        """
        return RNG._seed is not None

    @staticmethod
    def get_seed() -> int | None:
        """Get the RNG seed used for initialization.

        Returns:
            int | None: The RNG seed.

        """
        return RNG._seed

    @staticmethod
    def np_generator() -> np.random.Generator:
        """NumPy generator initialized with the RNG seed.

        Returns:
            np.random.Generator: The NumPy generator instance.

        """
        if RNG._np_generator is None:
            msg = "RNG is not initialized. Call RNG.initialize(...) first."
            raise RuntimeError(msg)
        return RNG._np_generator
