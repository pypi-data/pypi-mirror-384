from dataclasses import dataclass
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field, field_validator


class DatasetConfig(BaseModel):
    """Config for a dataset."""

    source: Path = Field(default=Path("dataset"))
    include: List[str] = Field(default_factory=list)
    exclude: List[str] = Field(default_factory=list)


class CalculationConfig:
    """Config for a single ORCA calculation."""

    title: str
    simple_keywords: List[str] = Field(..., min_length=1)
    keyword_blocks: List[str] = Field(default_factory=list)
    fetch: List[str] = Field(default_factory=list)


class StagesConfig:
    """Config for multiple stages of ORCA calculations."""

    title: str
    stages: List[CalculationConfig] = Field(..., min_length=1)


@dataclass(frozen=True)
class EngineResources:
    """Dataclass representing computing resources for a single calculation."""

    cores: int = Field(default=1, ge=1, description="Number of CPU cores.")
    mem_per_core: int = Field(default=1, ge=1, description="RAM per CPU core in GB.")
    time_limit: int = Field(default=168, ge=1, description="Time limit in hours.")

    def total_memory(self) -> int:
        return self.cores * self.mem_per_core


class EngineConfig:
    """Config for quantum chemistry backend engine (ORCA) to run individual calculations."""

    resources: EngineResources

    scratch: Path = Field(
        default=Path("/tmp"), description="Where to store temporary files."
    )
    reset: bool = Field(
        default=False, description="Reset calculation state and run again."
    )


class WorkflowConfig(BaseModel):
    """Config for running full workflows with multiple workers."""

    dataset: DatasetConfig

    output: Path = Field(default=Path("output"))
    workers: int = Field(default=1, ge=1)
    debug: bool = Field(default=False)

    @field_validator("output_dir", "scratch_dir", mode="before")
    def _resolve_paths(cls, v: str) -> Path:
        p = Path(v)
        # Convert to absolute, expanding user home if needed
        return (p if p.is_absolute() else Path.cwd() / p).expanduser().resolve()
