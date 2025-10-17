from pathlib import Path
import numpy as np
import pytest

from yaiv import grep
from yaiv.defaults.config import ureg

# ----------------------------------------------------------------------
# Supported kinds per function (centralized)
# ----------------------------------------------------------------------
SUPPORTED_ELECTRON_NUM = {"qe_scf_out", "qe_xml", "outcar", "eigenval"}
SUPPORTED_LATTICE = {
    "qe_scf_in",
    "qe_scf_out",
    "qe_xml",
    "qe_bands_in",
    "matdyn_in",
    "qe_ph_out",
    "qe_dyn",
    "outcar",
    "poscar",
}
SUPPORTED_FERMI = {"qe_xml", "qe_scf_out", "outcar"}
SUPPORTED_ENERGY = {"qe_xml", "qe_scf_out", "outcar"}
SUPPORTED_STRESS = {"qe_scf_out", "outcar"}
SUPPORTED_KPATH = {"qe_bands_in", "matdyn_in", "kpath"}
SUPPORTED_KPTS_E = {"qe_xml", "qe_scf_out", "outcar", "eigenval", "procar"}
SUPPORTED_PROJ = {"procar"}
SUPPORTED_FREQS = {"qe_freq_out"}
SUPPORTED_SYMS = {"qe_xml"}

# ----------------------------------------------------------------------
# External data matrix (filename relative to tests/data, expected kind)
# ----------------------------------------------------------------------
FILES = [
    ("qe/results/Si.scf.pwo", "qe_scf_out"),
    ("qe/results/Si.scf.pwi", "qe_scf_in"),
    ("qe/results/Si.ph.pwo", "qe_ph_out"),
    ("qe/results/Si.bands.pwi", "qe_bands_in"),
    ("qe/results/matdyn.in", "matdyn_in"),
    ("qe/results/Si.dyn1", "qe_dyn"),
    ("qe/results/Si.freq", "qe_freq_out"),
    ("qe/results/Si.proj.pwo", "qe_proj_out"),
    ("qe/results/Si.xml", "qe_xml"),
    ("vasp/RESULTS/PROCAR", "procar"),
    ("vasp/RESULTS/OUTCAR_BS", "outcar"),
    ("vasp/RESULTS/EIGENVAL_BS", "eigenval"),
    ("vasp/KPATH", "kpath"),
    ("vasp/POSCAR", "poscar"),
]
IDS = [f for f, _ in FILES]


@pytest.mark.parametrize("fname, kind", FILES, ids=IDS)
def test_filetype_detection(data_dir, require, fname, kind):
    f = data_dir / fname
    require(f, f"Missing test data: {fname}")
    assert grep._filetype(str(f)) == kind


@pytest.mark.parametrize("fname, kind", FILES, ids=IDS)
def test_electron_num(data_dir, require, fname, kind):
    f = data_dir / fname
    require(f, f"Missing test data: {fname}")

    if kind in SUPPORTED_ELECTRON_NUM:
        ne = grep.electron_num(str(f))
        assert isinstance(ne, int)
        assert ne == 8
    else:
        with pytest.raises(NotImplementedError):
            grep.electron_num(str(f))


@pytest.mark.parametrize("fname, kind", FILES, ids=IDS)
def test_lattice(data_dir, require, fname, kind):
    f = data_dir / fname
    require(f, f"Missing test data: {fname}")

    if kind in SUPPORTED_LATTICE:
        lat = grep.lattice(str(f))
        assert lat.shape == (3, 3)
        assert hasattr(lat, "units")
    else:
        with pytest.raises(NotImplementedError):
            grep.lattice(str(f))


@pytest.mark.parametrize("fname, kind", FILES, ids=IDS)
def test_fermi(data_dir, require, fname, kind):
    f = data_dir / fname
    require(f, f"Missing test data: {fname}")

    if kind in SUPPORTED_FERMI:
        Ef = grep.fermi(str(f))
        assert hasattr(Ef, "units")
        _ = Ef.to(ureg.eV)
    else:
        with pytest.raises(NotImplementedError):
            grep.fermi(str(f))


@pytest.mark.parametrize("fname, kind", FILES, ids=IDS)
def test_total_energy(data_dir, require, fname, kind):
    f = data_dir / fname
    require(f, f"Missing test data: {fname}")

    if kind in SUPPORTED_ENERGY:
        E = grep.total_energy(str(f))
        assert hasattr(E, "units")
        _ = E.to(ureg.Ry)

        if kind in ["qe_scf_out", "qe_xml"]:
            dec = grep.total_energy(str(f), decomposition=True)
            assert hasattr(dec, "F") and hasattr(dec, "U")
            assert dec.F.check(ureg.Ry)
            assert dec.U.check(ureg.Ry)
    else:
        with pytest.raises(NotImplementedError):
            grep.total_energy(str(f))


