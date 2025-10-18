from torch.utils.data import DataLoader, random_split

from kosmos.ml.datasets.dataset import SLDataset


def make_train_test_dataloaders(
    dataset: SLDataset,
    train_split: float,
    batch_size: int,
    num_train_subsets: int = 1,
) -> tuple[list[DataLoader], DataLoader]:
    """Split a dataset into training and test subsets and wrap them in DataLoaders.

    The training loaders shuffle their subset each epoch; the test loader does not.

    Args:
        dataset: The dataset to be split.
        train_split: Fraction of dataset for training. Test split is 1 - train_split.
        batch_size: Number of samples per batch in both loaders.
        num_train_subsets: Number of partitions to split the training subset into. Defaults to 1.

    Returns:
        tuple[list[DataLoader], DataLoader]: A tuple containing:

            - list[DataLoader]: DataLoaders for the partitions of the training subset.
            - DataLoader: DataLoader for the test subset.

    """
    if num_train_subsets < 1:
        msg = "num_train_subsets must be >= 1."
        raise ValueError(msg)

    n_total = len(dataset)
    n_train = int(n_total * train_split)
    n_test = n_total - n_train
    if n_train == 0 or n_test == 0:
        msg = "Empty subset after splitting."
        raise ValueError(msg)

    # Train/test split
    train_subset, test_subset = random_split(dataset, lengths=[n_train, n_test])

    # Split train subset across num_train_subsets
    num_train_samples = len(train_subset)
    base = num_train_samples // num_train_subsets
    rem = num_train_samples % num_train_subsets
    sizes = [(base + 1 if i < rem else base) for i in range(num_train_subsets)]

    if any(s == 0 for s in sizes):
        msg = (
            f"Not enough training samples ({num_train_samples})"
            f" to create {num_train_subsets} training subsets."
        )
        raise ValueError(msg)

    client_subsets = random_split(train_subset, lengths=sizes)
    train_loaders = [DataLoader(cs, batch_size, shuffle=True) for cs in client_subsets]
    test_loader = DataLoader(test_subset, batch_size, shuffle=False)

    return train_loaders, test_loader
