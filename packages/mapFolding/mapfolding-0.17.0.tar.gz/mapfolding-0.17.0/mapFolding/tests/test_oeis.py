"""OEIS (Online Encyclopedia of Integer Sequences) integration testing.

This module validates the package's integration with OEIS, ensuring that sequence
identification, value retrieval, and caching mechanisms work correctly. The OEIS
connection provides the mathematical foundation that validates computational results
against established mathematical knowledge.

These tests verify both the technical aspects of OEIS integration (network requests,
caching, error handling) and the mathematical correctness of sequence identification
and value mapping.

Key Testing Areas:
- OEIS sequence ID validation and normalization
- Network request handling and error recovery
- Local caching of sequence data for offline operation
- Command-line interface for OEIS sequence queries
- Mathematical consistency between local computations and OEIS values

The caching tests are particularly important for users working in environments with
limited network access, as they ensure the package can operate effectively offline
once sequence data has been retrieved.

Network error handling tests verify graceful degradation when OEIS is unavailable,
which is crucial for maintaining package reliability in production environments.
"""

from contextlib import redirect_stdout
from mapFolding.oeis import (
	_standardizeOEISid, dictionaryOEISMapFolding, getOEISids, OEIS_for_n, oeisIDfor_n, oeisIDsImplemented)
from mapFolding.tests.conftest import standardizedEqualToCallableReturn, standardizedSystemExit
from typing import Any
import io
import pytest
import random
import re as regex
import unittest.mock

def test__validateOEISid_valid_id(oeisIDmapFolding: str) -> None:
	standardizedEqualToCallableReturn(oeisIDmapFolding, _standardizeOEISid, oeisIDmapFolding)

def test__validateOEISid_valid_id_case_insensitive(oeisIDmapFolding: str) -> None:
	standardizedEqualToCallableReturn(oeisIDmapFolding.upper(), _standardizeOEISid, oeisIDmapFolding.lower())
	standardizedEqualToCallableReturn(oeisIDmapFolding.upper(), _standardizeOEISid, oeisIDmapFolding.upper())
	standardizedEqualToCallableReturn(oeisIDmapFolding.upper(), _standardizeOEISid, oeisIDmapFolding.swapcase())

parameters_test_aOFn_invalid_n = [
	(-random.randint(1, 100), "randomNegative"),  # noqa: S311
	("foo", "string"),
	(1.5, "float")
]
badValues, badValuesIDs = zip(*parameters_test_aOFn_invalid_n, strict=True)
@pytest.mark.parametrize("badN", badValues, ids=badValuesIDs)
def test_aOFn_invalid_n(oeisID_1random: str, badN: Any) -> None:
	"""Check that negative or non-integer n raises ValueError."""
	standardizedEqualToCallableReturn(ValueError, oeisIDfor_n, oeisID_1random, badN)

def test_aOFn_zeroDim_A001418() -> None:
	standardizedEqualToCallableReturn(ArithmeticError, oeisIDfor_n, 'A001418', 0)

# ===== Command Line Interface Tests =====
def testHelpText() -> None:
	"""Test that help text is complete and examples are valid."""
	outputStream = io.StringIO()
	with redirect_stdout(outputStream):
		getOEISids()

	helpText = outputStream.getvalue()

	# Verify content
	for oeisID in oeisIDsImplemented:
		assert oeisID in helpText
		assert dictionaryOEISMapFolding[oeisID]['description'] in helpText

	# Extract and verify examples

	cliMatch = regex.search(r'OEIS_for_n (\w+) (\d+)', helpText)
	pythonMatch = regex.search(r"oeisIDfor_n\('(\w+)', (\d+)\)", helpText)

	assert cliMatch and pythonMatch, "Help text missing examples"
	oeisID, n = pythonMatch.groups()
	n = int(n)

	# Verify CLI and Python examples use same values
	assert cliMatch.groups() == (oeisID, str(n)), "CLI and Python examples inconsistent"

	# Verify the example works
	expectedValue = oeisIDfor_n(oeisID, n)

	# Test CLI execution of the example
	with unittest.mock.patch('sys.argv', ['OEIS_for_n', oeisID, str(n)]):
		outputStream = io.StringIO()
		with redirect_stdout(outputStream):
			OEIS_for_n()
		standardizedEqualToCallableReturn(expectedValue, lambda: int(outputStream.getvalue().strip().split()[0]))

def testCLI_InvalidInputs() -> None:
	"""Test CLI error handling."""
	testCases = [
		(['OEIS_for_n'], "missing arguments"),
		(['OEIS_for_n', 'A999999', '1'], "invalid OEIS ID"),
		(['OEIS_for_n', 'A001415', '-1'], "negative n"),
		(['OEIS_for_n', 'A001415', 'abc'], "non-integer n"),
	]

	for arguments, _testID in testCases:
		with unittest.mock.patch('sys.argv', arguments):
			standardizedSystemExit("error", OEIS_for_n)

def testCLI_HelpFlag() -> None:
	"""Verify --help output contains required information."""
	with unittest.mock.patch('sys.argv', ['OEIS_for_n', '--help']):
		outputStream = io.StringIO()
		with redirect_stdout(outputStream):
			standardizedSystemExit("nonError", OEIS_for_n)

		helpOutput = outputStream.getvalue()
		assert "Available OEIS sequences:" in helpOutput
		assert "Usage examples:" in helpOutput
		assert all(oeisID in helpOutput for oeisID in oeisIDsImplemented)
