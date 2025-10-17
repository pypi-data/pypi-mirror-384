import pytest
import warnings
import numpy as np
from numpy.testing import assert_allclose

from yaiv.defaults.config import ureg
from yaiv import utils as ut
from yaiv import spectrum, grep


def test_check_unit_consistency_success():
    ut._check_unit_consistency([1, 2.0, None])  # all unitless
    ut._check_unit_consistency(
        [1.0 * ureg.meter, 2.0 * ureg.second, None]
    )  # all unitful


def test_check_unit_consistency_failure(capsys):
    with pytest.raises(TypeError):
        ut._check_unit_consistency(
            [1.0 * ureg.meter, 2.0, None],
            names=["length", "value", "optional"],
        )
    out = capsys.readouterr().out
    assert "Units check failed for:" in out
    assert "Units status:" in out


def test_invQ():
    # Inverse should have 1/unit
    A = np.eye(2) * (2.0 * ureg.meter)
    inv = ut.invQ(A)
    assert isinstance(inv, ureg.Quantity)
    assert_allclose(inv.magnitude, 0.5 * np.eye(2))
    # Units: 1/meter
    assert inv.check(1 / ureg.meter)


def test_reciprocal_basis():
    # Lattice basis as identity (rows), expect reciprocal = 2π I
    a = 2 * np.eye(3) * ureg.meter
    K = ut.reciprocal_basis(a)
    assert isinstance(K, ureg.Quantity)
    assert_allclose(K.magnitude, 0.5 * np.eye(3))
    # Units: 2π / meter
    assert K.check(ureg._2pi / ureg.meter)


def test_cartesian_crystal_conversion():
    # Cubic 1 Å box
    a0 = 3.0 * ureg.angstrom
    basis = np.eye(3) * a0
    r_cart = np.array([0.3, 0.4, 0.5]) * ureg.angstrom

    r_cryst = ut.cartesian2cryst(r_cart, basis)
    # Should be in crystal units
    assert isinstance(r_cryst, ureg.Quantity)
    assert r_cryst.check(ureg.crystal)

    r_back = ut.cryst2cartesian(r_cryst, basis)
    assert isinstance(r_back, ureg.Quantity)
    assert r_back.check(ureg.angstrom)
    assert_allclose(
        r_back.to(ureg.angstrom).magnitude,
        r_cart.to(ureg.angstrom).magnitude,
        atol=1e-12,
    )


def test_cartesian2cryst_unit_incompatibility_raises():
    basis = np.eye(3) * (1.0 * ureg.meter)
    coord = np.array([1.0, 0.0, 0.0]) * ureg.meter
    with pytest.raises(TypeError):
        _ = ut.cartesian2cryst(coord.magnitude, basis)
    with pytest.raises(TypeError):
        _ = ut.cartesian2cryst(coord, basis.magnitude)
    with pytest.raises(TypeError):
        _ = ut.cartesian2cryst(coord.magnitude, basis.magnitude / ureg.meter)


def test_cryst2cartesian_unit_incompatibility_raises():
    basis = np.eye(3) * (1.0 * ureg.angstrom)
    coord = np.array([1.0, 0.0, 0.0])
    with pytest.raises(TypeError):
        _ = ut.cryst2cartesian(coord * ureg.meter, basis)
    with pytest.raises(TypeError):
        _ = ut.cryst2cartesian(coord, basis)


def test_voigt_cartesian_conversion():
    T = (
        np.array(
            [
                [1.0, 0.2, -0.3],
                [0.2, 2.0, 0.4],
                [-0.3, 0.4, -1.0],
            ]
        )
        * ureg.gigapascal
    )

    v = ut.cartesian2voigt(T)
    assert isinstance(v, ureg.Quantity)
    assert v.check(ureg.gigapascal)
    assert v.shape == (6,)

    T2 = ut.voigt2cartesian(v)
    assert isinstance(T2, ureg.Quantity)
    assert T2.check(ureg.gigapascal)
    assert_allclose(T2.magnitude, T.magnitude)


@pytest.mark.parametrize(
    "grid,expected_shape",
    [([1], (1, 1)), ([2], (2, 1)), ([2, 3], (6, 2)), ([2, 3, 4], (24, 3))],
)
def test_grid_generator_nonperiodic(grid, expected_shape):
    coords = ut.grid_generator(grid, periodic=False)
    assert coords.shape == expected_shape
    # Nonperiodic default spans [-1, 1], endpoints included (unless g==1)
    assert np.all(coords <= 1.0 + 1e-12)
    assert np.all(coords >= -1.0 - 1e-12)


