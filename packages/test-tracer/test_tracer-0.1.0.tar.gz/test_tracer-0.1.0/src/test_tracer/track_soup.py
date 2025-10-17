import pytest
from pathlib import Path
import os
from black.trans import defaultdict
from coverage import Coverage
import sqlite3
from coverage.numbits import register_sqlite_functions

from test_tracer.test_case import TestCase


DB_DIR = ".coverage"


def get_soup_component(soup_file: Path):
    """Extract SOUP components from text file."""
    with open(soup_file, "r") as f:
        lines = f.readlines()

    return [l.strip() for l in lines if l.strip()]


def run_tests_with_coverage(test_path: Path, soup_components: list[str]) -> None:
    """Run selected tests with coverage."""
    cov = Coverage(
        data_file=DB_DIR,
        source=[str(test_path)],
        source_pkgs=soup_components,
        auto_data=True,
        config_file="pyproject.toml",
        context="test_function",  # Sets dynamic context switching
    )
    cov.start()
    pytest.main(["-x", test_path])
    cov.stop()
    cov.save()


def get_coverage_data(soup_components: list[str]) -> dict[str,set]:
    """Query sqlite DB for coverage data."""
    conn = sqlite3.connect(DB_DIR)
    register_sqlite_functions(conn)
    c = conn.cursor()
    _result = c.execute(
        "select c.context, group_concat(f.path) "
        "from context c "
        "inner join line_bits lb on lb.context_id = c.id "
        "inner join file f on f.id = lb.file_id "
        "where c.context != 'test_function' "
        "group by c.context"
    )

    test_soup: dict[str, set] = defaultdict()
    for row in _result.fetchall():

        test_func_name = row[0].split(".")[1]
        test_file_path = Path(row[1].split(",")[0]).relative_to(os.getcwd())
        test_path = f"{test_file_path}::{test_func_name}"  # should match test_path from trace_requirements

        # Combine files into SOUP types
        test_soup[test_path] = set()
        for s in soup_components:
            if s in row[1]:
                test_soup[str(test_path)].add(s)

    return test_soup


def add_soup_to_tests(test_soup: dict[str,set], tests: list[TestCase]) -> list[TestCase]:
    """Add SOUP components to traced tests.

    Test SOUP keys should match TestCase.test_path
    """
    for test_case in tests:
        if test_soup.get(test_case.test_path):
            test_case.soup_components = ", ".join(test_soup[test_case.test_path])

    return tests


def add_tracked_soup(tests, test_path: Path, soup_file_path: Path) -> list[TestCase]:
    """Run pytest and record SOUP components used."""
    soup_components = get_soup_component(soup_file_path)
    run_tests_with_coverage(test_path, soup_components)
    test_soup = get_coverage_data(soup_components)

    return add_soup_to_tests(test_soup, tests)

