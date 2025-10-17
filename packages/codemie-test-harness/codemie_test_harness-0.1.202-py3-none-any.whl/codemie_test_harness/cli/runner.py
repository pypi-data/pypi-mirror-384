from __future__ import annotations
import subprocess
import sys
from typing import Iterable, List
from pathlib import Path

try:
    from importlib.resources import files as pkg_files
except Exception:
    pkg_files = None

from .constants import CONSOLE
from .marks_utils import (
    get_all_available_marks,
    is_valid_mark_expression,
    print_marks_list,
)


def resolve_tests_path_and_root() -> tuple[str, str]:
    """Resolve tests path and working directory.

    Returns:
        tuple: (tests_path, root_dir)
            - tests_path: Path to tests for pytest collection
            - root_dir: Directory to use as cwd so pytest.ini/.env are found
    """
    # 1) Use importlib.resources to locate installed package "tests"
    if pkg_files is not None:
        try:
            # Try to locate codemie_test_harness.tests package
            tests_dir = Path(str(pkg_files("codemie_test_harness.tests")))
            # Root dir should be the codemie_test_harness package directory
            # where pytest.ini and .env are located
            root_dir = str(tests_dir.parent)  # codemie_test_harness package root
            return str(tests_dir), root_dir
        except Exception:
            pass

    # 2) Fallback to repo layout when running from source
    # runner.py -> cli -> codemie_test_harness -> <repo_root>
    codemie_test_harness_root = (
        Path(__file__).resolve().parents[1]
    )  # codemie_test_harness directory
    tests_path = str(codemie_test_harness_root / "tests")
    # Use codemie_test_harness as root_dir since pytest.ini and .env are there
    root_dir = str(codemie_test_harness_root)
    return tests_path, root_dir


def build_pytest_cmd(
    workers: int,
    marks: str,
    reruns: int,
    count: int | None = None,
    timeout: int | None = None,
    extra: Iterable[str] | None = None,
) -> tuple[List[str], str]:
    tests_path, root_dir = resolve_tests_path_and_root()
    cmd = [sys.executable, "-m", "pytest", tests_path]
    if workers:
        cmd += ["-n", str(workers)]
    if marks:
        cmd += ["-m", str(marks)]
    if reruns and int(reruns) > 0:
        cmd += ["--reruns", str(reruns)]
    if count and int(count) > 0:
        cmd += ["--count", str(count)]
    if timeout and int(timeout) > 0:
        cmd += ["--timeout", str(timeout)]
    if extra:
        cmd += list(extra)
    return cmd, root_dir


def validate_marks_expression(marks: str) -> None:
    """Validate that the marks expression contains only known marks.

    Args:
        marks: The pytest marks expression to validate

    Raises:
        SystemExit: If unknown marks are found
    """
    if not marks or not marks.strip():
        return

    try:
        available_marks = get_all_available_marks()
        is_valid, unknown_marks = is_valid_mark_expression(marks, available_marks)

        if not is_valid:
            CONSOLE.print(
                f"[red]Error: Unknown pytest mark(s) found: {', '.join(unknown_marks)}[/red]"
            )
            CONSOLE.print(f"\n[yellow]Expression used:[/yellow] {marks}")
            print_marks_list(show_files=False)
            CONSOLE.print(
                "\n[dim]Use 'codemie-test-harness marks' to see all available marks[/dim]"
            )
            raise SystemExit(1)

    except Exception as e:
        # If mark validation fails for any reason, issue a warning but continue
        CONSOLE.print(f"[yellow]Warning: Could not validate marks: {str(e)}[/yellow]")


def run_pytest(
    workers: int,
    marks: str,
    reruns: int,
    count: int | None = None,
    timeout: int | None = None,
    extra: Iterable[str] | None = None,
) -> None:
    # Validate marks before running pytest
    validate_marks_expression(marks)

    cmd, root_dir = build_pytest_cmd(workers, marks, reruns, count, timeout, extra)
    CONSOLE.print(f"[cyan]Running:[/] {' '.join(cmd)} (cwd={root_dir})")
    raise SystemExit(subprocess.call(cmd, cwd=root_dir))
