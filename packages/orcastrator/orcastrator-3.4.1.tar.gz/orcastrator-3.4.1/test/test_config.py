"""Unit tests for config module."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.config import (
    SlurmSettings,
    StageConfig,
    WorkflowConfig,
    load_config,
    substitute_variables,
)


class TestStageConfig:
    """Tests for StageConfig class."""

    def test_stage_config_minimal(self):
        """Test creating minimal stage config."""
        stage = StageConfig(name="opt", simple_keywords=["OPT", "B3LYP"])
        assert stage.name == "opt"
        assert stage.simple_keywords == ["OPT", "B3LYP"]
        assert stage.input_blocks == []
        assert stage.mult is None
        assert stage.charge is None
        assert stage.inherit == []

    def test_stage_config_full(self):
        """Test creating full stage config."""
        stage = StageConfig(
            name="casscf",
            simple_keywords=["CASSCF"],
            input_blocks=["%casscf nroot 2 end"],
            mult=3,
            charge=-1,
            inherit=["*.gbw", "*.xyz"],
        )
        assert stage.name == "casscf"
        assert stage.mult == 3
        assert stage.charge == -1
        assert len(stage.input_blocks) == 1
        assert len(stage.inherit) == 2

    def test_stage_config_strips_name(self):
        """Test that stage name is stripped of whitespace."""
        stage = StageConfig(name="  opt  ", simple_keywords=["OPT"])
        assert stage.name == "opt"

    def test_stage_config_requires_name(self):
        """Test that stage name is required."""
        with pytest.raises(ValidationError):
            StageConfig(simple_keywords=["OPT"])  # type: ignore # missing the name is what we're testing

    def test_stage_config_requires_keywords(self):
        """Test that simple_keywords are required."""
        with pytest.raises(ValidationError):
            StageConfig(name="opt")  # type: ignore # missing the keywords is what we're testing

    def test_stage_config_keywords_not_empty(self):
        """Test that simple_keywords cannot be empty."""
        with pytest.raises(ValidationError):
            StageConfig(name="opt", simple_keywords=[])


class TestWorkflowConfig:
    """Tests for WorkflowConfig class."""

    def test_workflow_config_minimal(self):
        """Test creating minimal workflow config."""
        config = WorkflowConfig(
            stages=[StageConfig(name="opt", simple_keywords=["OPT"])]
        )
        assert len(config.stages) == 1
        assert config.output_dir == Path("output")
        assert config.molecules_dir == Path("molecules")
        assert config.cpus == 1
        assert config.workers == 1

    def test_workflow_config_with_keywords(self):
        """Test workflow config with variable substitution keywords."""
        config = WorkflowConfig(
            keyword_defaults={"basis": "def2-SVP", "method": "B3LYP"},
            stages=[StageConfig(name="opt", simple_keywords=["OPT"])],
        )
        assert config.keyword_defaults["basis"] == "def2-SVP"
        assert config.keyword_defaults["method"] == "B3LYP"

    def test_workflow_config_duplicate_stage_names(self):
        """Test that duplicate stage names are rejected."""
        with pytest.raises(ValidationError, match="Duplicate stage names"):
            WorkflowConfig(
                stages=[
                    StageConfig(name="opt", simple_keywords=["OPT"]),
                    StageConfig(name="opt", simple_keywords=["FREQ"]),
                ]
            )

    def test_workflow_config_slurm_settings(self):
        """Test SLURM settings in workflow config."""
        config = WorkflowConfig(
            stages=[StageConfig(name="opt", simple_keywords=["OPT"])],
            slurm=SlurmSettings(
                nodelist=["node001", "node002"],
                exclude_nodes=["node003"],
                timelimit="24:00:00",
                partition="gpu",
                account="myaccount",
                email="user@example.com",
            ),
        )
        assert config.slurm.nodelist == ["node001", "node002"]
        assert config.slurm.exclude_nodes == ["node003"]
        assert config.slurm.timelimit == "24:00:00"
        assert config.slurm.partition == "gpu"
        assert config.slurm.account == "myaccount"
        assert config.slurm.email == "user@example.com"


class TestLegacyConfigNormalization:
    """Tests for legacy config format normalization."""

    def test_legacy_main_section(self):
        """Test normalizing legacy 'main' section."""
        raw_config = {
            "main": {
                "output_dir": "results",
                "cpus": 8,
                "workers": 2,
            },
            "stages": [{"name": "opt", "simple_keywords": ["OPT"]}],
        }
        config = WorkflowConfig(**raw_config)
        assert config.output_dir == Path("results")
        assert config.cpus == 8
        assert config.workers == 2

    def test_legacy_molecules_section(self):
        """Test normalizing legacy 'molecules' section."""
        raw_config = {
            "molecules": {
                "directory": "xyz_files",
                "include": ["mol1", "mol2"],
                "exclude": ["mol3"],
            },
            "stages": [{"name": "opt", "simple_keywords": ["OPT"]}],
        }
        config = WorkflowConfig(**raw_config)
        assert config.molecules_dir == Path("xyz_files")
        assert config.include == ["mol1", "mol2"]
        assert config.exclude == ["mol3"]

    def test_legacy_step_to_stages(self):
        """Test normalizing legacy 'step' to 'stages'."""
        raw_config = {
            "step": [{"name": "opt", "simple_keywords": ["OPT"]}],
        }
        config = WorkflowConfig(**raw_config)  # type: ignore # no way to check the expansion satifies the types
        assert len(config.stages) == 1
        assert config.stages[0].name == "opt"

    def test_legacy_keywords_to_simple_keywords(self):
        """Test normalizing legacy 'keywords' to 'simple_keywords' in stages."""
        raw_config = {
            "stages": [{"name": "opt", "keywords": ["OPT", "B3LYP"]}],
        }
        config = WorkflowConfig(**raw_config)  # type: ignore # no way to check the expansion satifies the types
        assert config.stages[0].simple_keywords == ["OPT", "B3LYP"]

    def test_legacy_keywords_not_overwrite_simple_keywords(self):
        """Test that simple_keywords takes precedence over keywords."""
        raw_config = {
            "stages": [
                {
                    "name": "opt",
                    "keywords": ["OPT"],
                    "simple_keywords": ["FREQ"],
                }
            ],
        }
        config = WorkflowConfig(**raw_config)  # type: ignore # no way to check the expansion satifies the types
        # simple_keywords should be preserved
        assert config.stages[0].simple_keywords == ["FREQ"]


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_basic(self, tmp_path):
        """Test loading a basic config file."""
        config_file = tmp_path / "config.toml"
        toml_content = """
