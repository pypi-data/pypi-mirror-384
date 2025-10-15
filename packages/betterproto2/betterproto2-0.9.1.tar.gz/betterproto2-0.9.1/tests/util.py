import importlib
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import pytest

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

root_path = Path(__file__).resolve().parent
inputs_path = root_path.joinpath("inputs")


def get_directories(path):
    for root, directories, files in os.walk(path):
        yield from directories


@dataclass
class TestCaseJsonFile:
    json: str
    test_name: str
    file_name: str


def get_test_case_json_data(test_case_name: str, *json_file_names: str) -> list[TestCaseJsonFile]:
    """
    :return:
        A list of all files found in "{inputs_path}/test_case_name" with names matching
        f"{test_case_name}.json" or f"{test_case_name}_*.json", OR given by
        json_file_names
    """
    test_case_dir = inputs_path.joinpath(test_case_name)
    possible_file_paths = [
        *(test_case_dir.joinpath(json_file_name) for json_file_name in json_file_names),
        test_case_dir.joinpath(f"{test_case_name}.json"),
        *test_case_dir.glob(f"{test_case_name}_*.json"),
    ]

    result = []
    for test_data_file_path in possible_file_paths:
        if not test_data_file_path.exists():
            continue
        with test_data_file_path.open("r") as fh:
            result.append(TestCaseJsonFile(fh.read(), test_case_name, test_data_file_path.name.split(".")[0]))

    return result


def find_module(module: ModuleType, predicate: Callable[[ModuleType], bool]) -> ModuleType | None:
    """
    Recursively search module tree for a module that matches the search predicate.
    Assumes that the submodules are directories containing __init__.py.

    Example:

        # find module inside foo that contains Test
        import foo
        test_module = find_module(foo, lambda m: hasattr(m, 'Test'))
    """
    if predicate(module):
        return module

    module_path = Path(*module.__path__)

    for sub in [sub.parent for sub in module_path.glob("**/__init__.py")]:
        if sub == module_path:
            continue
        sub_module_path = sub.relative_to(module_path)
        sub_module_name = ".".join(sub_module_path.parts)

        sub_module = importlib.import_module(f".{sub_module_name}", module.__name__)

        if predicate(sub_module):
            return sub_module

    return None


@pytest.fixture
def requires_pydantic():
    try:
        import pydantic  # noqa: F401
    except ImportError:
        pytest.skip("pydantic is not installed")


@pytest.fixture
def requires_grpclib():
    try:
        import grpclib  # noqa: F401
    except ImportError:
        pytest.skip("grpclib is not installed")


@pytest.fixture
def requires_grpcio():
    try:
        import grpc  # noqa: F401
    except ImportError:
        pytest.skip("grpcio is not installed")


@pytest.fixture
def requires_protobuf():
    try:
        import google.protobuf  # noqa: F401
    except ImportError:
        pytest.skip("protobuf is not installed")
