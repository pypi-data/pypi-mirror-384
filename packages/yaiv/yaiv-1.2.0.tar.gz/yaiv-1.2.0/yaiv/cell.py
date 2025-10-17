"""
YAIV | yaiv.cell
================

This module defines core functions and a container class for crystal structures
used in symmetry analysis, format conversion, and structural manipulation.

It provides a `Cell` class that wraps an ASE Atoms object along with its spglib-compatible
representation. The `Cell` object allows for easy integration with spglib and includes
utility methods to extract and report symmetry information, Wyckoff positions, and
symmetry operations in symbolic form.

The module also includes conversion tools between ASE and spglib formats,
as well as symmetry naming utilities.

Classes
-------
Cell
    Wrapper around ASE Atoms + spglib tuple (lattice, positions, numbers).
    Provides:
    - from_file(path): Read a file and return Cell.
    - from_spglib_tuple(tup): Construct Cell from spglib-format tuple.
    - get_sym_info(symprec=...): Print symbolic symmetry operations and Wyckoff info.
    - get_wyckoff_positions(symprec=...): Group atoms by Wyckoff positions.
    - get_supercell(supercell): Return a repeated Cell object.
    - write_espresso_in(...): Write Quantum ESPRESSO input file.

Functions
---------
ase2spglib(crystal_ase)
    Convert an ASE Atoms object to a spglib tuple (lattice, positions, numbers).

spglib2ase(spglib_crystal)
    Convert a spglib-format tuple back into an ASE Atoms object.

read_spg(file)
    Read a structure file and return its spglib-compatible tuple.

Private Utilities
-----------------
_rot_name(rot, lattice)
    Identify the symbolic name and axis of a rotation matrix (e.g. 'C3', 'm') using its eigenstructure.

Examples
--------
>>> from yaiv.cell import Cell
>>> cell = Cell.from_file("data/POSCAR")
>>> cell.get_sym_info()
SpaceGroup = Fd-3m (227)
...
>>> cell.get_wyckoff_positions()
>>> cell.wyckoff.labels
['a', 'b']
>>> cell.wyckoff.symbols
['Si', 'Si']

See Also
--------
yaiv.defaults : Configuration and default precision values
yaiv.utils    : Utility functions for basis and vector transformations
"""

from types import SimpleNamespace
import re
import os

import numpy as np
import spglib as spg

from ase.io import read, write
from ase import Atoms

from yaiv.defaults.config import defaults as dft
from yaiv.defaults.config import qe_defaults
from yaiv import utils as ut

__all__ = ["read", "write", "read_spg", "ase2spglib", "spglib2ase", "Cell"]


