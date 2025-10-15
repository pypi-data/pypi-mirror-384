"""Unit tests for engine module."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.engine import OrcaEngine


class TestOrcaEngine:
    """Tests for OrcaEngine class."""

    def test_engine_creation_default_scratch(self, tmp_path):
        """Test creating engine with default scratch directory."""
        with patch("shutil.which", return_value="/usr/bin/orca"):
            engine = OrcaEngine()
            # Should fall back to /tmp if /scratch doesn't exist
            assert engine.scratch_dir in [Path("/scratch"), Path("/tmp")]
            assert engine.orca_path == Path("/usr/bin/orca")

    def test_engine_creation_custom_scratch(self, tmp_path):
        """Test creating engine with custom scratch directory."""
        scratch = tmp_path / "scratch"
        scratch.mkdir()

        with patch("shutil.which", return_value="/usr/bin/orca"):
            engine = OrcaEngine(scratch_dir=scratch)
            assert engine.scratch_dir == scratch

    def test_engine_creation_nonexistent_scratch(self, tmp_path):
        """Test creating engine with nonexistent scratch falls back to /tmp."""
        nonexistent = tmp_path / "nonexistent"

        with patch("shutil.which", return_value="/usr/bin/orca"):
            engine = OrcaEngine(scratch_dir=nonexistent)
            assert engine.scratch_dir == Path("/tmp")

    def test_engine_creation_with_orca_path(self, tmp_path):
        """Test creating engine with explicit ORCA path."""
        orca_path = tmp_path / "orca"
        orca_path.write_text("#!/bin/bash\necho orca")

        engine = OrcaEngine(orca_path=orca_path)
        assert engine.orca_path == orca_path

    def test_engine_creation_orca_not_found(self):
        """Test creating engine when ORCA not found raises error."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="ORCA executable not found"):
                OrcaEngine()

    def test_engine_creation_invalid_orca_path(self, tmp_path):
        """Test creating engine with invalid ORCA path raises error."""
        invalid_path = tmp_path / "nonexistent_orca"

        with pytest.raises(FileNotFoundError, match="ORCA executable not found"):
            OrcaEngine(orca_path=invalid_path)

    def test_engine_with_slurm_job_id(self, tmp_path):
        """Test that engine creates subdirectory when SLURM_JOB_ID is set."""
        scratch = tmp_path / "scratch"
        scratch.mkdir()

        with patch("shutil.which", return_value="/usr/bin/orca"):
            with patch.dict(os.environ, {"SLURM_JOB_ID": "12345"}):
                engine = OrcaEngine(scratch_dir=scratch)
                assert engine.scratch_dir == scratch / "12345"
                assert engine.scratch_dir.exists()

    def test_scratch_context(self, tmp_path):
        """Test scratch context manager creates and cleans up directory."""
        scratch = tmp_path / "scratch"
        scratch.mkdir()

        with patch("shutil.which", return_value="/usr/bin/orca"):
            engine = OrcaEngine(scratch_dir=scratch)

            with engine.scratch_context("test_calc") as scratch_dir:
                assert scratch_dir.exists()
                assert scratch_dir.parent == scratch
                assert "test_calc" in scratch_dir.name

                # Create a file in scratch
                test_file = scratch_dir / "test.txt"
                test_file.write_text("test")
                assert test_file.exists()

            # After context, scratch should be cleaned up
            assert not scratch_dir.exists()

    def test_scratch_context_with_error(self, tmp_path):
        """Test that scratch context cleans up even on error."""
        scratch = tmp_path / "scratch"
        scratch.mkdir()

        with patch("shutil.which", return_value="/usr/bin/orca"):
            engine = OrcaEngine(scratch_dir=scratch)

            scratch_dir = None
            try:
                with engine.scratch_context("test_calc") as sd:
                    scratch_dir = sd
                    assert scratch_dir.exists()
                    raise ValueError("Test error")
            except ValueError:
                pass

            # Even with error, scratch should be cleaned up
            assert not scratch_dir.exists()  # type: ignore # scratch_dir should be None - we shoudln't reach this

    def test_run_direct_success(self, tmp_path):
        """Test running ORCA directly (no scratch)."""
        work_dir = tmp_path / "work"
        work_dir.mkdir()

        input_file = work_dir / "input.inp"
        input_file.write_text("! B3LYP def2-SVP\n* xyz 0 1\nH 0 0 0\n*")

        output_file = work_dir / "output.out"

        # Mock ORCA execution
        with patch("shutil.which", return_value="/usr/bin/orca"):
            engine = OrcaEngine()

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stderr="")

                result = engine.run(
                    work_dir=work_dir,
                    input_file=input_file,
                    output_file=output_file,
                    use_scratch=False,
                )

                assert result.returncode == 0
                mock_run.assert_called_once()

    def test_run_with_scratch(self, tmp_path):
        """Test running ORCA with scratch directory."""
        work_dir = tmp_path / "work"
        work_dir.mkdir()

        input_file = work_dir / "input.inp"
        input_file.write_text("! B3LYP def2-SVP")

        output_file = work_dir / "output.out"

        scratch = tmp_path / "scratch"
        scratch.mkdir()

        with patch("shutil.which", return_value="/usr/bin/orca"):
            engine = OrcaEngine(scratch_dir=scratch)

            with patch("subprocess.run") as mock_run:
                # Mock successful ORCA run
                def fake_run(*args, **kwargs):
                    # Create output file in the scratch directory
                    cwd = kwargs.get("cwd")
                    if cwd:
                        out_file = cwd / "output.out"
                        out_file.write_text("ORCA output")
                    return MagicMock(returncode=0, stderr="")

                mock_run.side_effect = fake_run

                result = engine.run(
                    work_dir=work_dir,
                    input_file=input_file,
                    output_file=output_file,
                    use_scratch=True,
                )

                assert result.returncode == 0

    def test_run_work_dir_not_found(self, tmp_path):
        """Test that run raises error if work_dir doesn't exist."""
        work_dir = tmp_path / "nonexistent"
        input_file = work_dir / "input.inp"
        output_file = work_dir / "output.out"

        with patch("shutil.which", return_value="/usr/bin/orca"):
            engine = OrcaEngine()

            with pytest.raises(FileNotFoundError, match="Work directory not found"):
                engine.run(work_dir, input_file, output_file)

    def test_run_input_file_not_found(self, tmp_path):
        """Test that run raises error if input_file doesn't exist."""
        work_dir = tmp_path / "work"
        work_dir.mkdir()

        input_file = work_dir / "nonexistent.inp"
        output_file = work_dir / "output.out"

        with patch("shutil.which", return_value="/usr/bin/orca"):
            engine = OrcaEngine()

            with pytest.raises(FileNotFoundError, match="Input file not found"):
                engine.run(work_dir, input_file, output_file)

    def test_run_input_file_not_in_work_dir(self, tmp_path):
        """Test that run raises error if input_file not in work_dir."""
        work_dir = tmp_path / "work"
        work_dir.mkdir()

        other_dir = tmp_path / "other"
        other_dir.mkdir()

        input_file = other_dir / "input.inp"
        input_file.write_text("test")

        output_file = work_dir / "output.out"

        with patch("shutil.which", return_value="/usr/bin/orca"):
            engine = OrcaEngine()

            with pytest.raises(
                ValueError, match="Input file must be in work directory"
            ):
                engine.run(work_dir, input_file, output_file)

    def test_run_nonzero_exit_code(self, tmp_path):
        """Test that run handles nonzero exit code."""
        work_dir = tmp_path / "work"
        work_dir.mkdir()

        input_file = work_dir / "input.inp"
        input_file.write_text("! B3LYP def2-SVP")

        output_file = work_dir / "output.out"

        with patch("shutil.which", return_value="/usr/bin/orca"):
            engine = OrcaEngine()

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stderr="ORCA error")

                result = engine.run(
                    work_dir=work_dir,
                    input_file=input_file,
                    output_file=output_file,
                    use_scratch=False,
                )

                assert result.returncode == 1
