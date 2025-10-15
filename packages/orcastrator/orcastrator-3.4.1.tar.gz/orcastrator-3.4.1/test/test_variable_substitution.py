"""Tests for variable substitution in keywords and blocks."""

import pytest

from src.config import substitute_variables


def test_substitute_from_molecule_metadata():
    """Test substitution using molecule-specific metadata."""
    template = "%casscf nroot {casscf_roots} end"
    molecule_metadata = {"casscf_roots": 4}
    global_keywords = {}

    result = substitute_variables(template, molecule_metadata, global_keywords)
    assert result == "%casscf nroot 4 end"


def test_substitute_from_global_keywords():
    """Test substitution using global keyword defaults."""
    template = "%casscf nroot {casscf_roots} end"
    molecule_metadata = {}
    global_keywords = {"casscf_roots": 2}

    result = substitute_variables(template, molecule_metadata, global_keywords)
    assert result == "%casscf nroot 2 end"


def test_molecule_metadata_overrides_global():
    """Test that molecule metadata takes precedence over global keywords."""
    template = "%casscf nroot {casscf_roots} end"
    molecule_metadata = {"casscf_roots": 4}
    global_keywords = {"casscf_roots": 2}

    result = substitute_variables(template, molecule_metadata, global_keywords)
    assert result == "%casscf nroot 4 end"


def test_multiple_variables():
    """Test substitution with multiple variables."""
    template = "%casscf nroot {casscf_roots} mult {mult_value} end"
    molecule_metadata = {"casscf_roots": 4}
    global_keywords = {"mult_value": 3}

    result = substitute_variables(template, molecule_metadata, global_keywords)
    assert result == "%casscf nroot 4 mult 3 end"


def test_variable_not_found_raises_error():
    """Test that missing variables raise KeyError."""
    template = "%casscf nroot {casscf_roots} end"
    molecule_metadata = {}
    global_keywords = {}

    with pytest.raises(KeyError) as exc_info:
        substitute_variables(template, molecule_metadata, global_keywords)

    assert "casscf_roots" in str(exc_info.value)
    assert "not found" in str(exc_info.value)


def test_no_variables_returns_unchanged():
    """Test that strings without variables are returned unchanged."""
    template = "%casscf nroot 2 end"
    molecule_metadata = {"casscf_roots": 4}
    global_keywords = {}

    result = substitute_variables(template, molecule_metadata, global_keywords)
    assert result == template


def test_string_values():
    """Test substitution with string values."""
    template = "! {method} {basis}"
    molecule_metadata = {"method": "B3LYP"}
    global_keywords = {"basis": "def2-TZVP"}

    result = substitute_variables(template, molecule_metadata, global_keywords)
    assert result == "! B3LYP def2-TZVP"


def test_integer_values_converted_to_string():
    """Test that integer values are converted to strings."""
    template = "value is {number}"
    molecule_metadata = {"number": 42}
    global_keywords = {}

    result = substitute_variables(template, molecule_metadata, global_keywords)
    assert result == "value is 42"


def test_same_variable_multiple_times():
    """Test substitution when the same variable appears multiple times."""
    template = "{value} + {value} = {value}"
    molecule_metadata = {"value": 5}
    global_keywords = {}

    result = substitute_variables(template, molecule_metadata, global_keywords)
    assert result == "5 + 5 = 5"


def test_variables_in_keywords_list():
    """Test realistic example with keywords list."""
    keywords = ["CASSCF({n},{m})", "def2-SVP"]
    molecule_metadata = {"n": 8, "m": 7}
    global_keywords = {}

    results = [
        substitute_variables(kw, molecule_metadata, global_keywords) for kw in keywords
    ]
    assert results == ["CASSCF(8,7)", "def2-SVP"]
