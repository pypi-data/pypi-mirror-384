from typing import Callable

from brtp.math.utils import EPS, same_sign


def bisection(fun: Callable[[float], float], a: float, b: float, x_tol: float = 0.0) -> float:
    """
    Bisection method for root finding.

    The algorithm determines a root for fun(x) with x in [a, b], where fun(a) and fun(b) must have opposite signs.

    The solution is determined up to machine accuracy or an absolute tolerance of x_tol, whichever is achieved first.
    In case provided x_tol<=0.0 (default=0.0), it is replaced with EPS*EPS, to guarantee convergence.
    """

    # argument handling
    if x_tol < 0.0:
        x_tol = EPS * EPS
    dx = 2 * x_tol  # if we terminate when (b-a)<=dx, we have accuracy dx/2 = x_tol

    # initialize
    fa = fun(a)
    fb = fun(b)
    if same_sign(fa, fb):
        raise ValueError("fun(a) and fun(b) must have opposite signs")

    while True:
        x_mid = 0.5 * (a + b)

        if ((b - a) <= dx) or (x_mid == a) or (x_mid == b):
            # we reached either required x_tol or machine accuracy
            return x_mid
        else:
            # bisect further
            f_mid = fun(x_mid)
            if same_sign(fa, f_mid):
                a = x_mid
                fa = f_mid
            else:
                b = x_mid
                fb = f_mid
