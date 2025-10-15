"""Oft-needed computations or actions, especially for multi-dimensional map folding."""

from collections.abc import Sequence
from hunterMakesPy import defineConcurrencyLimit, intInnit, oopsieKwargsie
from mapFolding import NumPyIntegerType
from numpy import dtype as numpy_dtype, int64 as numpy_int64, ndarray
from sys import maxsize as sysMaxsize
from typing import Any
import numpy

def getLeavesTotal(mapShape: tuple[int, ...]) -> int:
	"""Calculate the total number of leaves in a map with the given dimensions.

	The total number of leaves is the product of all dimensions in the map shape.

	Parameters
	----------
	mapShape : tuple[int, ...]
		A tuple of integers representing the dimensions of the map.

	Returns
	-------
	leavesTotal : int
		The total number of leaves in the map, calculated as the product of all dimensions.

	Raises
	------
	OverflowError
		If the product of dimensions would exceed the system's maximum integer size. This check prevents silent numeric
		overflow issues that could lead to incorrect results.

	"""
	productDimensions = 1
	for dimension in mapShape:
		# NOTE this check is one-degree short of absurd, but three lines of early absurdity is better than invalid output later. I'd add more checks if I could think of more.
		if dimension > sysMaxsize // productDimensions:
			message = f"I received `{dimension = }` in `{mapShape = }`, but the product of the dimensions exceeds the maximum size of an integer on this system."
			raise OverflowError(message)
		productDimensions *= dimension
	return productDimensions

def getTaskDivisions(computationDivisions: int | str | None, concurrencyLimit: int, leavesTotal: int) -> int:
	"""Determine whether to divide the computation into tasks and how many divisions.

	Parameters
	----------
	computationDivisions : int | str | None
		Specifies how to divide computations. Please see the documentation in `countFolds` for details. I know it is
		annoying, but I want to be sure you have the most accurate information.
	concurrencyLimit : int
		Maximum number of concurrent tasks allowed.
	leavesTotal : int
		Total number of leaves in the map.

	Returns
	-------
	taskDivisions : int
		How many tasks must finish before the job can compute the total number of folds. `0` means no tasks, only job.

	Raises
	------
	ValueError
		If `computationDivisions` is an unsupported type or if resulting task divisions exceed total leaves.

	Notes
	-----
	Task divisions should not exceed total leaves or the folds will be over-counted.

	"""
	taskDivisions = 0
	match computationDivisions:
		case None | 0 | False:
			pass
		case int() as intComputationDivisions:
			taskDivisions = intComputationDivisions
		case str() as strComputationDivisions:
			strComputationDivisions = strComputationDivisions.lower()
			match strComputationDivisions:
				case 'maximum':
					taskDivisions = leavesTotal
				case 'cpu':
					taskDivisions = min(concurrencyLimit, leavesTotal)
				case _:
					message = f"I received '{strComputationDivisions}' for the parameter, `computationDivisions`, but the string value is not supported."
					raise ValueError(message)
		case _:
			message = f"I received {computationDivisions} for the parameter, `computationDivisions`, but the type {type(computationDivisions).__name__} is not supported."
			raise ValueError(message)

	if taskDivisions > leavesTotal:
		message = f"Problem: `{taskDivisions = }`, is greater than `{leavesTotal = }`, which will cause duplicate counting of the folds.\n\nChallenge: you cannot directly set `taskDivisions` or `leavesTotal`: they are derived from parameters that may or may not be named `computationDivisions`, `CPUlimit` , and `listDimensions` and from my dubious-quality Python code."  # noqa: E501
		raise ValueError(message)
	return int(max(0, taskDivisions))

