"""SLURM batch script generation for cluster execution."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from jinja2 import Template
from loguru import logger as log

SLURM_SCRIPT_TEMPLATE = """\
#!/bin/bash
#SBATCH --job-name={{ job_name }}
#SBATCH --partition={{ partition }}
#SBATCH --nodes={{ nodes }}
#SBATCH --ntasks={{ ntasks }}
#SBATCH --cpus-per-task={{ cpus_per_task }}
#SBATCH --mem-per-cpu={{ mem_per_cpu_gb }}GB
{% if timelimit %}#SBATCH --time={{ timelimit }}{% else %}#SBATCH --time={{ time_h }}:00:00{% endif %}
#SBATCH --output=logs/%x-%j.slurm.log
#SBATCH --error=logs/%x-%j.slurm.log
{% if nodelist and nodelist|length > 0 %}#SBATCH --nodelist={{ nodelist | join(',') }}{% endif %}
{% if exclude and exclude|length > 0 %}#SBATCH --exclude={{ exclude | join(',') }}{% endif %}
{% if account %}#SBATCH --account={{ account }}{% endif %}
{% if email %}
#SBATCH --mail-user={{ email }}
#SBATCH --mail-type={{ email_type | default("END,FAIL") }}
{% endif %}

echo "======================================================"
echo "Job started at $(date)"
echo "SLURM Job ID: $SLURM_JOB_ID"
echo "SLURM Job Name: $SLURM_JOB_NAME"
echo "Running on node(s): $SLURM_JOB_NODELIST"
echo "Working directory: $(pwd)"
echo "Memory per CPU: {{ mem_per_cpu_gb }}GB"
echo "======================================================"
echo ""

# Create logs directory
CONFIG_DIR=$(dirname "{{ config_file }}")
LOG_DIR="${CONFIG_DIR}/logs"
mkdir -p "${LOG_DIR}"

# Environment setup
echo "Setting up environment..."
export ORCA_INSTALL_DIR="{{ orca_install_dir }}"
export OPENMPI_INSTALL_DIR="{{ openmpi_install_dir }}"

export PATH="${ORCA_INSTALL_DIR}:${OPENMPI_INSTALL_DIR}/bin:${PATH}"
export LD_LIBRARY_PATH="${ORCA_INSTALL_DIR}/lib:${OPENMPI_INSTALL_DIR}/lib64:${LD_LIBRARY_PATH}"

# Enable debug logging
export ORCASTRATOR_DEBUG=1
export ORCASTRATOR_LOG_DIR="${LOG_DIR}"

# Run Orcastrator
uvx orcastrator --version
echo "Running command: {{ orcastrator_command }}"
echo "------------------------------------------------------"
{{ orcastrator_command }}
ORCASTRATOR_EXIT_CODE=$?
echo "------------------------------------------------------"
echo ""

echo "======================================================"
echo "Job finished at $(date)"
echo "======================================================"

exit $ORCASTRATOR_EXIT_CODE
"""


@dataclass
class SlurmScriptConfig:
    """Configuration for SLURM batch script generation."""

    job_name: str
    ntasks: int
    mem_per_cpu_gb: int
    orcastrator_command: str
    config_file: Path
    nodes: int = 1
    partition: str = "normal"
    cpus_per_task: int = 1
    time_h: int = 168  # 7 days
    orca_install_dir: str = "/soft/orca/orca_6_1_0_linux_x86-64_shared_openmpi418_avx2"
    openmpi_install_dir: str = "/soft/openmpi/openmpi-4.1.8"
    account: Optional[str] = None
    email: Optional[str] = None
    email_type: Optional[str] = None
    nodelist: Optional[list] = None
    exclude: Optional[list] = None
    timelimit: Optional[str] = None

    def compile(self) -> str:
        """Compile the SLURM script from template.

        Returns:
            Rendered SLURM batch script as string
        """
        # Ensure nodelist and exclude are lists for Jinja2
        data = asdict(self)
        data["nodelist"] = self.nodelist if self.nodelist is not None else []
        data["exclude"] = self.exclude if self.exclude is not None else []
        slurm_script = Template(SLURM_SCRIPT_TEMPLATE).render(data)
        # TODO - because logging is not set up correctly,
        # this debug log just prints the whole slurm script to the console.
        # log.debug(f"SLURM script: {slurm_script}")
        return slurm_script

    def write_to(self, file: Path) -> None:
        """Write SLURM script to file and make it executable.

        Args:
            file: Path where the script should be written
        """
        script = self.compile()
        # Write the rendered script to the output path
        file.write_text(script)
        # Make the script executable
        file.chmod(0o755)
        log.info(f"SLURM script written to: {file}")
