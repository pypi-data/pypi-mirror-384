"""Parallel processing and task distribution validation.

This module tests the package's parallel processing capabilities, ensuring that
computations can be effectively distributed across multiple processors while
maintaining mathematical accuracy. These tests are crucial for performance
optimization and scalability.

The task distribution system allows large computational problems to be broken
down into smaller chunks that can be processed concurrently. These tests verify
that the distribution logic works correctly and that results remain consistent
regardless of how the work is divided.

Key Testing Areas:
- Task division strategies for different computational approaches
- Processor limit configuration and enforcement
- Parallel execution consistency and correctness
- Resource management and concurrency control
- Error handling in multi-process environments

For users working with large-scale computations: these tests demonstrate how to
configure and validate parallel processing setups. The concurrency limit tests
show how to balance performance with system resource constraints.

The multiprocessing configuration (spawn method) is essential for cross-platform
compatibility and proper resource isolation between test processes.
"""

from collections.abc import Callable
from hunterMakesPy.pytestForYourUse import PytestFor_defineConcurrencyLimit
from mapFolding import (
	countFolds, getFoldsTotalKnown, getLeavesTotal, getTaskDivisions, setProcessorLimit, validateListDimensions)
from mapFolding.tests.conftest import standardizedEqualToCallableReturn
from typing import Literal
import multiprocessing
import pytest

# When to use multiprocessing.set_start_method
# https://github.com/hunterhogan/mapFolding/issues/6
if __name__ == '__main__':
	multiprocessing.set_start_method('spawn')

def test_countFoldsComputationDivisionsInvalid(mapShapeTestFunctionality: tuple[int, ...]) -> None:
	standardizedEqualToCallableReturn(ValueError, countFolds, mapShapeTestFunctionality, None, {"wrong": "value"})

def test_countFoldsComputationDivisionsMaximum(mapShapeTestParallelization: list[int]) -> None:
	standardizedEqualToCallableReturn(getFoldsTotalKnown(tuple(mapShapeTestParallelization)), countFolds, mapShapeTestParallelization, None, 'maximum', None)

@pytest.mark.parametrize("nameOfTest,callablePytest", PytestFor_defineConcurrencyLimit())
def test_defineConcurrencyLimit(nameOfTest: str, callablePytest: Callable[[], None]) -> None:
	callablePytest()

@pytest.mark.parametrize("CPUlimitParameter", [{"invalid": True}, ["weird"]])
def test_countFolds_cpuLimitOopsie(mapShapeTestFunctionality: tuple[int, ...], CPUlimitParameter: dict[str, bool] | list[str]) -> None:
	standardizedEqualToCallableReturn(ValueError, countFolds, mapShapeTestFunctionality, None, 'cpu', CPUlimitParameter)

@pytest.mark.parametrize("computationDivisions, concurrencyLimit, listDimensions, expectedTaskDivisions", [
	(None, 4, [9, 11], 0),
	("maximum", 4, [7, 11], 77),
	("cpu", 4, [3, 7], 4),
	(["invalid"], 4, [19, 23], ValueError),
	(20, 4, [3,5], ValueError)
])
def test_getTaskDivisions(computationDivisions: Literal['maximum', 'cpu', 20] | None | list[str]
						, concurrencyLimit: Literal[4]
						, listDimensions: list[int]
						, expectedTaskDivisions: Literal[0, 77, 4] | type[ValueError]) -> None:
	mapShape = validateListDimensions(listDimensions)
	leavesTotal = getLeavesTotal(mapShape)
	standardizedEqualToCallableReturn(expectedTaskDivisions, getTaskDivisions, computationDivisions, concurrencyLimit, leavesTotal)

@pytest.mark.parametrize("expected,parameter", [
	(ValueError, [4]),  # list
	(ValueError, (2,)), # tuple
	(ValueError, {2}),  # set
	(ValueError, {"cores": 2}),  # dict
])
def test_setCPUlimitMalformedParameter(expected: type[ValueError] | Literal[2], parameter: list[int] | tuple[int] | set[int] | dict[str, int] | Literal['2']) -> None:
	"""Test that invalid CPUlimit types are properly handled."""
	standardizedEqualToCallableReturn(expected, setProcessorLimit, parameter)