class Cell:
    """
    A wrapper that stores both an ASE Atoms object and the corresponding
    spglib-format tuple (lattice, positions, numbers).

    This class allows use in spglib (via tuple interface) and in ASE (via .atoms).
    Moreover, it adds some extra functionality with custom methods.

    Attributes
    ----------
    atoms : ase.Atoms
        Full ASE Atoms object with chemical info.
    spglib : tuple
        Tuple (lattice, positions, numbers) derived from the Atoms object,
        used for spglib symmetry operations.

    Methods
    -------
    from_file(...)
        Read a structure file using ASE and return a Cell instance.
    from_spglib_tuple(...)
        Initialize from a (lattice, positions, numbers) spglib tuple.
    get_sym_info(...)
        Print a detailed report of symmetry information for the crystal structure.
    get_wyckoff_positions(...)
        Analyze the structure and store information about independent Wyckoff positions.
    get_supercell(...)
        Construct a supercell by repeating the current unit cell along each lattice direction.
    write_espresso_in(...)
        Write Quantum ESPRESSO input file using either default parameters or a template.
    """

    def __init__(
        self,
        lattice: np.ndarray = None,
        positions: np.ndarray = None,
        numbers: np.ndarray = None,
        atoms: Atoms = None,
    ):
        """
        Initialize a Cell object.

        Parameters
        ----------
        lattice : array-like, optional
            3x3 lattice matrix.
        positions : array-like, optional
            Nx3 array of fractional coordinates.
        numbers : array-like, optional
            Length-N array of atomic numbers.
        atoms : Atoms, optional
            Alternative way to initialize with an Atoms object.

        Raises
        ------
        ValueError
            If neither individual arguments nor `ase.Atoms` object is provided correctly.
        """
        if atoms is not None:
            if not isinstance(atoms, Atoms):
                raise ValueError("`atoms` must be an ase.Atoms object.")
            self.atoms = atoms
            self.spglib = ase2spglib(atoms)
        elif lattice is None or positions is None or numbers is None:
            raise ValueError(
                "Must provide either individual components or an `ase.Atoms` object."
            )
        else:
            self.spglib = (np.array(lattice), np.array(positions), np.array(numbers))
            self.atoms = spglib2ase(self.spglib)

    @classmethod
    def from_file(cls, file: str):
        """
        Read a structure file using ASE and return a Cell instance.

        Parameters
        ----------
        file : str
            Path to structure file (e.g. CIF, POSCAR).

        Returns
        -------
        Cell
            A new Cell instance with Atoms and spglib data.
        """
        atoms = read(file)
        return cls(atoms=atoms)

    @classmethod
    def from_spglib_tuple(cls, tup):
        """
        Initialize from a (lattice, positions, numbers) spglib tuple.

        Parameters
        ----------
        tup : tuple
            A 3-tuple (lattice, positions, numbers)

        Returns
        -------
        Cell
            A new Cell instance with Atoms and spglib data.
        """
        lattice, positions, numbers = map(np.array, tup)
        return cls(lattice, positions, numbers)

    def __iter__(self):
        return iter(self.spglib)

    def __getitem__(self, key):
        return self.spglib[key]

    def __len__(self):
        return len(self.spglib)

    def __repr__(self):
        return f"<Cell with {len(self.spglib[2])} atoms>\n\n{self.spglib}"
        return f"\n{self.spglib}"

    def get_sym_info(self, symprec: float = dft.symprec):
        """
        Print a detailed report of symmetry information for the crystal structure.

        This includes:
        - The chemical formula.
        - The space group name and number.
        - Wyckoff positions and equivalent atoms.
        - Site symmetry symbols.
        - A list of all symmetry operations (rotations + translations), with symbolic names (E, Cn, m, I, Sn).

        Parameters
        ----------
        symprec : float, optional
            Symmetry tolerance used by spglib to determine symmetry operations.
            The default is 1e-5. This sets the precision for atomic position comparison.

        Notes
        -----
        This is a diagnostic utility that gives insight into the symmetry content of the crystal.
        It is not meant for structured programmatic use, but rather for human-readable output.
        """
        atoms = spglib2ase(self.spglib)
        print(atoms.get_chemical_formula())
        dataset = spg.get_symmetry_dataset(self.spglib, symprec=symprec)
        print("SpaceGroup =", dataset.international, "(" + str(dataset.number) + ")")
        print()
        print("ATOMS:")
        print(atoms.get_chemical_symbols())
        print("Wyckoffs:")
        print(dataset.wyckoffs)
        print("Equivalent positions:")
        print(dataset.equivalent_atoms)
        print("Site symmetry simbols:")
        print(dataset.site_symmetry_symbols)
        print()
        print("Symmetry Operations:")
        print()
        symmetry = [(r, t) for r, t in zip(dataset.rotations, dataset.translations)]
        for i in range(len(symmetry)):
            rot = symmetry[i][0]
            t = np.around(symmetry[i][1], decimals=3)
            sym = _rot_name(rot, self.spglib[0])
            print(f"{sym.label}", end="")
            if sym.direction_crystal is not None:
                dir_lat = np.round(sym.direction_crystal, 3)
                dir_cart = np.round(sym.direction_cartesian, 3)
                print(f" / [a,b,c] = {dir_lat} / [x,y,z] = {dir_cart}")
            else:
                print()
            # _rot_name(rot, self.spglib[0])
            print(f"{rot} + {t}")

    def get_wyckoff_positions(self, symprec: float = dft.symprec):
        """
        Analyze the structure and store information about independent Wyckoff positions.

        This method identifies groups of symmetry-equivalent atoms using spglib
        and organizes them by Wyckoff label. It stores the results in the attribute
        `self.wyckoff`, which is a SimpleNamespace with the following fields:

        Attributes
        ----------
        self.wyckoff : SimpleNamespace
            A namespace with grouped symmetry information:
                - symbols : list of str
                    Chemical symbol for each independent Wyckoff site.
                - labels : list of str
                    Wyckoff letter (e.g. 'a', 'b', 'c', ...) corresponding to each independent site.
                - positions : list of ndarray, shape (N_i, 3)
                    List of arrays, each containing the fractional coordinates of atoms in a symmetry-equivalent group.
                - indices : list of list of int
                    Indices (in the full structure) of atoms belonging to each Wyckoff group.

        Parameters
        ----------
        symprec : float, optional
            Symmetry tolerance for spglib. Atoms closer than this value are considered equivalent.
        """
        spglib_data = self.spglib
        atoms = spglib2ase(spglib_data)
        dataset = spg.get_symmetry_dataset(spglib_data, symprec=symprec)

        wyckoff_letters = dataset.wyckoffs
        equivalent_atoms = dataset.equivalent_atoms
        symbols = atoms.get_chemical_symbols()

        unique_labels = []
        unique_symbols = []
        grouped_positions = []
        grouped_indices = []

        seen_equiv = []

        for i, eq in enumerate(equivalent_atoms):
            if eq not in seen_equiv:
                # New independent site
                seen_equiv.append(eq)
                unique_symbols.append(symbols[i])
                unique_labels.append(wyckoff_letters[i])
                grouped_positions.append([spglib_data[1][i]])
                grouped_indices.append([i])
            else:
                # Append to existing site
                index = seen_equiv.index(eq)
                grouped_positions[index].append(spglib_data[1][i])
                grouped_indices[index].append(i)

        # Convert positions to arrays
        grouped_positions = [np.array(group) for group in grouped_positions]

        self.wyckoff = SimpleNamespace(
            symbols=unique_symbols,
            labels=unique_labels,
            positions=grouped_positions,
            indices=grouped_indices,
        )

    def get_supercell(self, supercell: list[int] = [1, 1, 1]) -> "Cell":
        """
        Construct a supercell by repeating the current unit cell along each lattice direction.

        This method generates a new `Cell` object representing a supercell formed by tiling
        the original cell along the three lattice vectors.

        Parameters
        ----------
        supercell : list[int], optional
            A list of 3 integers specifying how many times to replicate the cell along
            each lattice direction. Default is [1, 1, 1] (no replication).

        Returns
        -------
        Cell
            A new `Cell` object representing the expanded supercell.
        """

        lattice = np.copy(self[0])  # Original lattice vectors (3x3)
        positions_list = []

        for i in range(supercell[0]):
            for j in range(supercell[1]):
                for k in range(supercell[2]):
                    displacement = np.array([i, j, k])
                    new_pos = self[1] + displacement  # Shift all atoms
                    positions_list.append(new_pos)

        # Stack all positions and flatten to a single (N_atoms × 3) array
        positions = np.vstack(positions_list)

        # Repeat the atomic elements accordingly
        elements = np.tile(self[2], np.prod(supercell))

        # Expand the lattice
        for i in range(3):
            lattice[i] *= supercell[i]
            positions[:, i] /= supercell[i]  # Normalize positions to new cell

        return Cell(lattice, positions, elements)

    def write_espresso_in(self, filename: str = "espresso.pwi", template: str = None):
        """
        Write Quantum ESPRESSO input file using either default parameters or a template.

        If no template is provided, writes a new input using default settings stored
        in `qe_defaults`. If a template is provided, it replaces the structural
        information (cell, atomic positions, nat) in the template with those from
        `self.atoms`.

        Parameters
        ----------
        filename : str
            Output input file name (e.g. 'espresso.pwi').
        template : str
            Optional template input file to use as a base. Only geometry-related fields
            (CELL_PARAMETERS, ATOMIC_POSITIONS, nat) are updated.
        """
        if template is None:
            write(
                filename,
                self.atoms,
                input_data=qe_defaults.input_data,
                kpts=qe_defaults.kpts,
                format="espresso-in",
            )
            return

        # Write a temporary QE input from the structure to extract updated geometry
        write(".tmp.pwi", self.atoms, format="espresso-in")

        # Extract updated geometry info: CELL_PARAMETERS, ATOMIC_POSITIONS, nat
        basis = []
        pos = []
        cell_line = -4
        pos_line = -999999
        nat = 0
        with open(".tmp.pwi", "r") as lines:
            for n, line in enumerate(lines):
                if re.search(r"\bnat\b", line):
                    nat = int(line.split()[2])
                if re.search("CELL_PARAMETERS", line):
                    cell_line = n
                if re.search("ATOMIC_POSITIONS", line):
                    pos_line = n
                if n - cell_line in [1, 2, 3]:
                    basis.append(line)
                if n - pos_line in range(1, nat + 1):
                    pos.append(line)
        os.remove(".tmp.pwi")

        # Open template and inject updated structural info
        write_nat = True
        write_pos = True
        write_basis = True
        K_points = False

        temp = open(template, "r")
        output = open(filename, "w")
        for line in temp:
            if re.search("ibrav", line):
                if "0" not in line:
                    raise ValueError("ERROR: Your template must have ibrav = 0.")
            elif re.search("pseudo_dir", line):
                line = "  pseudo_dir = '$PSEUDO_DIR',\n"
            elif re.search("outdir", line):
                line = "  outdir = './tmp',\n"
            elif re.search("nat*=", line) and write_nat == True:
                line = "  nat=" + str(nat) + ",\n"
                write_nat = False
            elif re.search("POSITIONS", line, re.IGNORECASE) and write_pos == True:
                line = "ATOMIC_POSITIONS {angstrom}\n"
                output.write(line)
                for line in pos:
                    output.write(line)
                write_pos = False
            elif re.search("POINTS", line, re.IGNORECASE):
                K_points = True
            elif re.search("CELL", line, re.IGNORECASE):
                line = "CELL_PARAMETERS {angstrom}\n"
                output.write(line)
                for line in basis:
                    output.write(line)
                K_points = False
            if write_pos == True or K_points == True:
                output.write(line)
        temp.close()
        output.close()


