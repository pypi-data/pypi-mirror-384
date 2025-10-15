# Orcastrator

Orcastrator is a Python toolkit and CLI for automating ORCA quantum-chemistry calculations.

**Features:**
- Simple TOML-based configuration
- Automatic directory and scratch management
- Multi-stage pipelines with caching and chaining (opt → freq → sp)
- Parallel execution across molecules
- SLURM batch script generation

**Version:** 3.0.0
**License:** MIT
**Requirements:** Python ≥3.11

## Installation

```bash
uv tool install orcastrator
```

### Global Configuration (Optional)

You can create a global configuration file at `~/.orcastrator_config` to set default paths:

```toml
# Path to ORCA executable (if not in PATH)
orca_path = "/opt/orca/orca"

# Path to OpenMPI installation directory
openmpi_path = "/opt/openmpi"

# Default scratch directory
scratch_dir = "/scratch"
```

**Settings are optional** - if not specified, Orcastrator will:
- Search `PATH` for ORCA executable
- Use `/scratch` (or `/tmp` if `/scratch` doesn't exist) for scratch files

All paths support `~` for home directory expansion.

See `.orcastrator_config.example` in the repository for a template.

## Quickstart

1. Generate a template configuration:
   ```bash
   orcastrator init
   ```

2. Edit `orcastrator.toml`:
   ```toml
   # Core paths (relative to this file)
   output_dir = "output"
   molecules_dir = "molecules"

   # Resources
   cpus = 8
   mem_per_cpu_gb = 4
   workers = 2
   scratch_dir = "/scratch"

   # Workflow settings
   overwrite = false
   debug = false

   # Molecule filtering (optional)
   # include = ["mol1", "mol2"]
   # exclude = ["mol3"]

   # Pipeline stages
   [[stages]]
   name = "opt"
   simple_keywords = ["D4", "TPSS", "def2-SVP", "OPT"]

   [[stages]]
   name = "freq"
   simple_keywords = ["D4", "TPSS", "def2-SVP", "FREQ"]
   inherit = ["*.gbw"]  # Inherit wavefunction from previous stage

   [[stages]]
   name = "sp"
   simple_keywords = ["D4", "TPSSh", "def2-TZVP"]
   inherit = ["*.gbw"]
   ```

3. Run the pipeline:
   ```bash
   orcastrator run orcastrator.toml
   ```

4. (Optional) Submit to SLURM:
   ```bash
   orcastrator slurm orcastrator.toml
   orcastrator slurm --no-submit orcastrator.toml  # just generate script
   ```

## Configuration Reference

### Core Settings

- `output_dir` - Output directory for results (relative to config file)
- `molecules_dir` - Directory containing .xyz files (relative to config file)
- `cpus` - Total CPU cores available
- `mem_per_cpu_gb` - Memory per CPU core in GB
- `workers` - Number of parallel workers (molecules processed simultaneously)
- `scratch_dir` - Scratch directory for temporary files (default: `/scratch`)

### Workflow Settings

- `overwrite` - Rerun all calculations, ignoring cache (default: `false`)
- `debug` - Enable debug logging (default: `false`)
- `include` - List of molecule names to include (optional)
- `exclude` - List of molecule names to exclude (optional)

### SLURM Settings (Optional)

SLURM settings are configured in a `[slurm]` table:

```toml
[slurm]
partition = "long"
timelimit = "48:00:00"
exclude_nodes = ["apollo-19", "apollo-20"]
nodelist = ["node001", "node002"]
account = "my_project"
email = "user@example.com"
```

Available settings:
- `partition` - SLURM partition (default: `"normal"`)
- `timelimit` - Time limit in `HH:MM:SS` format
- `exclude_nodes` - List of nodes to exclude (e.g., `["apollo-19", "apollo-20"]`)
- `nodelist` - List of nodes to use (e.g., `["node001", "node002"]`)
- `account` - SLURM account name
- `email` - Email for job notifications
- `orca_install_dir` - Path to ORCA installation (default: `/soft/orca/orca_6_0_1_linux_x86-64_shared_openmpi416_avx2`)
- `openmpi_install_dir` - Path to OpenMPI installation (default: `/soft/openmpi/openmpi-4.1.6`)

### Stage Configuration

Each `[[stages]]` block defines a calculation step:

- `name` - Unique stage identifier
- `simple_keywords` - ORCA keywords (e.g., `["OPT", "TPSS", "def2-SVP"]`)
- `input_blocks` - Additional ORCA % blocks (e.g., `["%scf maxiter 150 end"]`)
- `mult` - Override multiplicity for this stage (optional)
- `charge` - Override charge for this stage (optional)
- `inherit` - File patterns to inherit from previous stage (e.g., `["*.gbw", "*.xyz"]`)

### Variable Substitution

You can use `{variable_name}` placeholders in both `simple_keywords` and `input_blocks` to make molecule-specific calculations:

**Global defaults:**
```toml
[keyword_defaults]
casscf_roots = 2
active_electrons = 6

[[stages]]
name = "casscf"
simple_keywords = ["CASSCF({active_electrons},{casscf_roots})", "def2-SVP"]
input_blocks = ["%casscf nroot {casscf_roots} end"]
```

**Molecule-specific overrides in XYZ files:**
```xyz
5
{"charge": 0, "mult": 1, "casscf_roots": 4, "active_electrons": 8}
C  0.0  0.0  0.0
...
```

**Resolution order:**
1. Molecule-specific metadata (from XYZ file)
2. Global keyword defaults (from `[keyword_defaults]` section in config)
3. Error if variable not found

This allows you to set sensible defaults while overriding parameters for specific molecules as needed.

## Architecture

Orcastrator 3.0.0 uses a streamlined architecture for better maintainability:

```
src/
├── config.py    # Pydantic-based configuration
├── molecule.py  # Molecule representation
├── engine.py    # ORCA execution and scratch management
├── runner.py    # Parallel workflow execution
└── cli.py       # Command-line interface
```

**Key improvements in 3.0.0:**
- 27% code reduction (1,775 → 1,303 lines)
- Flat configuration structure (no unnecessary nesting)
- ProcessPoolExecutor for parallel execution
- Content hashing for cache validation
- Loguru for structured logging

## Migration from 2.0.x

Version 3.0.0 is backward compatible. Legacy config format is automatically converted:

**Old format (still works):**
```toml
[main]
cpus = 4

[molecules]
directory = "molecules"

[[step]]
name = "opt"
```

**New format (recommended):**
```toml
cpus = 4
molecules_dir = "molecules"

[[stages]]
name = "opt"
```

No changes required to existing workflows.

## Examples

### Basic Optimization and Frequency

```toml
output_dir = "results"
molecules_dir = "molecules"
cpus = 4
mem_per_cpu_gb = 2

[[stages]]
name = "opt"
simple_keywords = ["OPT", "B3LYP", "def2-SVP"]

[[stages]]
name = "freq"
simple_keywords = ["FREQ", "B3LYP", "def2-SVP"]
inherit = ["*.gbw"]
```

### High-Level Single Point

```toml
output_dir = "results"
molecules_dir = "molecules"
cpus = 8
mem_per_cpu_gb = 4
workers = 2

[[stages]]
name = "opt"
simple_keywords = ["OPT", "TPSS", "def2-SVP", "D4"]

[[stages]]
name = "sp"
simple_keywords = ["DLPNO-CCSD(T)", "def2-TZVPP", "def2-TZVPP/C"]
input_blocks = ["%scf maxiter 200 end"]
inherit = ["*.gbw"]
```

### Selective Processing

```toml
output_dir = "results"
molecules_dir = "molecules"
cpus = 4

# Only process specific molecules
include = ["benzene", "toluene", "phenol"]

[[stages]]
name = "opt"
simple_keywords = ["OPT", "PBE0", "def2-TZVP"]
```

## XYZ File Format

Molecule files should include charge and multiplicity in the comment line:

**JSON format (recommended):**
```xyz
12
{"charge": 0, "mult": 1}
C    0.000000    0.000000    0.000000
H    1.089000    0.000000    0.000000
...
```

**Simple format:**
```xyz
12
charge=0 mult=1
C    0.000000    0.000000    0.000000
H    1.089000    0.000000    0.000000
...
```

## Development

**Dependencies:**
- click - CLI framework
- pydantic - Configuration validation
- loguru - Structured logging
- jinja2 - SLURM template rendering
- toml - Configuration parsing

**Testing:**
```bash
uv run python -m src.cli --version
uv run python -m src.cli init --slim
```

**Project structure:**
- `src/` - Main codebase (3.0.0)
- `orcastrator/` - Legacy codebase (2.0.x, deprecated)
- `test/` - Integration tests

## License

MIT License - see LICENSE file for details.
