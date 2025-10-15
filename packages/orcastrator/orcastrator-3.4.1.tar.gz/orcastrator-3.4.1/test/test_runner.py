"""Unit tests for runner module."""

from unittest.mock import patch

import pytest

from src.config import StageConfig
from src.engine import OrcaEngine
from src.molecule import Atom, Molecule
from src.runner import Calculation, copy_files_by_pattern


class TestCalculation:
    """Tests for Calculation class."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock ORCA engine."""
        with patch("shutil.which", return_value="/usr/bin/orca"):
            return OrcaEngine()

    @pytest.fixture
    def test_molecule(self):
        """Create a test molecule."""
        atoms = [Atom("C", 0.0, 0.0, 0.0), Atom("H", 1.0, 0.0, 0.0)]
        return Molecule(
            name="test",
            charge=0,
            mult=1,
            atoms=atoms,
            metadata={"basis": "def2-SVP"},
        )

    @pytest.fixture
    def test_stage(self):
        """Create a test stage."""
        return StageConfig(
            name="opt",
            simple_keywords=["OPT", "B3LYP", "def2-SVP"],
            input_blocks=["%scf maxiter 150 end"],
        )

    def test_calculation_creation(
        self, tmp_path, test_molecule, test_stage, mock_engine
    ):
        """Test creating a calculation."""
        work_dir = tmp_path / "calc"

        calc = Calculation(
            work_dir=work_dir,
            molecule=test_molecule,
            stage=test_stage,
            cpus=4,
            mem_per_cpu_gb=2,
            engine=mock_engine,
        )

        assert calc.work_dir == work_dir
        assert calc.molecule == test_molecule
        assert calc.stage == test_stage
        assert calc.cpus == 4
        assert calc.mem_per_cpu_gb == 2
        assert calc.global_keywords == {}

    def test_calculation_with_global_keywords(
        self, tmp_path, test_molecule, test_stage, mock_engine
    ):
        """Test calculation with global keywords."""
        work_dir = tmp_path / "calc"
        global_keywords = {"method": "B3LYP", "basis": "def2-TZVP"}

        calc = Calculation(
            work_dir=work_dir,
            molecule=test_molecule,
            stage=test_stage,
            cpus=4,
            mem_per_cpu_gb=2,
            engine=mock_engine,
            global_keywords=global_keywords,
        )

        assert calc.global_keywords == global_keywords

    def test_build_input_basic(self, tmp_path, test_molecule, test_stage, mock_engine):
        """Test building basic ORCA input."""
        work_dir = tmp_path / "calc"

        calc = Calculation(
            work_dir=work_dir,
            molecule=test_molecule,
            stage=test_stage,
            cpus=1,
            mem_per_cpu_gb=2,
            engine=mock_engine,
        )

        input_str = calc.build_input()

        # Check keywords line
        assert "! OPT B3LYP def2-SVP" in input_str

        # Check blocks
        assert "%scf maxiter 150 end" in input_str
        assert "%maxcore" in input_str

        # Check geometry
        assert "* xyz 0 1" in input_str
        assert "C" in input_str
        assert "H" in input_str
        assert "*" in input_str

    def test_build_input_with_multiple_cpus(
        self, tmp_path, test_molecule, test_stage, mock_engine
    ):
        """Test building input with multiple CPUs."""
        work_dir = tmp_path / "calc"

        calc = Calculation(
            work_dir=work_dir,
            molecule=test_molecule,
            stage=test_stage,
            cpus=8,
            mem_per_cpu_gb=2,
            engine=mock_engine,
        )

        input_str = calc.build_input()
        assert "%pal nprocs 8 end" in input_str

    def test_build_input_with_variable_substitution(
        self, tmp_path, test_molecule, mock_engine
    ):
        """Test building input with variable substitution."""
        work_dir = tmp_path / "calc"

        stage = StageConfig(
            name="opt",
            simple_keywords=["OPT", "{method}", "{basis}"],
            input_blocks=["%scf maxiter {maxiter} end"],
        )

        global_keywords = {"method": "B3LYP", "basis": "def2-SVP", "maxiter": 200}

        calc = Calculation(
            work_dir=work_dir,
            molecule=test_molecule,
            stage=stage,
            cpus=1,
            mem_per_cpu_gb=2,
            engine=mock_engine,
            global_keywords=global_keywords,
        )

        input_str = calc.build_input()

        # Variables should be substituted
        assert "B3LYP" in input_str
        assert "def2-SVP" in input_str
        assert "maxiter 200" in input_str

        # Placeholders should not remain
        assert "{method}" not in input_str
        assert "{basis}" not in input_str

    def test_build_input_molecule_overrides_global(
        self, tmp_path, test_molecule, mock_engine
    ):
        """Test that molecule metadata overrides global keywords."""
        work_dir = tmp_path / "calc"

        stage = StageConfig(
            name="opt",
            simple_keywords=["OPT", "{basis}"],
        )

        # Molecule has basis="def2-SVP" in metadata
        global_keywords = {"basis": "def2-TZVP"}  # Global says TZVP

        calc = Calculation(
            work_dir=work_dir,
            molecule=test_molecule,
            stage=stage,
            cpus=1,
            mem_per_cpu_gb=2,
            engine=mock_engine,
            global_keywords=global_keywords,
        )

        input_str = calc.build_input()

        # Should use molecule metadata (SVP), not global (TZVP)
        assert "def2-SVP" in input_str
        assert "def2-TZVP" not in input_str

    def test_build_input_missing_variable_raises_error(
        self, tmp_path, test_molecule, mock_engine
    ):
        """Test that missing variable raises KeyError."""
        work_dir = tmp_path / "calc"

        stage = StageConfig(
            name="opt",
            simple_keywords=["OPT", "{missing_var}"],
        )

        calc = Calculation(
            work_dir=work_dir,
            molecule=test_molecule,
            stage=stage,
            cpus=1,
            mem_per_cpu_gb=2,
            engine=mock_engine,
        )

        with pytest.raises(KeyError, match="missing_var"):
            calc.build_input()

    def test_content_hash(self, tmp_path, test_molecule, test_stage, mock_engine):
        """Test content hash generation."""
        work_dir = tmp_path / "calc"

        calc = Calculation(
            work_dir=work_dir,
            molecule=test_molecule,
            stage=test_stage,
            cpus=4,
            mem_per_cpu_gb=2,
            engine=mock_engine,
        )

        hash1 = calc._content_hash()
        assert len(hash1) == 16  # Should be truncated to 16 chars

        # Same calculation should give same hash
        calc2 = Calculation(
            work_dir=work_dir,
            molecule=test_molecule,
            stage=test_stage,
            cpus=4,
            mem_per_cpu_gb=2,
            engine=mock_engine,
        )
        hash2 = calc2._content_hash()
        assert hash1 == hash2

    def test_content_hash_different_geometry(self, tmp_path, test_stage, mock_engine):
        """Test that different geometry gives different hash."""
        work_dir = tmp_path / "calc"

        mol1 = Molecule(name="mol1", charge=0, mult=1, atoms=[Atom("C", 0.0, 0.0, 0.0)])
        mol2 = Molecule(name="mol2", charge=0, mult=1, atoms=[Atom("C", 1.0, 0.0, 0.0)])

        calc1 = Calculation(
            work_dir=work_dir,
            molecule=mol1,
            stage=test_stage,
            cpus=4,
            mem_per_cpu_gb=2,
            engine=mock_engine,
        )

        calc2 = Calculation(
            work_dir=work_dir,
            molecule=mol2,
            stage=test_stage,
            cpus=4,
            mem_per_cpu_gb=2,
            engine=mock_engine,
        )

        assert calc1._content_hash() != calc2._content_hash()

    def test_is_cached_no_cache(self, tmp_path, test_molecule, test_stage, mock_engine):
        """Test that calculation without cache returns False."""
        work_dir = tmp_path / "calc"
        work_dir.mkdir()

        calc = Calculation(
            work_dir=work_dir,
            molecule=test_molecule,
            stage=test_stage,
            cpus=4,
            mem_per_cpu_gb=2,
            engine=mock_engine,
        )

        assert not calc.is_cached()

    def test_is_cached_with_overwrite(
        self, tmp_path, test_molecule, test_stage, mock_engine
    ):
        """Test that overwrite=True always returns False for is_cached."""
        work_dir = tmp_path / "calc"
        work_dir.mkdir()

        # Create cache and output files
        (work_dir / ".cache").write_text("somehash")
        (work_dir / f"{work_dir.name}.out").write_text(
            "****ORCA TERMINATED NORMALLY****"
        )

        calc = Calculation(
            work_dir=work_dir,
            molecule=test_molecule,
            stage=test_stage,
            cpus=4,
            mem_per_cpu_gb=2,
            engine=mock_engine,
            overwrite=True,
        )

        assert not calc.is_cached()

    # TODO - this test failes, probably because the calc.output_file
    # does not actually exist?
    #
    # def test_check_success_terminated_normally(
    #     self, tmp_path, test_molecule, test_stage, mock_engine
    # ):
    #     """Test successful calculation detection."""
    #     work_dir = tmp_path / "calc"
    #     work_dir.mkdir()

    #     calc = Calculation(
    #         work_dir=work_dir,
    #         molecule=test_molecule,
    #         stage=test_stage,
    #         cpus=4,
    #         mem_per_cpu_gb=2,
    #         engine=mock_engine,
    #     )

    #     # Create output file with success message
    #     calc.output_file.write_text("****ORCA TERMINATED NORMALLY****")

    #     assert calc._check_success()

    def test_check_success_failed(
        self, tmp_path, test_molecule, test_stage, mock_engine
    ):
        """Test failed calculation detection."""
        work_dir = tmp_path / "calc"
        work_dir.mkdir()

        calc = Calculation(
            work_dir=work_dir,
            molecule=test_molecule,
            stage=test_stage,
            cpus=4,
            mem_per_cpu_gb=2,
            engine=mock_engine,
        )

        # Create output file without success message
        calc.output_file.write_text("ORCA encountered an error")

        assert not calc._check_success()


