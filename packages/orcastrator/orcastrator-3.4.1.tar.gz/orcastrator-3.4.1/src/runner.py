"""Workflow runner for executing ORCA calculation pipelines."""

import hashlib
import json
import shutil
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger as log

from .config import StageConfig, WorkflowConfig, substitute_variables
from .engine import OrcaEngine
from .molecule import Molecule


class Calculation:
    """Represents a single ORCA calculation."""

    def __init__(
        self,
        work_dir: Path,
        molecule: Molecule,
        stage: StageConfig,
        cpus: int,
        mem_per_cpu_gb: int,
        engine: OrcaEngine,
        global_keywords: Optional[Dict[str, Any]] = None,
        overwrite: bool = False,
    ):
        self.work_dir = work_dir
        self.molecule = molecule
        self.stage = stage
        self.cpus = cpus
        self.mem_per_cpu_gb = mem_per_cpu_gb
        self.engine = engine
        self.global_keywords = global_keywords or {}
        self.overwrite = overwrite

        self.input_file = work_dir / f"{work_dir.name}.inp"
        self.output_file = work_dir / f"{work_dir.name}.out"

    def build_input(self) -> str:
        """Build ORCA input file content."""
        # Substitute variables in keywords (preserve order)
        substituted_keywords = []
        for kw in self.stage.simple_keywords:
            try:
                substituted_kw = substitute_variables(
                    kw, self.molecule.metadata, self.global_keywords
                )
                substituted_keywords.append(substituted_kw)
            except KeyError as e:
                log.error(
                    f"Variable substitution failed in keywords for {self.molecule.name}: {e}"
                )
                log.debug(f"Keyword: {kw}")
                log.debug(f"Molecule metadata: {self.molecule.metadata}")
                log.debug(f"Global keywords: {self.global_keywords}")
                raise

        # Keywords (preserve order for ORCA)
        simple_keywords = f"! {' '.join(substituted_keywords)}"

        # Blocks with variable substitution
        blocks = []
        for block in self.stage.input_blocks:
            try:
                substituted_block = substitute_variables(
                    block, self.molecule.metadata, self.global_keywords
                )
                blocks.append(substituted_block)
            except KeyError as e:
                log.error(
                    f"Variable substitution failed in blocks for {self.molecule.name}: {e}"
                )
                log.debug(f"Block: {block}")
                log.debug(f"Molecule metadata: {self.molecule.metadata}")
                log.debug(f"Global keywords: {self.global_keywords}")
                raise

        # Add CPU block if needed
        if self.cpus > 1:
            blocks.append(f"%pal nprocs {self.cpus} end")

        # Add memory block
        total_mem_mb = self.mem_per_cpu_gb * 1024
        available_mem_mb = int(total_mem_mb * 0.8)  # 20% reserve
        blocks.append(f"%maxcore {available_mem_mb}")

        blocks_str = "\n".join(blocks)

        # Molecule geometry
        mol_str = self.molecule.to_orca_input()

        return f"{simple_keywords}\n{blocks_str}\n{mol_str}"

    def _content_hash(self) -> str:
        """Generate hash of calculation-relevant content (for caching)."""
        # Only hash things that affect the calculation result
        content = {
            "keywords": sorted(self.stage.simple_keywords),
            "input_blocks": sorted(self.stage.input_blocks),
            "charge": self.molecule.charge,
            "mult": self.molecule.mult,
            "geometry": self.molecule.xyz_geometry,
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    def is_cached(self) -> bool:
        """Check if calculation is already complete and up-to-date."""
        if self.overwrite:
            return False

        if not self.input_file.exists() or not self.output_file.exists():
            return False

        # Check if hash matches
        cache_file = self.work_dir / ".cache"
        if cache_file.exists():
            cached_hash = cache_file.read_text().strip()
            current_hash = self._content_hash()
            if cached_hash != current_hash:
                log.debug(
                    f"Cache miss: hash mismatch for {self.molecule.name}/{self.work_dir.name}"
                )
                return False
        else:
            return False

        # Check if calculation completed successfully
        return self._check_success()

    def _check_success(self) -> bool:
        """Check if ORCA calculation completed successfully."""
        if not self.output_file.exists():
            return False

        output = self.output_file.read_text()

        # Basic success check
        if "****ORCA TERMINATED NORMALLY****" not in output:
            return False

        # Check optimization convergence
        if "opt" in [kw.lower() for kw in self.stage.simple_keywords]:
            convergence_phrases = [
                "THE OPTIMIZATION HAS CONVERGED",
                "OPTIMIZATION RUN DONE",
                "HURRAY",
            ]
            if not any(phrase in output for phrase in convergence_phrases):
                log.warning(
                    f"Optimization did not converge: {self.molecule.name}/{self.work_dir.name}"
                )
                return False

        # Warn about imaginary frequencies
        if "freq" in [kw.lower() for kw in self.stage.simple_keywords]:
            if "***imaginary mode***" in output:
                log.warning(
                    f"Imaginary mode detected: {self.molecule.name}/{self.work_dir.name}"
                )

        return True

    def run(self) -> Tuple[bool, float]:
        """Execute the calculation.

        Returns:
            (success, elapsed_time_seconds)
        """
        start_time = time.time()

        # Check cache
        if self.is_cached():
            log.info(
                f"Cached: {self.molecule.name}/{self.work_dir.name}/{self.stage.name}"
            )
            return True, time.time() - start_time

        # Prepare work directory
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # Write input file
        self.input_file.write_text(self.build_input())

        # Run ORCA
        log.info(
            f"Running: {self.molecule.name}/{self.work_dir.name}/{self.stage.name}"
        )
        try:
            self.engine.run(
                work_dir=self.work_dir,
                input_file=self.input_file,
                output_file=self.output_file,
                use_scratch=True,
                molecule_name=self.molecule.name,
            )
        except Exception as e:
            log.error(f"ORCA execution failed: {e}")
            return False, time.time() - start_time

        # Check success
        success = self._check_success()
        elapsed = time.time() - start_time

        # Write cache if successful
        if success:
            cache_file = self.work_dir / ".cache"
            cache_file.write_text(self._content_hash())
            log.info(
                f"Completed: {self.molecule.name}/{self.work_dir.name}/{self.stage.name} ({elapsed / 60:.1f} min)"
            )
        else:
            log.error(
                f"Failed: {self.molecule.name}/{self.work_dir.name}/{self.stage.name}"
            )

        return success, elapsed


def copy_files_by_pattern(src_dir: Path, dst_dir: Path, patterns: List[str]) -> None:
    """Copy files matching patterns from src to dst.

    Args:
        src_dir: Source directory
        dst_dir: Destination directory
        patterns: List of glob patterns (e.g., ['*.gbw', '*.xyz'])
    """
    dst_dir.mkdir(parents=True, exist_ok=True)

    for pattern in patterns:
        for file in src_dir.glob(pattern):
            if file.is_file():
                shutil.copy2(file, dst_dir)
                log.debug(f"Copied: {file.name} -> {dst_dir.name}")


def run_molecule_workflow(
    molecule: Molecule,
    config: WorkflowConfig,
    engine: OrcaEngine,
) -> Dict:
    """Run complete workflow for a single molecule.

    Args:
        molecule: Molecule to process
        config: Workflow configuration
        engine: ORCA engine instance

    Returns:
        Dictionary with results
    """
    start_time = time.time()
    mol_dir = config.output_dir / molecule.name

    results = {
        "molecule": molecule.name,
        "success": True,
        "stages": [],
        "total_time": 0.0,
    }

    current_molecule = molecule
    previous_stage_dir = None

    cpus_per_worker = config.cpus // config.workers

    for stage in config.stages:
        stage_dir = mol_dir / stage.name

        # Inherit files from previous stage if specified
        if previous_stage_dir and stage.inherit:
            copy_files_by_pattern(previous_stage_dir, stage_dir, stage.inherit)

        # Check if we need to load optimized geometry
        if previous_stage_dir:
            opt_xyz = previous_stage_dir / f"{previous_stage_dir.name}.xyz"
            if opt_xyz.exists():
                try:
                    current_molecule = Molecule.from_optimized_geometry(
                        opt_xyz, current_molecule
                    )
                except Exception as e:
                    log.warning(f"Could not load optimized geometry: {e}")

        # Override charge/mult if specified in stage
        if stage.charge is not None or stage.mult is not None:
            current_molecule = current_molecule.copy(
                charge=stage.charge, mult=stage.mult
            )

        # Create and run calculation
        calc = Calculation(
            work_dir=stage_dir,
            molecule=current_molecule,
            stage=stage,
            cpus=cpus_per_worker,
            mem_per_cpu_gb=config.mem_per_cpu_gb,
            engine=engine,
            global_keywords=config.keyword_defaults,
            overwrite=config.overwrite,
        )

        success, elapsed = calc.run()

        results["stages"].append(
            {
                "name": stage.name,
                "success": success,
                "time": elapsed,
            }
        )

        if not success:
            results["success"] = False
            break

        previous_stage_dir = stage_dir

    results["total_time"] = time.time() - start_time

    return results


class WorkflowRunner:
    """Orchestrates parallel execution of molecule workflows."""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.engine = OrcaEngine(scratch_dir=config.scratch_dir)

    def load_molecules(self) -> List[Molecule]:
        """Load and filter molecules based on config."""
        all_molecules = Molecule.load_from_directory(self.config.molecules_dir)

        # Apply filters
        molecules = all_molecules

        if self.config.include:
            include_set = set(self.config.include)
            molecules = [m for m in molecules if m.name in include_set]
            log.info(f"Including only: {self.config.include}")

        if self.config.exclude:
            exclude_set = set(self.config.exclude)
            molecules = [m for m in molecules if m.name not in exclude_set]
            log.info(f"Excluding: {self.config.exclude}")

        return molecules

    def run(self) -> List[Dict]:
        """Execute workflow for all molecules in parallel.

        Returns:
            List of result dictionaries
        """
        molecules = self.load_molecules()

        if not molecules:
            log.warning("No molecules to process")
            return []

        log.info(
            f"Processing {len(molecules)} molecules with {self.config.workers} workers"
        )

        start_time = time.time()
        results = []

        # Run in parallel
        with ProcessPoolExecutor(max_workers=self.config.workers) as executor:
            futures = {
                executor.submit(
                    run_molecule_workflow, mol, self.config, self.engine
                ): mol
                for mol in molecules
            }

            for future in as_completed(futures):
                mol = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    log.error(f"Failed to process {mol.name}: {e}")
                    results.append(
                        {
                            "molecule": mol.name,
                            "success": False,
                            "error": str(e),
                            "stages": [],
                            "total_time": 0.0,
                        }
                    )

        # Save results
        self._save_results(results)

        # Print summary
        self._print_summary(results, time.time() - start_time)

        return results

    def _save_results(self, results: List[Dict]) -> None:
        """Save results to JSON file."""
        results_file = self.config.output_dir / ".results.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        results_file.write_text(json.dumps(results, indent=2))
        log.debug(f"Saved results to {results_file}")

    def _print_summary(self, results: List[Dict], total_time: float) -> None:
        """Print workflow summary."""
        total = len(results)
        successful = sum(1 for r in results if r["success"])
        failed = total - successful

        log.info("=" * 60)
        log.info("WORKFLOW SUMMARY")
        log.info("=" * 60)
        log.info(f"Total time: {total_time / 60:.1f} min ({total_time / 3600:.2f} hr)")
        log.info(f"Molecules: {total} total, {successful} successful, {failed} failed")

        if total > 0:
            avg_time = sum(r["total_time"] for r in results) / total
            log.info(f"Average time per molecule: {avg_time / 60:.1f} min")

        if failed > 0:
            log.info("Failed molecules:")
            for r in results:
                if not r["success"]:
                    failed_stage = next(
                        (s["name"] for s in r["stages"] if not s["success"]), "unknown"
                    )
                    log.info(f"  - {r['molecule']} (failed at: {failed_stage})")

        log.info("=" * 60)