@pytest.mark.parametrize("fname, kind", FILES, ids=IDS)
def test_stress_tensor(data_dir, require, fname, kind):
    f = data_dir / fname
    require(f, f"Missing test data: {fname}")

    if kind in SUPPORTED_STRESS:
        S = grep.stress_tensor(str(f))
        assert hasattr(S, "units")
        assert S.check(ureg.kbar)
        assert S.magnitude.shape == (3, 3)
    else:
        with pytest.raises(NotImplementedError):
            grep.stress_tensor(str(f))


@pytest.mark.parametrize("fname, kind", FILES, ids=IDS)
def test_kpath(data_dir, require, fname, kind):
    f = data_dir / fname
    require(f, f"Missing test data: {fname}")

    if kind in SUPPORTED_KPATH:
        res = grep.kpath(str(f), labels=True)
        assert hasattr(res, "path") and hasattr(res, "labels")
        assert res.path.check(ureg._2pi / ureg.crystal)
        assert res.path.magnitude.ndim == 2
        assert res.path.magnitude.shape[1] == 4
        assert len(res.labels) >= 2
        assert len(res.labels) == len(res.path)

    else:
        with pytest.raises(NotImplementedError):
            grep.kpath(str(f))


@pytest.mark.parametrize("fname, kind", FILES, ids=IDS)
def test_kpointsEnergies(data_dir, require, fname, kind):
    f = data_dir / fname
    require(f, f"Missing test data: {fname}")

    if kind in SUPPORTED_KPTS_E:
        data = grep.kpointsEnergies(str(f))
        assert data.energies.check("eV")
        assert (
            data.kpoints.check("1/ang")
            or data.kpoints.check("1/crystal")
            or data.kpoints.check("1/alat")
        )
        assert data.weights.ndim == 1
        assert data.energies.magnitude.ndim == 2
        assert data.kpoints.magnitude.ndim == 2

        if kind in SUPPORTED_PROJ:
            assert data.projections is not None
            _ = data.projections(0, 0, 0, 0)
    else:
        with pytest.raises(NotImplementedError):
            grep.kpointsEnergies(str(f))


@pytest.mark.parametrize("fname, kind", FILES, ids=IDS)
def test_kpointsFrequencies(data_dir, require, fname, kind):
    f = data_dir / fname
    require(f, f"Missing test data: {fname}")

    if kind in SUPPORTED_FREQS:
        data = grep.kpointsFrequencies(str(f))
        assert data.frequencies.check(ureg.c / ureg.cm)
        assert data.kpoints.check(ureg._2pi / ureg.alat)
        assert data.frequencies.magnitude.ndim == 2
        assert data.kpoints.magnitude.ndim == 2
    else:
        with pytest.raises(NotImplementedError):
            grep.kpointsFrequencies(str(f))


@pytest.mark.parametrize("fname, kind", FILES, ids=IDS)
def test_dyn_file(data_dir, require, fname, kind):
    f = data_dir / fname
    require(f, f"Missing test data: {fname}")

    if kind == "qe_dyn":
        sys = grep.dyn_file(str(f))
        assert sys.q.check(ureg._2pi / ureg.angstrom)
        assert sys.lattice.check(ureg.angstrom)
        assert sys.freqs.check(ureg.c / ureg.cm)
        assert sys.positions.check(ureg.angstrom)
        assert sys.masses.check(ureg._2m_e)
        assert isinstance(sys.elements, list)
        assert sys.displacements.ndim == 3
    else:
        with pytest.raises(NotImplementedError):
            grep.dyn_file(str(f))


def test_dyn_q_on_results_folder(data_dir):
    results_dir = data_dir / "qe" / "results"
    q_cryst = np.array([0.0, 0.0, 0.0])
    system = grep.dyn_q(q_cryst, str(results_dir), qe_format=True)
    n_ions = len(system.elements)
    assert system.q.check(ureg._2pi / ureg.crystal)
    assert system.dyn.magnitude.ndim == 2
    assert system.dyn.check(ureg("_2m_e * Ry^2 / planck_constant^2"))
    assert system.dyn.shape == (3 * n_ions, 3 * n_ions)


@pytest.mark.parametrize("fname, kind", FILES, ids=IDS)
def test_symmetries_and_symmetry_class(data_dir, require, fname, kind):
    f = data_dir / fname
    require(f, f"Missing test data: {fname}")

    if kind in SUPPORTED_SYMS:
        syms = grep.symmetries(str(f))
        lattice = grep.lattice(str(f))
        # basic content checks
        assert isinstance(syms, list)
        assert len(syms) == 48

        # first symmetry entry sanity
        s0 = syms[0]
        assert isinstance(s0.R, np.ndarray)
        assert np.all(s0.R == np.identity(3))
        assert np.all(s0.t == np.zeros(3))

        # translation is a Quantity with correct units
        assert hasattr(s0, "t")
        print(s0.units)
        assert s0.units == ureg.crystal

        # Check lattice and crystal conversion.
        s1 = syms[1]
        s1.t = np.ones(3)
        new = s1.to_cartesian(lattice).to_crystal(lattice)
        assert np.allclose(s1.R, new.R, rtol=1e-15)
        assert np.allclose(s1.t, new.t, rtol=1e-15)
        assert s1.units == new.units