output_dir = "output"
molecules_dir = "molecules"
cpus = 4

[[stages]]
name = "opt"
simple_keywords = ["OPT"]
"""
        config_file.write_text(toml_content)

        config = load_config(config_file)
        assert config.cpus == 4
        assert len(config.stages) == 1

    def test_load_config_with_multiline_input_blocks(self, tmp_path):
        """Test that multi-line strings in input_blocks are parsed correctly.

        This is a regression test for a bug in the old toml library (v0.10.2)
        that would truncate triple-quoted multi-line strings inside arrays to
        only 2-3 characters.

        Example: '''%CASSCF\\n    NEL 10\\n    END''' would be parsed as '%CA'
        """
        config_file = tmp_path / "config.toml"

        # Write TOML with multi-line strings in input_blocks array
        # This mimics real ORCA CASSCF input blocks
        toml_content = """
output_dir = "output"
molecules_dir = "molecules"

[[stages]]
name = "avas"
simple_keywords = ["AVAS", "def2-SVP"]
input_blocks = [
    '''%CASSCF
    MULT 5, 3, 1
    NROOTS 5, 45, 50
    END'''
]

[[stages]]
name = "ailft"
simple_keywords = ["MOREAD", "def2-SVP"]
input_blocks = [
    '%MOINP "avas.gbw"',
    '''%CASSCF
    NEL 10
    NORB 5
    MULT 5, 3, 1
    NROOTS 5, 45, 50
    ACTORBS DORBS
    REL
        DOSOC TRUE END
    END'''
]
"""
        config_file.write_text(toml_content)

        config = load_config(config_file)

        # Verify the config loaded correctly
        assert len(config.stages) == 2

        # Check first stage (avas)
        avas_stage = config.stages[0]
        assert avas_stage.name == "avas"
        assert len(avas_stage.input_blocks) == 1
        avas_block = avas_stage.input_blocks[0]

        # The block should contain the full multi-line string, not truncated
        assert len(avas_block) > 10  # Should be ~66 chars, not 2-3
        assert avas_block.startswith("%CASSCF")
        assert "MULT 5, 3, 1" in avas_block
        assert "NROOTS 5, 45, 50" in avas_block
        assert avas_block.strip().endswith("END")

        # Check second stage (ailft)
        ailft_stage = config.stages[1]
        assert ailft_stage.name == "ailft"
        assert len(ailft_stage.input_blocks) == 2

        # First block should be the simple single-line string
        assert ailft_stage.input_blocks[0] == '%MOINP "avas.gbw"'

        # Second block should be the full CASSCF block
        casscf_block = ailft_stage.input_blocks[1]
        assert len(casscf_block) > 100  # Should be ~159 chars, not 2-3
        assert casscf_block.startswith("%CASSCF")
        assert "NEL 10" in casscf_block
        assert "NORB 5" in casscf_block
        assert "MULT 5, 3, 1" in casscf_block
        assert "NROOTS 5, 45, 50" in casscf_block
        assert "ACTORBS DORBS" in casscf_block
        assert "DOSOC TRUE" in casscf_block
        assert casscf_block.strip().endswith("END")

        # Count lines to ensure full content is there
        casscf_lines = casscf_block.split("\n")
        assert len(casscf_lines) >= 8  # Should have at least 8-9 lines

    def test_load_config_with_relative_paths(self, tmp_path):
        """Test that relative paths are resolved relative to config file."""
        subdir = tmp_path / "configs"
        subdir.mkdir()
        config_file = subdir / "config.toml"

        toml_content = """
