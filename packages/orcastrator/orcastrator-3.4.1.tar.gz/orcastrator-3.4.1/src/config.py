"""Configuration models for Orcastrator using Pydantic."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import tomli
from loguru import logger as log
from pydantic import BaseModel, Field, field_validator, model_validator


class SlurmSettings(BaseModel):
    """SLURM settings from configuration file."""

    nodelist: List[str] = Field(default_factory=list, description="SLURM node list")
    exclude_nodes: List[str] = Field(
        default_factory=list, description="SLURM nodes to exclude"
    )
    timelimit: Optional[str] = Field(
        default=None, description="SLURM time limit (HH:MM:SS)"
    )
    partition: str = Field(default="normal", description="SLURM partition")
    account: Optional[str] = Field(default=None, description="SLURM account")
    email: Optional[str] = Field(
        default=None, description="Email for SLURM notifications"
    )
    orca_install_dir: str = Field(
        default="/soft/orca/orca_6_1_0_linux_x86-64_shared_openmpi418_avx2",
        description="ORCA installation directory",
    )
    openmpi_install_dir: str = Field(
        default="/soft/openmpi/openmpi-4.1.8",
        description="OpenMPI installation directory",
    )


class GlobalConfig(BaseModel):
    """Global user configuration from ~/.orcastrator_config."""

    orca_path: Optional[Path] = Field(
        default=None, description="Path to ORCA executable"
    )
    openmpi_path: Optional[Path] = Field(
        default=None, description="Path to OpenMPI installation directory"
    )
    scratch_dir: Optional[Path] = Field(
        default=None, description="Default scratch directory"
    )

    @field_validator("orca_path", "openmpi_path", "scratch_dir", mode="before")
    def _expand_paths(cls, v):
        if v is None:
            return None
        return Path(v).expanduser().resolve()


def load_global_config() -> GlobalConfig:
    """Load global user configuration from ~/.orcastrator_config.

    Returns:
        GlobalConfig instance (possibly with all None values if file doesn't exist)
    """
    config_file = Path.home() / ".orcastrator_config"

    if not config_file.exists():
        log.debug(f"Global config not found at {config_file}, using defaults")
        return GlobalConfig()

    try:
        with open(config_file, "rb") as f:
            raw = tomli.load(f)
        log.debug(f"Loaded global config from {config_file}")
        return GlobalConfig(**raw)
    except Exception as e:
        log.warning(f"Failed to load global config from {config_file}: {e}")
        return GlobalConfig()


class StageConfig(BaseModel):
    """Configuration for a single calculation stage."""

    name: str = Field(..., description="Stage name (e.g., 'opt', 'freq', 'sp')")
    simple_keywords: List[str] = Field(
        ..., min_length=1, description="ORCA keywords (simple input line)"
    )
    input_blocks: List[str] = Field(
        default_factory=list, description="Additional ORCA % blocks"
    )
    mult: Optional[int] = Field(
        default=None, description="Override multiplicity for this stage"
    )
    charge: Optional[int] = Field(
        default=None, description="Override charge for this stage"
    )
    inherit: List[str] = Field(
        default_factory=list,
        description="File patterns to inherit from previous stage (e.g., ['*.gbw'])",
    )

    @field_validator("name")
    def _strip_name(cls, v: str) -> str:
        return v.strip()


class WorkflowConfig(BaseModel):
    """Main workflow configuration."""

    # Core settings
    output_dir: Path = Field(default=Path("output"), description="Output directory")
    molecules_dir: Path = Field(
        default=Path("molecules"), description="Directory containing .xyz files"
    )

    # Variable substitution defaults
    keyword_defaults: Dict[str, Any] = Field(
        default_factory=dict,
        description="Global default values for keyword substitution in stages",
    )

    # Resource settings
    cpus: int = Field(default=1, ge=1, description="Total CPU cores available")
    mem_per_cpu_gb: int = Field(default=1, ge=1, description="Memory per CPU in GB")
    workers: int = Field(default=1, ge=1, description="Number of parallel workers")
    scratch_dir: Path = Field(
        default=Path("/scratch"), description="Scratch directory for calculations"
    )

    # Workflow settings
    stages: List[StageConfig] = Field(
        ..., min_length=1, description="Calculation stages"
    )
    overwrite: bool = Field(
        default=False, description="Overwrite existing calculations"
    )

    # Filtering
    include: List[str] = Field(
        default_factory=list, description="Include only these molecules"
    )
    exclude: List[str] = Field(
        default_factory=list, description="Exclude these molecules"
    )

    # SLURM settings (optional)
    slurm: SlurmSettings = Field(
        default_factory=SlurmSettings, description="SLURM settings"
    )

    # Other
    debug: bool = Field(default=False, description="Enable debug logging")

    # Internal: store config file path for relative path resolution
    _config_file_path: Optional[Path] = None

    @model_validator(mode="before")
    def _normalize_legacy_config(cls, values):
        """Support legacy config format with deprecation warnings."""
        if not isinstance(values, dict):
            return values

        # Handle deprecated 'rerun_failed' field
        if "rerun_failed" in values:
            log.warning(
                "Config field 'rerun_failed' is deprecated and will be removed in v4.0. "
                "Use 'overwrite' instead or rely on automatic caching."
            )
            values.pop("rerun_failed")

        # Handle deprecated top-level SLURM fields
        slurm_fields = [
            "nodelist",
            "exclude_nodes",
            "timelimit",
            "partition",
            "account",
            "email",
            "orca_install_dir",
            "openmpi_install_dir",
        ]
        found_slurm_fields = [f for f in slurm_fields if f in values]

        if found_slurm_fields:
            log.warning(
                f"Top-level SLURM fields {found_slurm_fields} are deprecated. "
                "Move them to a [slurm] table. Legacy support will be removed in v4.0"
            )
            if "slurm" not in values:
                values["slurm"] = {}
            for field in found_slurm_fields:
                values["slurm"][field] = values.pop(field)

        # Handle deprecated 'keywords' field (now 'keyword_defaults')
        if "keywords" in values and "keyword_defaults" not in values:
            log.warning(
                "Config field 'keywords' is deprecated, use 'keyword_defaults'. "
                "Legacy support will be removed in v4.0"
            )
            values["keyword_defaults"] = values.pop("keywords")

        # Handle legacy 'main' section
        if "main" in values:
            log.warning(
                "Config section [main] is deprecated. Move fields to top level. "
                "Legacy support will be removed in v4.0"
            )
            main = values.pop("main")
            values["output_dir"] = main.get("output_dir", "output")
            values["overwrite"] = main.get("overwrite", False)
            values["debug"] = main.get("debug", False)
            values["cpus"] = main.get("cpus", 1)
            values["mem_per_cpu_gb"] = main.get("mem_per_cpu_gb", 1)
            values["workers"] = main.get("workers", 1)
            values["scratch_dir"] = main.get("scratch_dir", "/scratch")

        # Handle legacy 'molecules' section
        if "molecules" in values:
            log.warning(
                "Config section [molecules] is deprecated. Move fields to top level. "
                "Legacy support will be removed in v4.0"
            )
            mol = values.pop("molecules")
            values["molecules_dir"] = mol.get("directory", "molecules")
            values["include"] = mol.get("include", [])
            values["exclude"] = mol.get("exclude", [])

        # Handle legacy 'dataset' section
        if "dataset" in values:
            log.warning(
                "Config section [dataset] is deprecated, use 'molecules_dir' instead. "
                "Legacy support will be removed in v4.0"
            )
            dataset = values.pop("dataset")
            values["molecules_dir"] = dataset.get("directory", "molecules")
            values["include"] = dataset.get("include", [])
            values["exclude"] = dataset.get("exclude", [])

        # Handle legacy 'resources' section
        if "resources" in values:
            log.warning(
                "Config section [resources] is deprecated. Move fields to top level. "
                "Legacy support will be removed in v4.0"
            )
            res = values.pop("resources")
            values["cpus"] = res.get("cpus", 1)
            values["mem_per_cpu_gb"] = res.get("mem_per_cpu_gb", 1)
            values["workers"] = res.get("workers", 1)
            values["scratch_dir"] = res.get("scratch_dir", "/scratch")

        # Handle legacy 'step' instead of 'stages'
        if "step" in values and "stages" not in values:
            log.warning(
                "Config field 'step' is deprecated, use 'stages'. "
                "Legacy support will be removed in v4.0"
            )
            values["stages"] = values.pop("step")

        # Handle deprecated stage fields
        if "stages" in values:
            for i, stage in enumerate(values["stages"]):
                if not isinstance(stage, dict):
                    continue

                stage_name = stage.get("name", f"stage {i}")

                # Handle 'keywords' -> 'simple_keywords'
                if "keywords" in stage and "simple_keywords" not in stage:
                    log.warning(
                        f"Stage '{stage_name}': field 'keywords' is deprecated, use 'simple_keywords'. "
                        "Legacy support will be removed in v4.0"
                    )
                    stage["simple_keywords"] = stage.pop("keywords")

                # Handle 'blocks' -> 'input_blocks'
                if "blocks" in stage and "input_blocks" not in stage:
                    log.warning(
                        f"Stage '{stage_name}': field 'blocks' is deprecated, use 'input_blocks'. "
                        "Legacy support will be removed in v4.0"
                    )
                    stage["input_blocks"] = stage.pop("blocks")

                # Handle 'keep' -> 'inherit'
                if "keep" in stage and "inherit" not in stage:
                    log.warning(
                        f"Stage '{stage_name}': field 'keep' is deprecated, use 'inherit'. "
                        "Legacy support will be removed in v4.0"
                    )
                    stage["inherit"] = stage.pop("keep")

        return values

    def _resolve_path(self, path: Path) -> Path:
        """Resolve path relative to config file location."""
        if path.is_absolute():
            return path.expanduser().resolve()

        # Resolve relative to config file if available
        if self._config_file_path:
            base_dir = self._config_file_path.parent
            return (base_dir / path).resolve()

        # Fallback to cwd
        return (Path.cwd() / path).resolve()

    @field_validator("output_dir", "molecules_dir", "scratch_dir", mode="before")
    def _resolve_paths(cls, v: str) -> Path:
        """Store path as-is for now, will resolve after config_file_path is set."""
        return Path(v)

    @field_validator("stages")
    def _unique_stage_names(cls, v: List[StageConfig]) -> List[StageConfig]:
        names = [s.name for s in v]
        duplicates = {n for n in names if names.count(n) > 1}
        if duplicates:
            raise ValueError(f"Duplicate stage names found: {duplicates}")
        return v

    def resolve_paths(self, config_file: Path) -> None:
        """Resolve all paths relative to the config file.

        This must be called after loading the config.
        """
        self._config_file_path = config_file.resolve()
        self.output_dir = self._resolve_path(self.output_dir)
        self.molecules_dir = self._resolve_path(self.molecules_dir)
        # Don't resolve scratch_dir - it's usually an absolute system path
        self.scratch_dir = self.scratch_dir.expanduser().resolve()


def substitute_variables(
    template: str, molecule_metadata: Dict[str, Any], global_keywords: Dict[str, Any]
) -> str:
    """Substitute variables in template string using molecule metadata and keyword defaults.

    Variables are specified using {variable_name} or {dict.key} syntax. Resolution order:
    1. Molecule-specific metadata (from XYZ file JSON)
    2. Global keyword defaults (from config [keyword_defaults] section)
    3. Error if not found

    Supports nested dictionaries using dot notation:
    - {casscf.norbs} accesses metadata["casscf"]["norbs"]
    - Falls back to global_keywords["casscf"]["norbs"]

    Args:
        template: String containing variables like "nroot {casscf.nroots}"
        molecule_metadata: Molecule-specific metadata from XYZ file
        global_keywords: Global keyword defaults from config

    Returns:
        String with all variables substituted

    Raises:
        KeyError: If a variable is not found in either metadata or keyword defaults
    """
    import re

    pattern = r"\{([\w.]+)\}"

    def get_nested(data: Dict[str, Any], keys: list) -> Any:
        """Get value from nested dict using list of keys."""
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    def replacer(match):
        var_path = match.group(1)
        keys = var_path.split(".")

        # Try molecule metadata first
        value = get_nested(molecule_metadata, keys)
        if value is not None:
            return str(value)

        # Then try global keywords
        value = get_nested(global_keywords, keys)
        if value is not None:
            return str(value)

        # Not found
        raise KeyError(
            f"Variable '{var_path}' not found in molecule metadata or global keywords"
        )

    return re.sub(pattern, replacer, template)


def load_config(config_file: Path) -> WorkflowConfig:
    """Load and validate workflow configuration from a TOML file.

    Args:
        config_file: Path to the TOML configuration file

    Returns:
        Validated WorkflowConfig instance

    Raises:
        tomli.TOMLDecodeError: if the TOML is invalid
        pydantic.ValidationError: if the config does not match the schema
    """
    with open(config_file, "rb") as f:
        raw = tomli.load(f)
    config = WorkflowConfig(**raw)
    config.resolve_paths(config_file)
    return config