def test_grid_generator_periodic():
    # periodic -> values in (-0.5, 0.5], no duplicates at borders
    coords = ut.grid_generator([4, 2], periodic=True)
    assert coords.shape == (8, 2)
    assert np.all(coords[:, 0] > -0.5 - 1e-12) and np.all(coords[:, 0] <= 0.5 + 1e-12)
    assert np.all(coords[:, 1] > -0.5 - 1e-12) and np.all(coords[:, 1] <= 0.5 + 1e-12)


def test_methpax_delta_integrates_to_A():
    # Order 0 should integrate to A. Numerically approximate over a wide range.
    A = 1.7
    s = 0.2  # smearing
    xs = np.linspace(-5 * s, 5 * s, 2001)
    # order 0
    ys = np.array([ut.methpax_delta(x, mean=0.0, smearing=s, order=0, A=A) for x in xs])
    integral = np.trapezoid(ys, xs)
    assert_allclose(
        integral, A, rtol=5e-3, atol=5e-3
    )  # loose tolerance due to finite range
    # order 1
    ys = np.array([ut.methpax_delta(x, mean=0.0, smearing=s, order=0, A=A) for x in xs])
    integral = np.trapezoid(ys, xs)
    assert_allclose(
        integral, A, rtol=5e-3, atol=5e-3
    )  # loose tolerance due to finite range


def test_analyze_distribution_gaussian():
    mu = 0.3
    sigma = 0.1
    A = 1
    X = np.linspace(mu - 6 * sigma, mu + 6 * sigma, 2001)
    #    Y = (1.0 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((X - mu) / sigma) ** 2)
    Y = ut._normal_dist(X, mean=mu, sd=sigma, A=A)

    stats = ut.analyze_distribution(X, Y)
    assert_allclose(stats.norm, A, rtol=1e-3, atol=1e-3)
    assert_allclose(stats.mean, mu, rtol=1e-3, atol=1e-3)
    assert_allclose(stats.std, sigma, rtol=1e-3, atol=1e-3)
    # Gaussian skewness ~ 0, kurtosis ~ 3
    assert abs(stats.skewness) < 1e-2
    assert_allclose(stats.kurtosis, 3.0, rtol=1e-2, atol=1e-2)


def test_analyze_distribution_zero_norm_raise():
    X = np.linspace(-2, 2, 201)
    Y = X
    with pytest.raises(ValueError):
        ut.analyze_distribution(X, Y)


def test_kernel_density_normalization_gaussian():
    """
    For Gaussian kernel (order=0), the integral over the density should equal
    sum_k w_k * sum_b values[k,b]. With values=1 and weights summing to 1,
    this equals the number of bands.
    """
    nk, nb = 4, 3
    # Simple energies spread around 0
    x = np.array(
        [
            [-0.20, 0.00, 0.15],
            [-0.10, 0.05, 0.25],
            [0.00, 0.10, 0.30],
            [0.05, 0.20, 0.40],
        ]
    )
    assert x.shape == (nk, nb)
    values = np.ones_like(x)
    weights = np.ones(nk) / nk  # sum(weights) = 1

    # Choose a window around the energies, and small sigma for reasonable resolution
    center = 0.0
    x_window = 1.0
    sigma = 0.05
    steps = 2000

    out = ut.kernel_density_on_grid(
        x=x,
        values=values,
        weights=weights,
        center=center,
        x_window=x_window,
        sigma=sigma,
        steps=steps,
        order=0,  # Gaussian
        cutoff_sigmas=5.0,
    )
    # Integral of density over grid should be nb (sum_b values) since sum_k w_k = 1
    integral = np.trapezoid(out.density, out.grid)
    assert_allclose(integral, nb, rtol=5e-3, atol=5e-3)


def test_kernel_density_units():
    """
    With unitful inputs: grid should have x units; density should have units values/x.
    """
    nk, nb = 2, 2
    x = np.array([[0.0, 0.1], [0.2, 0.3]]) * ureg.eV
    values = np.ones_like(x)  # dimensionless "states"
    weights = np.array([0.5, 0.5])

    out = ut.kernel_density_on_grid(
        x=x,
        values=values,
        weights=weights,
        center=0.0 * ureg.eV,
        x_window=0.5 * ureg.eV,
        sigma=0.05 * ureg.eV,
        steps=1000,
        order=0,
    )
    # Grid units should be eV
    assert hasattr(out.grid, "units")
    assert out.grid.check(ureg.eV)
    # Density units should be 1/eV
    assert hasattr(out.density, "units")
    assert out.density.check(1 / ureg.eV)