def _makeConnectionGraph(mapShape: tuple[int, ...], leavesTotal: int) -> ndarray[tuple[int, int, int], numpy_dtype[numpy_int64]]:
	"""Implement connection graph generation for map folding.

	Parameters
	----------
	mapShape : tuple[int, ...]
		A tuple of integers representing the dimensions of the map.
	leavesTotal : int
		The total number of leaves in the map.

	Returns
	-------
	connectionGraph : ndarray[tuple[int, int, int], numpy_dtype[numpy_int64]]
		A 3D NumPy array with shape (`dimensionsTotal`, `leavesTotal`+1, `leavesTotal`+1) where each entry [d,i,j]
		represents the leaf that would be connected to leaf j when inserting leaf i in dimension d.

	Notes
	-----
	This is an implementation detail and shouldn't be called directly by external code. Use `getConnectionGraph`
	instead, which applies proper typing.

	The algorithm calculates a coordinate system first, then determines connections based on parity rules, boundary
	conditions, and dimensional constraints.

	"""
	dimensionsTotal = len(mapShape)
	cumulativeProduct = numpy.multiply.accumulate([1, *list(mapShape)], dtype=numpy_int64)
	arrayDimensions = numpy.array(mapShape, dtype=numpy_int64)
	coordinateSystem = numpy.zeros((dimensionsTotal, leavesTotal + 1), dtype=numpy_int64)
	for indexDimension in range(dimensionsTotal):
		for leaf1ndex in range(1, leavesTotal + 1):
			coordinateSystem[indexDimension, leaf1ndex] = (((leaf1ndex - 1) // cumulativeProduct[indexDimension]) % arrayDimensions[indexDimension] + 1)

	connectionGraph = numpy.zeros((dimensionsTotal, leavesTotal + 1, leavesTotal + 1), dtype=numpy_int64)
	for indexDimension in range(dimensionsTotal):
		for activeLeaf1ndex in range(1, leavesTotal + 1):
			for connectee1ndex in range(1, activeLeaf1ndex + 1):
				isFirstCoord = coordinateSystem[indexDimension, connectee1ndex] == 1
				isLastCoord = coordinateSystem[indexDimension, connectee1ndex] == arrayDimensions[indexDimension]
				exceedsActive = connectee1ndex + cumulativeProduct[indexDimension] > activeLeaf1ndex
				isEvenParity = (coordinateSystem[indexDimension, activeLeaf1ndex] & 1) == (coordinateSystem[indexDimension, connectee1ndex] & 1)

				if (isEvenParity and isFirstCoord) or (not isEvenParity and (isLastCoord or exceedsActive)):
					connectionGraph[indexDimension, activeLeaf1ndex, connectee1ndex] = connectee1ndex
				elif isEvenParity and not isFirstCoord:
					connectionGraph[indexDimension, activeLeaf1ndex, connectee1ndex] = connectee1ndex - cumulativeProduct[indexDimension]
				elif not isEvenParity and not (isLastCoord or exceedsActive):
					connectionGraph[indexDimension, activeLeaf1ndex, connectee1ndex] = connectee1ndex + cumulativeProduct[indexDimension]
	return connectionGraph

def getConnectionGraph(mapShape: tuple[int, ...], leavesTotal: int, datatype: type[NumPyIntegerType]) -> ndarray[tuple[int, int, int], numpy_dtype[NumPyIntegerType]]:
	"""Create a properly typed connection graph for the map folding algorithm.

	Parameters
	----------
	mapShape : tuple[int, ...]
		A tuple of integers representing the dimensions of the map.
	leavesTotal : int
		The total number of leaves in the map.
	datatype : type[NumPyIntegerType]
		The NumPy integer type to use for the array elements, ensuring proper memory usage and compatibility with the
		computation state.

	Returns
	-------
	connectionGraph : ndarray[tuple[int, int, int], numpy_dtype[NumPyIntegerType]]
		A 3D NumPy array with shape (`dimensionsTotal`, `leavesTotal`+1, `leavesTotal`+1) with the specified `datatype`,
		representing all possible connections between leaves.

	"""
	connectionGraph = _makeConnectionGraph(mapShape, leavesTotal)
	return connectionGraph.astype(datatype)

def makeDataContainer(shape: int | tuple[int, ...], datatype: type[NumPyIntegerType]) -> ndarray[Any, numpy_dtype[NumPyIntegerType]]:
	"""Create any data container as long as it is a `numpy.ndarray` full of zeroes of type `numpy.integer`.

	By centralizing data container creation, you can more easily make global changes.

	Parameters
	----------
	shape : int | tuple[int, ...]
		The array shape, either as a single axis length or a tuple of axes lengths.
	datatype : type[NumPyIntegerType]
		The `numpy.integer` type for the array elements.

	Returns
	-------
	container : ndarray[Any, numpy_dtype[NumPyIntegerType]]
		A zero-filled `ndarray` with the specified `shape` and `datatype`.

	"""
	return numpy.zeros(shape, dtype=datatype)

def setProcessorLimit(CPUlimit: Any | None, concurrencyPackage: str | None = None) -> int:
	"""Set the CPU usage limit for concurrent operations.

	Parameters
	----------
	CPUlimit : Any | None
		Please see the documentation in `countFolds` for details. I know it is annoying, but I want to be sure you
		have the most accurate information.
	concurrencyPackage : str | None = None
		Specifies which concurrency package to use.
		- `None` or `'multiprocessing'`: Uses standard `multiprocessing`.
		- `'numba'`: Uses Numba's threading system.

	Returns
	-------
	concurrencyLimit : int
		The actual concurrency limit that was set.

	Raises
	------
	TypeError
		If `CPUlimit` is not of the expected types.
	NotImplementedError
		If `concurrencyPackage` is not supported.

	Notes
	-----
	If using `'numba'` as the concurrency package, the maximum number of processors is retrieved from
	`numba.get_num_threads()` rather than by polling the hardware. If Numba environment variables limit available
	processors, that will affect this function.

	When using Numba, this function must be called before importing any Numba-jitted function for this processor limit
	to affect the Numba-jitted function.

	"""
	if not (CPUlimit is None or isinstance(CPUlimit, (bool, int, float))):
		CPUlimit = oopsieKwargsie(CPUlimit)

	match concurrencyPackage:
		case 'multiprocessing' | None:
			# When to use multiprocessing.set_start_method
			# https://github.com/hunterhogan/mapFolding/issues/6  # noqa: ERA001
			concurrencyLimit: int = defineConcurrencyLimit(limit=CPUlimit)
		case 'numba':
			from numba import get_num_threads, set_num_threads  # noqa: PLC0415
			concurrencyLimit = defineConcurrencyLimit(limit=CPUlimit, cpuTotal=get_num_threads())
			set_num_threads(concurrencyLimit)
			concurrencyLimit = get_num_threads()
		case _:
			message = f"I received `{concurrencyPackage = }` but I don't know what to do with that."
			raise NotImplementedError(message)
	return concurrencyLimit

def validateListDimensions(listDimensions: Sequence[int]) -> tuple[int, ...]:
	"""Validate and normalize dimensions for a map folding problem.

	(AI generated docstring)

	This function serves as the gatekeeper for dimension inputs, ensuring that all map dimensions provided to the
	package meet the requirements for valid computation. It performs multiple validation steps and normalizes the
	dimensions into a consistent format.

	Parameters
	----------
	listDimensions : Sequence[int]
		A sequence of integers representing the dimensions of the map.

	Returns
	-------
	mapShape : tuple[int, ...]
		An _unsorted_ tuple of positive integers representing the validated dimensions.

	Raises
	------
	ValueError
		If the input is empty or contains negative values.
	NotImplementedError
		If fewer than two positive dimensions are provided.

	"""
	if not listDimensions:
		message = "`listDimensions` is a required parameter."
		raise ValueError(message)
	listOFint: list[int] = intInnit(listDimensions, 'listDimensions')
	mapDimensions: list[int] = []
	for dimension in listOFint:
		if dimension <= 0:
			message = f"I received `{dimension = }` in `{listDimensions = }`, but all dimensions must be a non-negative integer."
			raise ValueError(message)
		mapDimensions.append(dimension)
	if len(mapDimensions) < 2:
		message = f"This function requires `{listDimensions = }` to have at least two dimensions greater than 0. You may want to look at https://oeis.org/."
		raise NotImplementedError(message)

	"""
	I previously sorted the dimensions for a few reasons that may or may not be valid:
		1. After empirical testing, I believe that (2,10), for example, computes significantly faster than (10,2).
		2. Standardization, generally.
		3. If I recall correctly, after empirical testing, I concluded that sorted dimensions always leads to
		non-negative values in the connection graph, but if the dimensions are not in ascending order of magnitude,
		the connection graph might have negative values, which as far as I know, is not an inherent problem, but the
		negative values propagate into other data structures, which requires the datatypes to hold negative values,
		which means I cannot optimize the bit-widths of the datatypes as easily. (And optimized bit-widths helps with
		performance.)

	Furthermore, now that the package includes OEIS A000136, 1 x N stamps/maps, sorting could distort results.
	"""
	# NOTE Do NOT sort the dimensions.
	return tuple(mapDimensions)
