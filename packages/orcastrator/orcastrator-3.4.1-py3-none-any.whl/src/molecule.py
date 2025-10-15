"""Molecule representation and XYZ file handling."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger as log


@dataclass
class Atom:
    """Represents a single atom in a molecule."""

    symbol: str
    x: float
    y: float
    z: float

    def to_xyz_line(self) -> str:
        """Format atom as XYZ file line."""
        return (
            f"{self.symbol:4}    {self.x:>12.8f}    {self.y:>12.8f}    {self.z:>12.8f}"
        )


@dataclass
class Molecule:
    """Represents a molecule with geometry and properties."""

    name: str
    charge: int
    mult: int
    atoms: List[Atom] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def xyz_geometry(self) -> str:
        """XYZ geometry string (atoms only)."""
        return "\n".join(atom.to_xyz_line() for atom in self.atoms)

    def to_orca_input(self) -> str:
        """Convert to ORCA input format."""
        return f"* xyz {self.charge} {self.mult}\n{self.xyz_geometry}\n*\n"

    def copy(
        self, charge: Optional[int] = None, mult: Optional[int] = None
    ) -> "Molecule":
        """Create a copy with optional charge/mult override."""
        return Molecule(
            name=self.name,
            charge=charge if charge is not None else self.charge,
            mult=mult if mult is not None else self.mult,
            atoms=[Atom(a.symbol, a.x, a.y, a.z) for a in self.atoms],
            metadata=self.metadata.copy(),
        )

    @staticmethod
    def _parse_xyz_comment(comment: str) -> Dict[str, Any]:
        """Parse XYZ comment line for metadata.

        Supports:
        - JSON: {"charge": 1, "mult": 1, "extra": "data"}
        - Key-value: charge=1 mult=1

        Args:
            comment: Comment line from XYZ file

        Returns:
            Dictionary with parsed metadata
        """
        metadata = {}

        # Try JSON first
        try:
            metadata = json.loads(comment.strip())
            return metadata
        except (json.JSONDecodeError, ValueError) as e:
            # If it looks like JSON but failed to parse, log the error
            if comment.strip().startswith("{"):
                log.warning(f"Failed to parse JSON comment: {e}")
                log.debug(f"Comment line: {comment.strip()}")

        # Fall back to key=value parsing
        for token in comment.strip().split():
            if "=" in token:
                key, value = token.split("=", 1)
                try:
                    metadata[key] = int(value)
                except ValueError:
                    metadata[key] = value

        return metadata

    @classmethod
    def from_xyz_file(
        cls,
        xyz_file: Path,
        charge: Optional[int] = None,
        mult: Optional[int] = None,
    ) -> "Molecule":
        """Load molecule from XYZ file.

        Args:
            xyz_file: Path to XYZ file
            charge: Override charge (if None, read from file)
            mult: Override multiplicity (if None, read from file)

        Returns:
            Molecule instance

        Raises:
            ValueError: If file is invalid or missing charge/mult
        """
        lines = xyz_file.read_text().strip().splitlines()

        if len(lines) < 3:
            raise ValueError(f"Invalid XYZ file {xyz_file}: too few lines")

        n_atoms = int(lines[0])
        comment = lines[1]
        atom_lines = lines[2:]

        if len(atom_lines) != n_atoms:
            raise ValueError(
                f"XYZ file {xyz_file}: expected {n_atoms} atoms, found {len(atom_lines)}"
            )

        # Parse metadata
        metadata = cls._parse_xyz_comment(comment)
        file_charge = metadata.get("charge")
        file_mult = metadata.get("mult")

        # Use override or fall back to file values
        final_charge = charge if charge is not None else file_charge
        final_mult = mult if mult is not None else file_mult

        if final_charge is None or final_mult is None:
            raise ValueError(
                f"XYZ file {xyz_file}: missing charge or mult in file and no override provided"
            )

        # Parse atoms
        atoms = []
        for line in atom_lines:
            parts = line.split()
            if len(parts) < 4:
                raise ValueError(f"Invalid atom line in {xyz_file}: {line}")
            symbol, x, y, z = (
                parts[0],
                float(parts[1]),
                float(parts[2]),
                float(parts[3]),
            )
            atoms.append(Atom(symbol, x, y, z))

        return cls(
            name=xyz_file.stem,
            charge=final_charge,
            mult=final_mult,
            atoms=atoms,
            metadata=metadata,
        )

    @classmethod
    def load_from_directory(
        cls,
        directory: Path,
        default_charge: Optional[int] = None,
        default_mult: Optional[int] = None,
    ) -> List["Molecule"]:
        """Load all molecules from a directory of XYZ files.

        Args:
            directory: Directory containing .xyz files
            default_charge: Default charge if not in file
            default_mult: Default multiplicity if not in file

        Returns:
            List of Molecule instances
        """
        xyz_files = sorted(directory.glob("*.xyz"))

        if not xyz_files:
            log.warning(f"No XYZ files found in {directory}")
            return []

        molecules = []
        for xyz_file in xyz_files:
            try:
                mol = cls.from_xyz_file(xyz_file, default_charge, default_mult)
                molecules.append(mol)
            except Exception as e:
                log.error(f"Failed to load {xyz_file}: {e}")

        log.info(f"Loaded {len(molecules)} molecules from {directory}")
        return molecules

    @classmethod
    def from_optimized_geometry(
        cls, xyz_file: Path, original: "Molecule"
    ) -> "Molecule":
        """Create molecule from optimized geometry file.

        Uses name/charge/mult/metadata from original molecule.

        Args:
            xyz_file: Path to optimized .xyz file (from ORCA output)
            original: Original molecule to inherit properties from

        Returns:
            New Molecule with optimized geometry but original properties
        """
        mol = cls.from_xyz_file(xyz_file, charge=original.charge, mult=original.mult)
        # Preserve name and metadata from original molecule
        mol.name = original.name
        mol.metadata = original.metadata.copy()
        return mol