def test_kernel_density_shape_errors():
    """
    Mismatched shapes should raise ValueError.
    """
    nk, nb = 3, 2
    x = np.random.rand(nk, nb)
    values_bad = np.random.rand(nk, nb + 1)  # wrong shape
    weights_bad = np.ones(nk + 1) / (nk + 1)  # wrong length

    with pytest.raises(ValueError):
        ut.kernel_density_on_grid(x=x, values=values_bad)

    with pytest.raises(ValueError):
        ut.kernel_density_on_grid(x=x, values=np.ones_like(x), weights=weights_bad)


def test_kernel_density_mp_order_1_normalization():
    """
    For MP kernel with order=1, the integral should still approximate sum_k w_k * sum_b values,
    provided the window and cutoff resolve the kernel tails well.
    """
    nk, nb = 3, 2
    x = np.array(
        [
            [-0.15, 0.05],
            [0.00, 0.10],
            [0.20, 0.30],
        ]
    )
    values = np.ones_like(x)
    weights = np.ones(nk) / nk

    out = ut.kernel_density_on_grid(
        x=x,
        values=values,
        weights=weights,
        center=0.0,
        x_window=1.0,
        sigma=0.06,
        steps=2000,
        order=1,  # Methfessel–Paxton order 1
        cutoff_sigmas=5.0,
    )
    integral = np.trapezoid(out.density, out.grid)
    assert_allclose(integral, nb, rtol=1e-2, atol=1e-2)


def test_kernel_density_window_and_steps_defaults():
    """
    If x_window and steps are None, the function should still produce a sensible grid and density.
    """
    nk, nb = 2, 2
    x = np.array([[0.0, 0.1], [0.2, 0.3]])
    out = ut.kernel_density_on_grid(
        x=x, values=None, weights=None, sigma=None, steps=None, order=0
    )
    # Basic sanity checks
    assert isinstance(out.grid, np.ndarray) or hasattr(out.grid, "magnitude")
    assert isinstance(out.density, np.ndarray) or hasattr(out.density, "magnitude")
    # density and grid lengths must match
    if isinstance(out.grid, np.ndarray):
        assert out.grid.shape == out.density.shape
    else:
        assert out.grid.magnitude.shape == out.density.magnitude.shape


def test_expand_zone_border_shapes_and_units():
    q = np.array([[0.5, 0.0, 0.0], [0, 0, 0]]) * ureg.meter
    with pytest.raises(TypeError):
        expanded = ut._expand_zone_border(q)
    q = np.array([0.5, 0.0, 0.0])
    expanded = ut._expand_zone_border(q)
    assert expanded.shape == (27, 3)
    q = np.array([[0.5, 0.0, 0.0], [0, 0, 0]])
    expanded = ut._expand_zone_border(q)
    assert expanded.shape == (2 * 27, 3)
    # With crystal units preserved
    q_u = q * ureg.crystal
    expanded_u = ut._expand_zone_border(q_u)
    assert isinstance(expanded_u, ureg.Quantity)
    assert expanded_u.check(ureg.crystal)
    assert_allclose(expanded_u.magnitude, expanded)


def test_amplitude2order_parameter():
    # Two atoms, simple displacements
    amps = np.array([0.05, 0.10]) * ureg.angstrom  # length units
    masses = np.array([1.0, 4.0]) * ureg.kilogram  # mass units
    disp0 = np.array([[1.0, 0.0, 0.0], [0.0, 2.0, 0.0]])  # norms: 1 and 2
    disp1 = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 3.0]])  # norms: 1 and 3
    # NN_i = sum_j M_j * ||ε_ij||^2
    # For disp0: 1*1^2 + 4*2^2 = 1 + 16 = 17
    # For disp1: 1*1^2 + 4*3^2 = 1 + 36 = 37
    expected = np.array(
        [amps.magnitude[0] * np.sqrt(17), amps.magnitude[1] * np.sqrt(37)]
    )

    q = ut.amplitude2order_parameter(amps, masses, [disp0, disp1])
    assert isinstance(q, ureg.Quantity)
    # Units: length * sqrt(mass)
    assert q.check("angstrom * kilogram^0.5")
    assert_allclose(q.magnitude, expected)


def test_cumulative_integral_input_validation():
    with pytest.raises(ValueError):
        ut.cumulative_integral(np.array([[0, 1]]), np.array([0, 1]))  # x not 1D
    with pytest.raises(ValueError):
        ut.cumulative_integral(np.array([0, 1]), np.array([0, 1, 2]))  # shape mismatch
    with pytest.raises(ValueError):
        ut.cumulative_integral(
            np.array([0, 0, 1]), np.array([0, 1, 2])
        )  # not strictly increasing


