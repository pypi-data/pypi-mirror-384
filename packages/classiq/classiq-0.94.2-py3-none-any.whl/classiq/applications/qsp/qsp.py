import builtins
import importlib.util
from collections.abc import Callable
from functools import wraps

import numpy as np
from numpy.polynomial import Chebyshev, Polynomial
from numpy.polynomial.chebyshev import cheb2poly, poly2cheb


def _require_qsp() -> None:
    missing = [m for m in ("cvxpy", "pyqsp") if importlib.util.find_spec(m) is None]
    if missing:
        raise RuntimeError(
            "This feature needs the 'qsp' extra."
            "Install with: pip install classiq[qsp]"
            f"(missing: {', '.join(missing)})"
        )


def silence(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):  # type:ignore[no-untyped-def]
        try:
            original_print = print
            builtins.print = lambda *a, **k: None

            result = func(*args, **kwargs)
        finally:
            builtins.print = original_print
        return result

    return wrapper


@silence
def _pyqsp_get_phases(
    poly_coeffs: np.ndarray, tol: float = 1e-12
) -> tuple[np.ndarray, float]:
    from pyqsp.sym_qsp_opt import newton_solver  # type:ignore[import]

    parity = (len(poly_coeffs) + 1) % 2
    reduced_coefs = poly_coeffs[parity::2]
    _phases, err, _tot_iter, opt = newton_solver(reduced_coefs, parity, crit=tol)
    return opt.full_phases, err


def qsvt_phases(
    poly_coeffs: np.ndarray, cheb_basis: bool = True, tol: float = 1e-12
) -> np.ndarray:
    r"""
    Get QSVT phases that will generate the given Chebyshev polynomial.
    The phases are ready to be used in `qsvt` and `qsvt_lcu` functions in the classiq library. The convetion
    is the reflection signal operator, and the measurement basis is the hadamard basis (see https://arxiv.org/abs/2105.02859
    APPENDIX A.).
    The current implementation is using the pyqsp package, based on techniques in https://arxiv.org/abs/2003.02831.

    Notes:
        1. The polynomial should have a definite parity, and bounded in magnitude by 1 in the interval [-1, 1].
        2. The phase finding works in the Chebyshev basis. If the a monomial basis polynomial is provided,
           it will be converted to the chebyshev basis (and introduce an additional overhead).
        3. The user is advised to get the polynomial using the `qsp_approximate` function.
        4. If the function fails, try to scale down the polynomial by a factor, it should ease the angle finding.

    Args:
        poly_coeffs: Array of polynomial coefficients (Chebyshev\Monomial, depending on cheb_basis).
        cheb_basis: Whether the poly coefficients are given in Chebyshev (True) or Monomial(False). Defaults to Chebyshev.
        tol: Error tolerance for the phases.
    Returns:
        phases: array of the qsvt phases corresponding to the given polynomial.
    """
    _require_qsp()

    assert poly_coeffs is not None
    assert len(poly_coeffs) > 1, "polynomial should have degree >= 1"

    # verify parity
    is_even = np.sum(np.abs(poly_coeffs[0::2])) > 1e-8
    is_odd = np.sum(np.abs(poly_coeffs[1::2])) > 1e-8
    assert is_even or is_odd, "Polynomial should have a definite parity"

    poly_coeffs = np.array(np.trim_zeros(poly_coeffs, "b"))

    if not cheb_basis:
        poly_coeffs = poly2cheb(poly_coeffs)

    # heuristic bound verification
    grid = np.linspace(-1, 1, 1000)
    assert (
        np.max(np.abs(Chebyshev(poly_coeffs)(grid))) <= 1
    ), "polynomial should be bounded in magnitude by 1"

    # get the phases using pyqsp
    phases, err = _pyqsp_get_phases(poly_coeffs, tol)
    if err > tol:
        raise RuntimeError(
            f"Phase finding did not meet target tolerance "
            f"(target={tol:.3e}, achieved={err:.3e}). "
            "Consider increasing the degree, relaxing tol, or changing solver settings."
        )

    # verify conventions.
    ## change the R(x) to W(x), as the phases are in the W(x) conventions
    ## minus is due to exp(-i*phi*z) in qsvt in comparison to qsp
    phases[1:-1] = phases[1:-1] - np.pi / 2
    phases[0] = phases[0] - np.pi / 4
    phases[-1] = phases[-1] + (2 * (len(phases) - 1) - 1) * np.pi / 4

    ## the symmetric method creates the polynomial on Im[P(x)] with Im[Q(x)]=0, so adjust the phases
    ## to extract that (equivalent to applying S on the auxiliary after the first H and before the last H)
    phases[0] -= np.pi / 4
    phases[-1] -= np.pi / 4

    ## multiply by 2 as RZ(theta) = exp(-i*theta/2)
    phases = -2 * phases
    return phases


