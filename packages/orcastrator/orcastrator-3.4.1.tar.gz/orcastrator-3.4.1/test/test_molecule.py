"""Unit tests for molecule module."""

import pytest

from src.molecule import Atom, Molecule


class TestAtom:
    """Tests for Atom class."""

    def test_atom_creation(self):
        """Test creating an atom."""
        atom = Atom("C", 1.0, 2.0, 3.0)
        assert atom.symbol == "C"
        assert atom.x == 1.0
        assert atom.y == 2.0
        assert atom.z == 3.0

    def test_atom_to_xyz_line(self):
        """Test formatting atom as XYZ line."""
        atom = Atom("C", 1.23456789, -2.34567890, 3.45678901)
        line = atom.to_xyz_line()
        assert "C" in line
        assert "1.23456789" in line
        assert "-2.34567890" in line
        assert "3.45678901" in line


class TestMolecule:
    """Tests for Molecule class."""

    def test_molecule_creation(self):
        """Test creating a molecule."""
        atoms = [
            Atom("C", 0.0, 0.0, 0.0),
            Atom("H", 1.0, 0.0, 0.0),
        ]
        mol = Molecule(name="methane", charge=0, mult=1, atoms=atoms)
        assert mol.name == "methane"
        assert mol.charge == 0
        assert mol.mult == 1
        assert len(mol.atoms) == 2

    def test_xyz_geometry(self):
        """Test XYZ geometry string generation."""
        atoms = [
            Atom("C", 0.0, 0.0, 0.0),
            Atom("H", 1.0, 0.0, 0.0),
        ]
        mol = Molecule(name="test", charge=0, mult=1, atoms=atoms)
        geometry = mol.xyz_geometry
        assert "C" in geometry
        assert "H" in geometry
        lines = geometry.split("\n")
        assert len(lines) == 2

    def test_to_orca_input(self):
        """Test ORCA input format generation."""
        atoms = [Atom("C", 0.0, 0.0, 0.0)]
        mol = Molecule(name="test", charge=-1, mult=2, atoms=atoms)
        orca_input = mol.to_orca_input()
        assert "* xyz -1 2" in orca_input
        assert "C" in orca_input
        assert orca_input.endswith("*\n")

    def test_copy_molecule(self):
        """Test copying a molecule."""
        atoms = [Atom("C", 0.0, 0.0, 0.0)]
        mol1 = Molecule(
            name="test", charge=0, mult=1, atoms=atoms, metadata={"key": "value"}
        )
        mol2 = mol1.copy()

        assert mol2.name == mol1.name
        assert mol2.charge == mol1.charge
        assert mol2.mult == mol1.mult
        assert len(mol2.atoms) == len(mol1.atoms)
        assert mol2.metadata == mol1.metadata

        # Ensure it's a deep copy
        mol2.atoms[0].x = 5.0
        assert mol1.atoms[0].x == 0.0

    def test_copy_with_charge_override(self):
        """Test copying with charge override."""
        atoms = [Atom("C", 0.0, 0.0, 0.0)]
        mol1 = Molecule(name="test", charge=0, mult=1, atoms=atoms)
        mol2 = mol1.copy(charge=1)

        assert mol2.charge == 1
        assert mol1.charge == 0

    def test_copy_with_mult_override(self):
        """Test copying with multiplicity override."""
        atoms = [Atom("C", 0.0, 0.0, 0.0)]
        mol1 = Molecule(name="test", charge=0, mult=1, atoms=atoms)
        mol2 = mol1.copy(mult=3)

        assert mol2.mult == 3
        assert mol1.mult == 1