def ase2spglib(crystal_ase: Atoms) -> tuple:
    """
    Convert an ASE Atoms object into the tuple format required by spglib.

    This function extracts the lattice, scaled atomic positions, and atomic numbers
    from an ASE Atoms object and returns them in the standard spglib tuple format:
    (lattice, positions, numbers).

    Parameters
    ----------
    crystal_ase : Atoms
        ASE Atoms object representing the crystal structure.

    Returns
    -------
    spglib_crystal : tuple
        A 3-tuple (lattice, positions, numbers) where:
        - lattice : (3, 3) array of lattice vectors
        - positions : (N, 3) array of scaled atomic positions (fractional)
        - numbers : (N,) array of atomic numbers
    """
    lattice = np.asarray(crystal_ase.get_cell()).copy()
    positions = crystal_ase.get_scaled_positions()
    numbers = crystal_ase.get_atomic_numbers()
    spglib_crystal = (lattice, positions, numbers)
    return spglib_crystal


def spglib2ase(spglib_crystal: tuple) -> Atoms:
    """
        Convert a spglib-format crystal tuple into an ASE Atoms object.

        This function takes a tuple of the form (lattice, positions, numbers),
        as used by spglib, and creates a corresponding ASE Atoms object.
    Parameters
        ----------
        spglib_crystal : tuple
            A 3-tuple (lattice, positions, numbers) as returned by spglib,
            where:
            - lattice : (3, 3) array of lattice vectors
            - positions : (N, 3) array of scaled (fractional) positions
            - numbers : (N,) array of atomic numbers

        Returns
        -------
        ase_crystal : Atoms
            ASE Atoms object representing the crystal structure.
    """
    lattice = spglib_crystal[0]
    positions = spglib_crystal[1]
    numbers = spglib_crystal[2]
    ase_crystal = Atoms(scaled_positions=positions, numbers=numbers, cell=lattice)
    return ase_crystal


