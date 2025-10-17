import math


def sign(x: float) -> int | None:
    """Return -1,0,1, None for negative, zero, positive, NaN values of x."""
    if math.isnan(x):  # NaN check
        return None
    elif x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0


def same_sign(x: float, y: float) -> bool:
    """Return True if x and y have the same sign, False if not & False if either is NaN."""
    if math.isnan(x) or math.isnan(y):
        return False
    else:
        return (x > 0 and y > 0) or (x < 0 and y < 0) or (x == 0 and y == 0)