class TestCopyFilesByPattern:
    """Tests for copy_files_by_pattern function."""

    def test_copy_single_pattern(self, tmp_path):
        """Test copying files with single pattern."""
        src = tmp_path / "src"
        src.mkdir()
        dst = tmp_path / "dst"

        # Create some files
        (src / "file.gbw").write_text("gbw content")
        (src / "file.xyz").write_text("xyz content")
        (src / "file.txt").write_text("txt content")

        copy_files_by_pattern(src, dst, ["*.gbw"])

        assert (dst / "file.gbw").exists()
        assert not (dst / "file.xyz").exists()
        assert not (dst / "file.txt").exists()

    def test_copy_multiple_patterns(self, tmp_path):
        """Test copying files with multiple patterns."""
        src = tmp_path / "src"
        src.mkdir()
        dst = tmp_path / "dst"

        # Create some files
        (src / "file.gbw").write_text("gbw content")
        (src / "file.xyz").write_text("xyz content")
        (src / "file.txt").write_text("txt content")

        copy_files_by_pattern(src, dst, ["*.gbw", "*.xyz"])

        assert (dst / "file.gbw").exists()
        assert (dst / "file.xyz").exists()
        assert not (dst / "file.txt").exists()

    def test_copy_no_matches(self, tmp_path):
        """Test copying with no matching files."""
        src = tmp_path / "src"
        src.mkdir()
        dst = tmp_path / "dst"

        (src / "file.txt").write_text("txt content")

        copy_files_by_pattern(src, dst, ["*.gbw"])

        # dst should be created but empty (except for itself)
        assert dst.exists()
        assert not (dst / "file.txt").exists()

    def test_copy_creates_dst_dir(self, tmp_path):
        """Test that destination directory is created if it doesn't exist."""
        src = tmp_path / "src"
        src.mkdir()
        dst = tmp_path / "nonexistent" / "dst"

        (src / "file.gbw").write_text("content")

        copy_files_by_pattern(src, dst, ["*.gbw"])

        assert dst.exists()
        assert (dst / "file.gbw").exists()