def _plot_qsp_approx(
    poly_cheb: np.ndarray,
    f_target: Callable[[np.ndarray], np.ndarray],
    interval: tuple[float, float] = (-1, 1),
) -> None:
    from matplotlib import pyplot as plt

    grid_full = np.linspace(-1, 1, 3000)
    grid_interval = np.linspace(interval[0], interval[1], 3000)

    y_target = f_target(grid_interval)
    y_approx = np.polynomial.Chebyshev(poly_cheb)(grid_full)

    # Plot
    plt.figure(figsize=(10, 5))
    plt.plot(grid_interval, y_target, label="Target function", linewidth=4)
    plt.plot(
        grid_full,
        y_approx,
        "--",
        label="Polynomial approximation",
        linewidth=2,
        c="r",
    )
    plt.title("Polynomial Approximation vs Target Function")
    plt.xlabel("x")
    plt.ylabel("f(x)")
    # Draw vertical lines
    plt.axvline(interval[0], color="gray", linestyle=":", linewidth=3)
    plt.axvline(interval[1], color="gray", linestyle=":", linewidth=3)

    plt.legend()
    plt.grid(True)
    plt.show()


def qsp_approximate(
    f_target: Callable[[np.ndarray], np.ndarray],
    degree: int,
    parity: int | None = None,
    interval: tuple[float, float] = (-1, 1),
    bound: float = 0.99,
    num_grid_points: int | None = None,
    plot: bool = False,
) -> tuple[np.ndarray, float]:
    """
    Approximate the target function on the given (sub-)interval of [-1,1], using QSP-compatible chebyshev polynomials.
    The approximating polynomial is enforced to |P(x)| <= bound on all of [-1,1].

    Note: scaling f_target by a factor < 1 might help the convergence and also a later qsp phase factor finiding.

    Args:
        f_target: Real function to approximate within the given interval. Should be bounded by [-1, 1] in the given interval.
        degree: Approximating polynomial degree.
        parity: None - full polynomial, 0 - restrict to even polynomial, 1 - odd polynomial.
        interval: sub interval of [-1, 1] to approximate the function within.
        bound: global polynomial bound on [-1,1] (defaults to 0.99).
        num_grid_points: sets the number of grid points used for the polynomial approximation (defaults to `max(2 * degree, 1000)`).
        plot: A flag for plotting the resulting approximation vs the target function.

    Returns:
        coeffs: Array of Chebyshev coefficients. In case of definite parity, still a full coefficients array is returned.
        max_error: (Approximated) maximum error between the target function and the approximating polynomial within the interval.
    """
    _require_qsp()
    import cvxpy as cp  # type:ignore[import]

    if num_grid_points is None:
        num_grid_points = max(2 * degree, 1000)
    # Discretize [-1, 1] using the grid points (interpolants)
    xj_full = np.cos(
        np.pi * np.arange(num_grid_points) / (num_grid_points - 1)
    )  # Chebyshev nodes on [-1, 1]

    # Select grid points for the objective in [w_min, w_max]
    xj_obj = xj_full[(xj_full >= interval[0]) & (xj_full <= interval[1])]

    yj_obj = f_target(xj_obj)
    # heuristic verification
    bound = min(1, bound)
    assert (
        np.max(np.abs(yj_obj)) <= bound
    ), f"f_target function values should be bounded in magnitude by bound={bound} within the interval:{interval}"

    # Define the Chebyshev polynomials
    con_mat = np.polynomial.chebyshev.chebvander(xj_full, degree)
    obj_mat = np.polynomial.chebyshev.chebvander(xj_obj, degree)

    # Choose which Chebyshev indices to use
    if parity is None:
        cols = np.arange(degree + 1)  # full
    elif parity == 0:
        cols = np.arange(0, degree + 1, 2)  # even T_0, T_2, ...
    elif parity == 1:
        cols = np.arange(1, degree + 1, 2)  # odd  T_1, T_3, ...
    else:
        raise ValueError("parity must be None, 0 (even), or 1 (odd)")

    con_mat = con_mat[:, cols]
    obj_mat = obj_mat[:, cols]

    # Define optimization variables
    c = cp.Variable(len(cols))  # Coefficients for Chebyshev polynomials
    f_values_full = con_mat @ c
    f_values_obj = obj_mat @ c

    # Define the optimization problem
    objective = cp.Minimize(cp.max(cp.abs(f_values_obj - yj_obj)))
    constraints = [cp.abs(f_values_full) <= bound]  # global bound
    prob = cp.Problem(objective, constraints)

    # Solve the optimization problem
    prob.solve()

    # Return coefficients, optimal value, and grid points
    pcoeffs = np.zeros(degree + 1)
    pcoeffs[cols] = c.value

    if plot:
        _plot_qsp_approx(pcoeffs, f_target, interval)

    return pcoeffs, prob.value