output_dir = "../output"
molecules_dir = "../molecules"

[[stages]]
name = "opt"
simple_keywords = ["OPT"]
"""
        config_file.write_text(toml_content)

        config = load_config(config_file)
        # Paths should be resolved relative to config file location
        assert config.output_dir == (tmp_path / "output").resolve()
        assert config.molecules_dir == (tmp_path / "molecules").resolve()

    def test_load_config_with_absolute_paths(self, tmp_path):
        """Test that absolute paths are preserved."""
        config_file = tmp_path / "config.toml"

        toml_content = """
output_dir = "/absolute/output"
molecules_dir = "/absolute/molecules"

[[stages]]
name = "opt"
simple_keywords = ["OPT"]
"""
        config_file.write_text(toml_content)

        config = load_config(config_file)
        assert config.output_dir == Path("/absolute/output")
        assert config.molecules_dir == Path("/absolute/molecules")

    def test_load_config_invalid_toml(self, tmp_path):
        """Test loading invalid TOML raises error."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("this is not valid toml [[[]")

        with pytest.raises(Exception):  # toml.TomlDecodeError
            load_config(config_file)

    def test_load_config_invalid_schema(self, tmp_path):
        """Test loading config with invalid schema raises error."""
        config_file = tmp_path / "config.toml"
        toml_content = """
output_dir = "output"
# Missing required 'stages' field
"""
        config_file.write_text(toml_content)

        with pytest.raises(ValidationError):
            load_config(config_file)


class TestSubstituteVariables:
    """Tests for substitute_variables function (already covered in test_variable_substitution.py)."""

    def test_substitute_basic(self):
        """Test basic variable substitution."""
        template = "Hello {name}"
        result = substitute_variables(template, {"name": "World"}, {})
        assert result == "Hello World"

    def test_substitute_from_global(self):
        """Test substitution from global keywords."""
        template = "Method: {method}"
        result = substitute_variables(template, {}, {"method": "B3LYP"})
        assert result == "Method: B3LYP"

    def test_substitute_molecule_overrides_global(self):
        """Test that molecule metadata overrides global keywords."""
        template = "{value}"
        result = substitute_variables(
            template, {"value": "molecule"}, {"value": "global"}
        )
        assert result == "molecule"

    def test_substitute_variable_not_found(self):
        """Test that missing variable raises KeyError."""
        template = "Missing {var}"
        with pytest.raises(KeyError, match="not found"):
            substitute_variables(template, {}, {})

    def test_substitute_no_variables(self):
        """Test that strings without variables are unchanged."""
        template = "No variables here"
        result = substitute_variables(template, {}, {})
        assert result == template

    def test_substitute_multiple_same_variable(self):
        """Test substituting the same variable multiple times."""
        template = "{x} + {x} = {x}"
        result = substitute_variables(template, {"x": 5}, {})
        assert result == "5 + 5 = 5"