def read_spg(file: str) -> tuple:
    """
    Read a crystal structure file and convert it directly to spglib format.

    This function uses ASE's `read()` to load a crystal structure file
    and returns the structure as a tuple in the format required by spglib:
    (lattice, positions, atomic_numbers).

    Parameters
    ----------
    file : str
        Path to the structure file (e.g., CIF, POSCAR, XYZ, etc.) supported by ASE.

    Returns
    -------
    spglib_crystal : tuple
        A 3-tuple (lattice, positions, numbers) where:
        - lattice : (3, 3) array of lattice vectors
        - positions : (N, 3) array of scaled atomic positions (fractional)
        - numbers : (N,) array of atomic numbers
    """
    cryst = read(file)
    spglib_cryst = ase2spglib(cryst)
    return spglib_cryst


def _rot_name(rot: np.ndarray, lattice=np.ndarray):
    """
    Identify the symbolic name and direction of a symmetry operation given by spglib.

    Parameters
    ----------
    rot : ndarray, shape (3, 3)
        Rotation matrix of the symmetry operation.

    lattice : ndarray, shape (3, 3)
        Lattice vectors of the crystal, used to compute Cartesian directions.

    Returns
    -------
    SimpleNamespace
        Object with the following fields:
        - label : str
            Symbolic name of the symmetry element (e.g. 'E', 'C3', 'm', 'I', 'S6')
        - direction_crystal : ndarray or None
            Normalized direction vector in lattice (fractional) coordinates.
        - direction_cartesian : ndarray or None
            Normalized direction vector in Cartesian coordinates.
        - order : int
            Order of the operation (rot^order = identity)
        - det : float
            Determinant of the rotation matrix (+1 or -1)
    """
    E = np.identity(3)
    det = np.linalg.det(rot)
    eigvals, eigvecs = np.linalg.eig(rot)

    # Determine operation order: smallest d such that rot^d ≈ identity
    r = rot.copy()
    d = 1
    while not np.allclose(r, E, atol=1e-6):
        r = r @ rot
        d += 1
        if d > 12:
            break  # fail-safe

    label = "?"
    direction_crystal = None
    direction_cartesian = None

    if np.allclose(rot, E):
        label = "E"
    elif det > 0:  # Proper rotation
        if d > 1:
            idx = np.argmax(np.isclose(eigvals, 1))
            axis = eigvecs[:, idx].real
            direction_crystal = axis / np.linalg.norm(axis)
            direction_cartesian = ut.cryst2cartesian(direction_crystal, lattice)
            direction_cartesian /= np.linalg.norm(direction_cartesian)
            label = f"C{d}"
    elif det < 0:  # Improper rotation
        if d == 2 and np.allclose(rot, -E):
            label = "I"
        else:
            idx = np.argmax(np.isclose(eigvals, -1))
            axis = eigvecs[:, idx].real
            direction_crystal = axis / np.linalg.norm(axis)
            direction_cartesian = ut.cryst2cartesian(direction_crystal, lattice)
            direction_cartesian /= np.linalg.norm(direction_cartesian)
            if d == 1:
                label = "m"
            else:
                label = f"S{d}"

    return SimpleNamespace(
        label=label,
        direction_crystal=direction_crystal,
        direction_cartesian=direction_cartesian,
        order=d,
        det=det,
    )
