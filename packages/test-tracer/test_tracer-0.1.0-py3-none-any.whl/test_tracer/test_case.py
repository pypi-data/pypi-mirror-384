"""Dataclasses for Test Cases"""
from dataclasses import dataclass


@dataclass
class TestDefinition:
    description: str
    precondition: str
    steps: str
    expected_result: str
    req_ids: list[str]


@dataclass
class TestCase:
    id: str|None
    name: str
    file_path: str
    test_path: str
    definition: TestDefinition
    soup_components: str|None

