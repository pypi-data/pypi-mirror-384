from typing import Iterable
import random


def zip_random(*iterables, seed: int | None = None) -> Iterable[tuple]:
    """
    Zip multiple iterables together in a random order.

    Example:
        >>> list(zip_random([1, 2, 3], ['a', 'b', 'c'], seed=42))
        [(2, 'b'), (3, 'a'), (1, 'c')]

    :param iterables: positional arguments representing iterables to be zipped
    :param seed: (int | None) random seed for reproducibility, default=None (no seed set).
    :return: iterable of tuples
    """

    # it's inevitable to 'materialize' the iterables before randomization & zipping
    lists = [list(it) for it in iterables]

    # randomize lists
    if seed is not None:
        random.seed(seed)
    for lst in lists:
        random.shuffle(lst)

    # zip the lists together
    return zip(*lists)