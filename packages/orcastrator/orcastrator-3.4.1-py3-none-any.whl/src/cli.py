"""Command-line interface for Orcastrator."""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from loguru import logger as log

from src.slurm import SlurmScriptConfig

from .config import load_config
from .runner import WorkflowRunner

__version__ = "3.4.1"


def setup_logging(log_file: Path, debug: bool = False) -> None:
    """Configure loguru logging.

    Args:
        log_file: Path to log file
        debug: Enable debug logging
    """
    # Remove default handler
    log.remove()

    # Console handler (INFO or DEBUG)
    log.add(
        sys.stderr,
        format="<level>{level: <8}</level> | <level>{message}</level>",
        level="DEBUG" if debug else "INFO",
        colorize=True,
    )

    # File handler (always DEBUG)
    log.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="DEBUG",
        rotation="10 MB",
    )


@click.group()
@click.version_option(version=__version__, prog_name="orcastrator")
def cli():
    """Orcastrator - ORCA workflow orchestration tool."""
    pass


@cli.command()
@click.argument("config_file", type=click.Path(exists=True, path_type=Path))
@click.option("--debug", is_flag=True, help="Enable debug logging")
def run(config_file: Path, debug: bool):
    """Run ORCA workflow from config file."""
    # Setup logging
    log_file = config_file.with_suffix(".log")
    setup_logging(log_file, debug)

    log.info(f"Orcastrator v{__version__}")
    log.info(f"Config: {config_file}")

    # Load config
    try:
        config = load_config(config_file)
    except Exception as e:
        log.error(f"Failed to load config: {e}")
        sys.exit(1)

    # Override debug setting if CLI flag is set
    if debug:
        config.debug = True

    # Run workflow
    try:
        runner = WorkflowRunner(config)
        results = runner.run()

        # Check for failures
        failed = sum(1 for r in results if not r["success"])
        if failed > 0:
            log.warning(f"{failed} molecules failed")
            sys.exit(1)

    except Exception as e:
        log.exception(f"Workflow failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("config_file", type=click.Path(exists=True, path_type=Path))
@click.option("--no-submit", is_flag=True, help="Generate script but don't submit")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option("--partition", default="normal", help="SLURM partition")
@click.option("--nodes", default=1, help="Number of nodes")
@click.option("--account", default=None, help="SLURM account")
@click.option("--email", default=None, help="Email for notifications")
@click.option(
    "--orca-install-dir",
    default="/soft/orca/orca_6_0_1_linux_x86-64_shared_openmpi416_avx2",
    help="ORCA installation directory",
)
@click.option(
    "--openmpi-install-dir",
    default="/soft/openmpi/openmpi-4.1.6",
    help="OpenMPI installation directory",
)
def slurm(
    config_file: Path,
    no_submit: bool,
    debug: bool,
    partition: str,
    nodes: int,
    account: Optional[str],
    email: Optional[str],
    orca_install_dir: str,
    openmpi_install_dir: str,
):
    """Generate and submit SLURM batch script."""
    # Load config
    try:
        config = load_config(config_file)
    except Exception as e:
        log.error(f"Failed to load config: {e}")
        sys.exit(1)

    # Build orcastrator command
    orcastrator_cmd = "uvx orcastrator run"
    if debug or config.debug:
        orcastrator_cmd += " --debug"
    orcastrator_cmd += f" {config_file.resolve()}"

    # Create SLURM config (CLI options override config file)
    slurm_config = SlurmScriptConfig(
        job_name=config_file.stem,
        ntasks=config.cpus,
        cpus_per_task=1,
        mem_per_cpu_gb=config.mem_per_cpu_gb,
        orcastrator_command=orcastrator_cmd,
        config_file=config_file.resolve(),
        nodes=nodes,
        partition=partition if partition != "normal" else config.slurm.partition,
        nodelist=config.slurm.nodelist if config.slurm.nodelist else None,
        exclude=config.slurm.exclude_nodes if config.slurm.exclude_nodes else None,
        timelimit=config.slurm.timelimit,
        account=account if account is not None else config.slurm.account,
        email=email if email is not None else config.slurm.email,
        orca_install_dir=orca_install_dir
        if orca_install_dir
        != "/soft/orca/orca_6_0_1_linux_x86-64_shared_openmpi416_avx2"
        else config.slurm.orca_install_dir,
        openmpi_install_dir=openmpi_install_dir
        if openmpi_install_dir != "/soft/openmpi/openmpi-4.1.6"
        else config.slurm.openmpi_install_dir,
    )

    # Write script
    slurm_file = config_file.with_suffix(".slurm")
    slurm_config.write_to(slurm_file)

    # Submit if requested
    if not no_submit:
        if not shutil.which("sbatch"):
            log.error("sbatch not found in PATH")
            sys.exit(1)

        result = subprocess.run(
            ["sbatch", str(slurm_file)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            job_id = result.stdout.strip().split()[-1]
            log.info(f"Submitted job: {job_id}")
        else:
            log.error(f"sbatch failed: {result.stderr}")
            sys.exit(1)


@cli.command()
@click.argument("output_file", type=click.Path(path_type=Path), required=False)
@click.option("--slim", "-s", is_flag=True, help="Generate minimal template")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing file")
def init(output_file: Optional[Path] = None, slim: bool = False, force: bool = False):
    """Create a template configuration file."""
    if output_file is None:
        output_file = Path("orcastrator.toml")

    if output_file.exists() and not force:
        log.error(f"File {output_file} already exists (use --force to overwrite)")
        sys.exit(1)

    # Create molecules directory
    mol_dir = output_file.parent / "molecules"
    mol_dir.mkdir(exist_ok=True)

    # Template content
    if slim:
        template = """# Orcastrator Configuration
output_dir = "output"
molecules_dir = "molecules"

cpus = 4
mem_per_cpu_gb = 2
workers = 1

[[stages]]
name = "opt"
simple_keywords = ["D4", "TPSS", "def2-SVP", "OPT"]

[[stages]]
name = "freq"
simple_keywords = ["D4", "TPSS", "def2-SVP", "FREQ"]

[[stages]]
name = "sp"
simple_keywords = ["D4", "TPSSh", "def2-TZVP"]
"""
    else:
        template = (
            """# Orcastrator Configuration (v"""
            + __version__
            + """)

# Core settings (paths relative to this file)
output_dir = "output"
molecules_dir = "molecules"

# Resource settings
cpus = 4
mem_per_cpu_gb = 2
workers = 1
scratch_dir = "/scratch"

# Workflow settings
overwrite = false
debug = false

# Molecule filtering (optional)
# include = ["molecule1", "molecule2"]
# exclude = ["molecule3"]
# Note: Use 'overwrite = true' to rerun all calculations, or rely on automatic caching

# Variable substitution defaults (optional)
# Use {variable_name} in keywords/input_blocks, override in XYZ metadata
[keyword_defaults]
# casscf_roots = 2
# active_electrons = 6

# SLURM settings (optional)
[slurm]
# nodelist = ["node001", "node002"]
# exclude_nodes = ["node003"]
# timelimit = "24:00:00"
# partition = "normal"
# account = "my_account"
# email = "user@example.com"

# Calculation stages (executed in order)
[[stages]]
name = "opt"
simple_keywords = ["D4", "TPSS", "def2-SVP", "OPT"]
# Optional: additional ORCA input blocks
# input_blocks = ["%scf maxiter 150 end"]
# Optional: use variable substitution
# input_blocks = ["%casscf nroot {casscf_roots} end"]

[[stages]]
name = "freq"
simple_keywords = ["D4", "TPSS", "def2-SVP", "FREQ"]
# Optional: override multiplicity
# mult = 3
# Optional: inherit files from previous stage (e.g., wavefunctions)
# inherit = ["*.gbw"]

[[stages]]
name = "sp"
simple_keywords = ["D4", "TPSSh", "def2-TZVP"]
# Optional: inherit files from previous stage
# inherit = ["*.gbw"]
# Optional: use variables in simple_keywords
# simple_keywords = ["CASSCF({active_electrons},{casscf_roots})", "def2-SVP"]
"""
        )

    output_file.write_text(template)
    log.info(f"Created config template: {output_file}")


if __name__ == "__main__":
    cli()