def _gqsp_complementary_polynomial(poly_coeffs: np.ndarray) -> np.ndarray:
    """
    Given polynomial coefficients of a wanted P such that |P(e^{i*theta})| <= 1,
    calculates the complementary polynomial Q for the GQSP protocol. The polynomials
    should fulfil |P(e^{i*theta})|^2 + |Q(e^{i*theta})|^2<= 1

    The Implementation is based on the paper https://arxiv.org/abs/2308.01501 Theorem 4.

    Args:
        poly_coeffs: polynomial coefficients of the P polynomial in the monomial basis.

    Returns:
        Q: the coefficient of the complementary Q polynomial in monomial basis.
    """
    degree = len(poly_coeffs) - 1

    grid = np.exp(1j * np.linspace(0.0, 2.0 * np.pi, 2000))
    p_z = Polynomial(poly_coeffs)(grid)
    assert (
        np.max(np.abs(p_z)) <= 1 + 1e-10
    ), "P violates |P(e^{i*theta})| <= 1; cannot construct a complementary Q."

    r = Polynomial.basis(degree) - Polynomial(poly_coeffs) * Polynomial(
        np.conj(poly_coeffs[::-1])
    )
    roots = r.roots()

    roots_circle = roots[np.isclose(np.abs(roots), 1)]
    roots_out = roots[~np.isclose(np.abs(roots), 1)]
    roots_large = roots_out[np.abs(roots_out) > 1]
    roots_small = roots_out[np.abs(roots_out) < 1]

    assert len(roots_small) + len(roots_large) + len(roots_circle) == 2 * (degree)

    # assume the unit roots are with even multiplicity
    roots_circle_halved = sorted(roots_circle)[::2]
    q_roots = np.concatenate([roots_small, roots_circle_halved])

    scale = np.sqrt(np.abs(np.prod(roots_large) * r.coef[-1]))
    q = Polynomial.fromroots(q_roots) * scale

    # verify the completion
    q_z = q(grid)
    if not np.allclose(np.square(np.abs(p_z)) + np.square(np.abs(q_z)), 1, atol=1e-3):
        raise ValueError("Failed to Complete P")

    return q.coef


def _r_rot(theta: float, phi: float) -> np.ndarray:
    return np.array(
        [
            [np.exp(1j * (phi)) * np.cos(theta), np.exp(1j * (phi)) * np.sin(theta)],
            [np.sin(theta), -np.cos(theta)],
        ],
        dtype=complex,
    )


def gqsp_phases(
    poly_coeffs: np.ndarray, cheb_basis: bool = False
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute GQSP phases for a polynomial in the monomial (power) basis.

    The returned phases are compatible with Classiq's `gqsp` function and use the Wz signal
    operator convention.

    Notes:
    - The polynomial must be bounded on the unit circle:
      |P(e^{i*theta})| <= 1 for all theta in [0, 2*pi).
    - Laurent polynomials are supported by degree shifting. If
      P(z) = sum_{k=m}^n c_k * z^k with m < 0, the phases correspond to the
      degree-shifted polynomial z^{-m} * P(z) (so the minimal degree is zero).
    - The phase finiding works in the monomial basis. If the a Chebyshev basis polynomial is provided,
      it will be converted to the monomial basis (and introduce an additional overhead).

    Args:
      poly: array-like of complex, shape (d+1). Monomial coefficients in ascending
            order: [c_0, c_1, ..., c_d].
      cheb_basis: Whether the poly coefficients are given in Chebyshev (True) or Monomial(False). Defaults to Monomial.

    Returns:
      phases: tuple of np.ndarray (thetas, phis, lambdas), ready to use with `gqsp`.

    Raises:
      ValueError: if |P(e^{i*theta})| > 1 anywhere on the unit circle.
    """
    # remove redundant zeros at the end
    poly_coeffs = np.array(np.trim_zeros(poly_coeffs, "b"))

    # move to monomial basis if needed
    if cheb_basis:
        poly_coeffs = cheb2poly(poly_coeffs)

    # verify the normalization
    grid = np.exp(1j * np.linspace(0.0, 2.0 * np.pi, 2000))
    p_z = Polynomial(poly_coeffs)(grid)
    assert (
        np.max(np.abs(p_z)) < 1 + 1e-10
    ), "P violates |P(e^{i*theta})| <= 1; cannot create calculate gqsp phases."

    # get complementary gqsp polynomial
    comp = _gqsp_complementary_polynomial(poly_coeffs)

    s = np.array([poly_coeffs, comp])
    thetas, phis, lambdas = np.zeros((3, len(poly_coeffs)))

    for i in reversed(range(len(poly_coeffs))):
        p_i, q_i = s[:, i]
        thetas[i] = np.arctan2(np.abs(q_i), np.abs(p_i))

        phis[i] = (
            0
            if np.isclose(np.abs([q_i, p_i]), 0, atol=1e-10).any()
            else np.angle(p_i * np.conj(q_i))
        )

        if i == 0:
            lambdas[i] = 0 if np.allclose(np.abs(q_i), 0) else np.angle(q_i)
        else:
            s = _r_rot(thetas[i], phis[i]).conj().T @ s
            s = np.array([s[0][1 : i + 1], s[1][:i]])

    return thetas, phis, lambdas
