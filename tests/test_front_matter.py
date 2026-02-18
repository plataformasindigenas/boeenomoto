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


def test_parse_valid_front_matter(tmp_path):
    """Test parsing a valid markdown file with front matter."""
    md_file = tmp_path / "test.md"
    md_file.write_text("---\nid: test-1\ntitle: Test\n---\nBody content here.\n")

    result = _run_python(f"""
import sys; sys.path.insert(0, '{SCRIPTS_DIR}')
from convert import _parse_front_matter
from pathlib import Path
fm, body = _parse_front_matter(Path('{md_file}'))
assert fm['id'] == 'test-1'
assert fm['title'] == 'Test'
assert body.strip() == 'Body content here.'
print('OK')
""")
    assert result.returncode == 0, f"Failed: {result.stderr}"


def test_parse_missing_front_matter_start(tmp_path):
    """Test that missing front matter start raises ValueError."""
    md_file = tmp_path / "test.md"
    md_file.write_text("No front matter here.\n")

    result = _run_python(f"""
import sys; sys.path.insert(0, '{SCRIPTS_DIR}')
from convert import _parse_front_matter
from pathlib import Path
try:
    _parse_front_matter(Path('{md_file}'))
    print('ERROR: no exception raised')
    sys.exit(1)
except ValueError as e:
    assert 'missing front matter start' in str(e)
    print('OK')
""")
    assert result.returncode == 0, f"Failed: {result.stderr}"


def test_parse_missing_front_matter_end(tmp_path):
    """Test that missing front matter end raises ValueError."""
    md_file = tmp_path / "test.md"
    md_file.write_text("---\nid: test-1\nNo closing delimiter\n")

    result = _run_python(f"""
import sys; sys.path.insert(0, '{SCRIPTS_DIR}')
from convert import _parse_front_matter
from pathlib import Path
try:
    _parse_front_matter(Path('{md_file}'))
    print('ERROR: no exception raised')
    sys.exit(1)
except ValueError as e:
    assert 'missing front matter end' in str(e)
    print('OK')
""")
    assert result.returncode == 0, f"Failed: {result.stderr}"


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
