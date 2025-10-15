"""ORCA execution engine with scratch directory management."""

import os
import shutil
import subprocess
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from loguru import logger as log

from src.config import load_global_config


class OrcaEngine:
    """Handles ORCA execution and scratch directory management."""

    def __init__(
        self,
        scratch_dir: Optional[Path] = None,
        orca_path: Optional[Path] = None,
    ) -> None:
        """Initialize ORCA engine.

        Args:
            scratch_dir: Base directory for scratch files (falls back to global config, then /scratch)
            orca_path: Path to ORCA executable (falls back to global config, then PATH)
        """
        # Load global config for defaults
        global_config = load_global_config()

        # Set up scratch directory (priority: arg > global config > /scratch)
        if scratch_dir is None:
            scratch_dir = global_config.scratch_dir or Path("/scratch")

        if scratch_dir.exists():
            self.scratch_dir = scratch_dir
        else:
            self.scratch_dir = Path("/tmp")
            log.warning(
                f"Scratch dir {scratch_dir} not found, using {self.scratch_dir}"
            )

        # Incorporate SLURM job ID if running under SLURM
        if slurm_job_id := os.getenv("SLURM_JOB_ID"):
            self.scratch_dir = self.scratch_dir / slurm_job_id
            self.scratch_dir.mkdir(parents=True, exist_ok=True)

        log.debug(f"Scratch directory: {self.scratch_dir}")

        # Find ORCA executable (priority: arg > global config > PATH)
        if orca_path is None:
            orca_path = global_config.orca_path

        if orca_path:
            self.orca_path = orca_path.resolve()
            if not self.orca_path.is_file():
                raise FileNotFoundError(f"ORCA executable not found: {orca_path}")
        else:
            orca_which = shutil.which("orca")
            if not orca_which:
                raise RuntimeError("ORCA executable not found in PATH")
            self.orca_path = Path(orca_which).resolve()

        log.debug(f"ORCA executable: {self.orca_path}")

    @contextmanager
    def scratch_context(self, calc_name: str) -> Iterator[Path]:
        """Create temporary scratch directory for calculation.

        Args:
            calc_name: Name for the calculation

        Yields:
            Path to scratch directory

        The directory is automatically cleaned up after use.
        """
        unique_id = str(uuid.uuid4())[:8]
        scratch = self.scratch_dir / f"{calc_name}_{unique_id}"

        try:
            scratch.mkdir(parents=True, exist_ok=False)
            log.debug(f"Created scratch: {scratch}")
            yield scratch
        finally:
            if scratch.exists():
                shutil.rmtree(scratch)
                log.debug(f"Cleaned scratch: {scratch}")

    def run(
        self,
        work_dir: Path,
        input_file: Path,
        output_file: Path,
        use_scratch: bool = True,
        molecule_name: Optional[str] = None,
    ) -> subprocess.CompletedProcess:
        """Execute ORCA calculation.

        Args:
            work_dir: Working directory containing input files
            input_file: Input .inp file (must be in work_dir)
            output_file: Output .out file (will be created in work_dir)
            use_scratch: Whether to use scratch directory

        Returns:
            CompletedProcess with returncode and stderr

        Raises:
            FileNotFoundError: If work_dir or input_file don't exist
            ValueError: If input_file not in work_dir
        """
        if not work_dir.is_dir():
            raise FileNotFoundError(f"Work directory not found: {work_dir}")

        if not input_file.is_file():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        if input_file.parent != work_dir:
            raise ValueError("Input file must be in work directory")

        if use_scratch:
            return self._run_in_scratch(
                work_dir, input_file, output_file, molecule_name
            )
        else:
            return self._run_direct(work_dir, input_file, output_file, molecule_name)

    def _run_direct(
        self,
        work_dir: Path,
        input_file: Path,
        output_file: Path,
        molecule_name: Optional[str] = None,
    ) -> subprocess.CompletedProcess:
        """Run ORCA directly in work directory (no scratch)."""
        cmd = [str(self.orca_path), input_file.name]
        log_msg = f"Running ORCA: {work_dir.name}"
        if molecule_name:
            log_msg += f" ({molecule_name})"
        log.info(log_msg)

        with open(output_file, "w") as out_fd:
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                stdout=out_fd,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )

        if result.returncode != 0:
            log.warning(f"ORCA exited with code {result.returncode}")

        return result

    def _run_in_scratch(
        self,
        work_dir: Path,
        input_file: Path,
        output_file: Path,
        molecule_name: Optional[str] = None,
    ) -> subprocess.CompletedProcess:
        """Run ORCA using scratch directory."""
        calc_name = work_dir.name

        with self.scratch_context(calc_name) as scratch:
            # Copy work_dir contents to scratch
            shutil.copytree(work_dir, scratch, dirs_exist_ok=True)

            # Run in scratch
            scratch_input = scratch / input_file.name
            scratch_output = scratch / output_file.name
            result = self._run_direct(
                scratch, scratch_input, scratch_output, molecule_name
            )

            # Copy results back (ignore temp files)
            for item in scratch.iterdir():
                if item.is_file() and not item.name.endswith((".tmp", ".tmp.*")):
                    shutil.copy2(item, work_dir)

        return result
