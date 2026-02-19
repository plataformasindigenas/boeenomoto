"""Tests for encyclopedia front matter parsing."""

import subprocess
import sys
from pathlib import Path

import pytest

# The convert module requires aptoro which may only be in the venv.
# We test the functions by running them in a subprocess with the venv python.
VENV_PYTHON = Path(__file__).parent.parent / ".venv" / "bin" / "python"
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"


def _run_python(code: str) -> subprocess.CompletedProcess:
    """Run Python code using the venv interpreter."""
    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    return subprocess.run(
        [python, "-c", code],
        capture_output=True, text=True,
        env={"PYTHONPATH": str(SCRIPTS_DIR)},
    )


def test_assert_no_html_clean():
    """Test that clean markdown passes HTML check."""
    result = _run_python(f"""
import sys; sys.path.insert(0, '{SCRIPTS_DIR}')
from convert import _assert_no_html
_assert_no_html('This is **bold** and *italic*.', 'test-entry')
print('OK')
""")
    assert result.returncode == 0, f"Failed: {result.stderr}"


def test_assert_no_html_with_tags():
    """Test that HTML tags in markdown raise ValueError."""
    result = _run_python(f"""
import sys; sys.path.insert(0, '{SCRIPTS_DIR}')
from convert import _assert_no_html
try:
    _assert_no_html('<p>HTML content</p>', 'test-entry')
    print('ERROR: no exception raised')
    sys.exit(1)
except ValueError as e:
    assert 'contains HTML tags' in str(e)
    print('OK')
""")
    assert result.returncode == 0, f"Failed: {result.stderr}"


def test_wikilink_valid():
    """Test that valid wikilinks are converted to markdown links."""
    result = _run_python(f"""
import sys; sys.path.insert(0, '{SCRIPTS_DIR}')
from convert import _process_wikilinks
all_ids = {{'boe', 'aroe', 'ecerae'}}
out = _process_wikilinks('See [[boe]] for details.', all_ids)
assert '[boe](boe.html)' in out, f'Unexpected output: {{out}}'
print('OK')
""")
    assert result.returncode == 0, f"Failed: {result.stderr}"


def test_wikilink_broken():
    """Test that broken wikilinks produce span.broken-link."""
    result = _run_python(f"""
import sys; sys.path.insert(0, '{SCRIPTS_DIR}')
from convert import _process_wikilinks
all_ids = {{'boe'}}
out = _process_wikilinks('See [[nonexistent]] entry.', all_ids)
assert 'broken-link' in out, f'Unexpected output: {{out}}'
assert 'nonexistent' in out
print('OK')
""")
    assert result.returncode == 0, f"Failed: {result.stderr}"


def test_wikilink_piped():
    """Test that piped wikilinks use display text."""
    result = _run_python(f"""
import sys; sys.path.insert(0, '{SCRIPTS_DIR}')
from convert import _process_wikilinks
all_ids = {{'boe'}}
out = _process_wikilinks('See [[boe|the Bororo people]].', all_ids)
assert '[the Bororo people](boe.html)' in out, f'Unexpected output: {{out}}'
print('OK')
""")
    assert result.returncode == 0, f"Failed: {result.stderr}"