class TestMoleculeXYZParsing:
    """Tests for XYZ file parsing."""

    def test_parse_json_comment(self):
        """Test parsing JSON format comment."""
        comment = '{"charge": -1, "mult": 2, "extra": "data"}'
        metadata = Molecule._parse_xyz_comment(comment)
        assert metadata["charge"] == -1
        assert metadata["mult"] == 2
        assert metadata["extra"] == "data"

    def test_parse_keyvalue_comment(self):
        """Test parsing key=value format comment."""
        comment = "charge=0 mult=1"
        metadata = Molecule._parse_xyz_comment(comment)
        assert metadata["charge"] == 0
        assert metadata["mult"] == 1

    def test_parse_keyvalue_with_string(self):
        """Test parsing key=value with string values."""
        comment = "charge=0 mult=1 basis=def2-SVP"
        metadata = Molecule._parse_xyz_comment(comment)
        assert metadata["charge"] == 0
        assert metadata["mult"] == 1
        assert metadata["basis"] == "def2-SVP"

    def test_parse_empty_comment(self):
        """Test parsing empty comment."""
        comment = ""
        metadata = Molecule._parse_xyz_comment(comment)
        assert metadata == {}

    def test_parse_malformed_json(self):
        """Test parsing malformed JSON falls back gracefully."""
        comment = '{"charge": 0, "mult"'  # Malformed JSON
        metadata = Molecule._parse_xyz_comment(comment)
        # Should fall back to key=value parsing (which finds nothing)
        assert metadata == {}

    def test_from_xyz_file_json(self, tmp_path):
        """Test loading from XYZ file with JSON metadata."""
        xyz_file = tmp_path / "test.xyz"
        xyz_content = """5
{"charge": -1, "mult": 2, "extra_key": "extra_value"}
C    0.00000000    0.00000000    0.00000000
H    1.00000000    0.00000000    0.00000000
H   -0.50000000    0.86602540    0.00000000
H   -0.50000000   -0.43301270    0.75000000
H   -0.50000000   -0.43301270   -0.75000000
"""
        xyz_file.write_text(xyz_content)

        mol = Molecule.from_xyz_file(xyz_file)
        assert mol.name == "test"
        assert mol.charge == -1
        assert mol.mult == 2
        assert len(mol.atoms) == 5
        assert mol.atoms[0].symbol == "C"
        assert mol.metadata["extra_key"] == "extra_value"

    def test_from_xyz_file_keyvalue(self, tmp_path):
        """Test loading from XYZ file with key=value metadata."""
        xyz_file = tmp_path / "molecule.xyz"
        xyz_content = """2
charge=0 mult=1
C    0.0    0.0    0.0
O    1.2    0.0    0.0
"""
        xyz_file.write_text(xyz_content)

        mol = Molecule.from_xyz_file(xyz_file)
        assert mol.name == "molecule"
        assert mol.charge == 0
        assert mol.mult == 1
        assert len(mol.atoms) == 2

    def test_from_xyz_file_with_override(self, tmp_path):
        """Test loading from XYZ file with charge/mult override."""
        xyz_file = tmp_path / "test.xyz"
        xyz_content = """1
{"charge": 0, "mult": 1}
C    0.0    0.0    0.0
"""
        xyz_file.write_text(xyz_content)

        mol = Molecule.from_xyz_file(xyz_file, charge=2, mult=3)
        assert mol.charge == 2
        assert mol.mult == 3

    def test_from_xyz_file_missing_charge_mult(self, tmp_path):
        """Test loading from XYZ file without charge/mult raises error."""
        xyz_file = tmp_path / "test.xyz"
        xyz_content = """1
no charge or mult here
C    0.0    0.0    0.0
"""
        xyz_file.write_text(xyz_content)

        with pytest.raises(ValueError, match="missing charge or mult"):
            Molecule.from_xyz_file(xyz_file)

    def test_from_xyz_file_invalid_atom_count(self, tmp_path):
        """Test loading from XYZ file with wrong atom count."""
        xyz_file = tmp_path / "test.xyz"
        xyz_content = """3
{"charge": 0, "mult": 1}
C    0.0    0.0    0.0
H    1.0    0.0    0.0
"""  # Says 3 atoms but only has 2
        xyz_file.write_text(xyz_content)

        with pytest.raises(ValueError, match="expected 3 atoms"):
            Molecule.from_xyz_file(xyz_file)

    def test_from_xyz_file_invalid_atom_line(self, tmp_path):
        """Test loading from XYZ file with invalid atom line."""
        xyz_file = tmp_path / "test.xyz"
        xyz_content = """1
{"charge": 0, "mult": 1}
C    not_a_number
"""
        xyz_file.write_text(xyz_content)

        with pytest.raises(ValueError, match="Invalid atom line"):
            Molecule.from_xyz_file(xyz_file)

    def test_load_from_directory(self, tmp_path):
        """Test loading multiple molecules from directory."""
        # Create multiple XYZ files
        xyz1 = tmp_path / "mol1.xyz"
        xyz1.write_text("""1
{"charge": 0, "mult": 1}
C    0.0    0.0    0.0
""")

        xyz2 = tmp_path / "mol2.xyz"
        xyz2.write_text("""1
{"charge": 1, "mult": 2}
N    0.0    0.0    0.0
""")

        molecules = Molecule.load_from_directory(tmp_path)
        assert len(molecules) == 2
        assert molecules[0].name == "mol1"
        assert molecules[1].name == "mol2"

    def test_load_from_empty_directory(self, tmp_path):
        """Test loading from directory with no XYZ files."""
        molecules = Molecule.load_from_directory(tmp_path)
        assert molecules == []

    def test_from_optimized_geometry(self, tmp_path):
        """Test creating molecule from optimized geometry."""
        # Create original molecule
        atoms = [Atom("C", 0.0, 0.0, 0.0)]
        original = Molecule(name="original", charge=-1, mult=2, atoms=atoms)

        # Create optimized geometry file
        opt_xyz = tmp_path / "optimized.xyz"
        opt_xyz.write_text("""1
optimized geometry
C    0.5    0.5    0.5
""")

        mol = Molecule.from_optimized_geometry(opt_xyz, original)
        assert mol.charge == original.charge  # Inherited
        assert mol.mult == original.mult  # Inherited
        assert mol.atoms[0].x == 0.5  # New geometry
        assert mol.atoms[0].y == 0.5
        assert mol.atoms[0].z == 0.5