def test_cumulative_integral_linear_function_and_units():
    # y = x => integral = 0.5 x^2
    x = np.linspace(0.0, 2.0, 201)
    y = x.copy()
    I = ut.cumulative_integral(x, y)
    assert_allclose(I, 0.5 * x**2, rtol=1e-6, atol=1e-6)

    # With units: x in m, y in N => integral has units N*m
    x_u = x * ureg.meter
    y_u = y * ureg.newton
    Iu = ut.cumulative_integral(x_u, y_u)
    assert isinstance(Iu, ureg.Quantity)
    assert Iu.check(ureg.newton * ureg.meter)
    assert_allclose(Iu.magnitude, I, rtol=1e-6, atol=1e-6)


def test_point_to_segment_distance():
    # Point on the segment
    A = np.array([0.0, 0.0, 0.0])
    B = np.array([1.0, 0.0, 0.0])
    P_on = np.array([0.3, 0.0, 0.0])
    assert_allclose(ut._point_to_segment_distance(P_on, A, B), 0.0)

    # Point above the middle
    P_above = np.array([0.5, 2.0, 0.0])
    assert_allclose(ut._point_to_segment_distance(P_above, A, B), 2.0)

    # Point nearest to endpoint A
    P_near_A = np.array([-1.0, 1.0, 0.0])
    # The closest point on the segment is A (0,0,0), distance sqrt(2)
    assert_allclose(
        ut._point_to_segment_distance(P_near_A, A, B), np.sqrt(2.0), atol=1e-12
    )


def test_symmetry_orbit_kpoints_matches_2x2x2_grid(data_dir, require):
    """
    For a QE XML with a 2x2x2 Monkhorst-Pack grid, the symmetry orbit
    of IBZ k-points (modulo G) should match the full 2x2x2 grid generated
    by ut.grid_generator (up to ordering).
    """

    fname = data_dir / "qe/results_scf/scf.xml"
    require(fname, f"Missing test data: {fname}")

    # Read symmetries and k-points from file
    syms = grep.symmetries(str(fname))
    data = spectrum.ElectronBands(str(fname))
    # Quantity in _2pi/crystal (expected)
    k_ibz = ut.cartesian2cryst(data.kpoints / data.alat, data.k_lattice)

    # Compute symmetry orbit (modulo G)
    out = ut.symmetry_orbit_kpoints(k_ibz, syms, tol=1e-12, mod_G=True)

    # Build expected 2x2x2 grid in crystal units
    # periodic=True means values in (-0.5, 0.5] for a 2x2x2 mesh
    grid = ut.grid_generator([2, 2, 2], periodic=True)  # ndarray or Quantity

    # Prepare actual orbit set for comparison (float crystal units)
    orbit = out.kpoints.magnitude

    # Compare sets ignoring order: sort rows and compare shape and values
    assert grid.shape == orbit.shape

    # For each expected point, ensure there is an orbit point equivalent mod 1
    def is_close_mod1(a, b, tol=1e-12):
        """
        Check if vectors a and b are equal modulo integers (component-wise), i.e.,
        a - b ≡ 0 (mod 1). Assumes a, b are 1D arrays of length 3.
        """
        d = a - b
        d = d - np.round(d)
        return np.all(np.abs(d) <= tol)

    for kg in grid:
        assert any(
            is_close_mod1(kg, ko, tol=1e-12) for ko in orbit
        ), f"Missing k-point mod 1: {ke}"

    # mod_G requires crystal units; verify unit on output
    assert hasattr(out.kpoints, "units")
    assert out.kpoints.check(ureg("_2pi/crystal"))


def test_find_little_group_silicon(data_dir, require):
    fname = data_dir / "qe/results_scf/scf.xml"
    require(fname, f"Missing test data: {fname}")

    # Read symmetries and k-points from file
    syms = grep.symmetries(str(fname))
    data = spectrum.ElectronBands(str(fname))
    # Quantity in _2pi/crystal (expected)
    k_ibz = ut.cartesian2cryst(data.kpoints / data.alat, data.k_lattice)

    # Compute little_group or original points and points in the orbits
    origin_lg = ut.find_little_group(k_ibz, syms, tol=1e-12)
    orbit = ut.symmetry_orbit_kpoints(k_ibz, syms, tol=1e-12, mod_G=True)
    orbit_lg = ut.find_little_group(orbit.kpoints, syms, tol=1e-12)

    # Check that all little groups of points in the star have the same number of elements
    for i, k in enumerate(orbit.kpoints):
        assert len(orbit_lg[i]) == len(origin_lg[orbit.origin[i]])
