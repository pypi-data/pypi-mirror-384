# ruff: noqa
import numpy

indexDistinctCrossings = int(0)  # noqa: RUF046, UP018
indexBifurcationAlpha = int(1)  # noqa: RUF046, UP018
indexBifurcationZulu = int(2)  # noqa: RUF046, UP018
indexCurveLocations = int(3)  # noqa: RUF046, UP018

def make1array(listArrays: list[numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.uint64]]]) -> numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.uint64]]:
	arrayCurveLocations: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.uint64]] = numpy.fromiter({element for stupidSystem in listArrays for element in stupidSystem[:, 1]}, dtype=numpy.uint64)

	arrayOut = numpy.column_stack((
		numpy.zeros(len(arrayCurveLocations), dtype=numpy.uint64)
		, arrayCurveLocations & numpy.uint64(0x5555555555555555)
		, (arrayCurveLocations & numpy.uint64(0xaaaaaaaaaaaaaaaa)) >> numpy.uint64(1)
		, arrayCurveLocations
	))
	for arrayCurveLocations in listArrays:
		arrayOut[:, indexDistinctCrossings] += numpy.sum(arrayCurveLocations[:, 0] * (arrayCurveLocations[:, -1][:, numpy.newaxis] == arrayOut[:, indexCurveLocations]).T, axis=1)

	return arrayOut  # The next `arrayBifurcations`

def convertDictionaryToNumPy(dictionaryIn: dict[int, int]) -> numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.uint64]]:
	arrayKeys: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.uint64]] = numpy.fromiter(dictionaryIn.keys(), dtype=numpy.uint64)

	return numpy.column_stack((
		numpy.fromiter(dictionaryIn.values(), dtype=numpy.uint64)
		, arrayKeys & numpy.uint64(0x5555555555555555)
		, (arrayKeys & numpy.uint64(0xaaaaaaaaaaaaaaaa)) >> numpy.uint64(1)
		, arrayKeys
	))

def count(bridges: int, startingCurveLocations: dict[int, int]) -> int:
	arrayBifurcations: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.uint64]] = convertDictionaryToNumPy(startingCurveLocations)

	while bridges > 0:
		bridges -= 1

		listArrayCurveLocationsAnalyzed: list[numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.uint64]]] = []

		# Selector-adjacent
		curveLocationsMAXIMUM: numpy.uint64 = numpy.uint64(1) << numpy.uint64(2 * bridges + 4)
		# Selectors, general
		selectBifurcationAlphaCurves: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool_]] = arrayBifurcations[:, indexBifurcationAlpha] != numpy.uint64(1)
		selectBifurcationAlphaEven: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool_]] = (arrayBifurcations[:, indexBifurcationAlpha] & numpy.uint64(1)) == numpy.uint64(0)
		selectBifurcationZuluCurves: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool_]] = arrayBifurcations[:, indexBifurcationZulu] != numpy.uint64(1)
		selectBifurcationZuluEven: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool_]] = (arrayBifurcations[:, indexBifurcationZulu] & numpy.uint64(1)) == numpy.uint64(0)

		# bridgesSimple
		selector: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool_]] = arrayBifurcations[:, indexDistinctCrossings] >= numpy.uint64(0) # This had better always be `True`.
		curveLocations: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.uint64]] = (((arrayBifurcations[selector, indexBifurcationAlpha] | (arrayBifurcations[selector, indexBifurcationZulu] << numpy.uint64(1))) << numpy.uint64(2)) | numpy.uint64(3))
		listArrayCurveLocationsAnalyzed.append(numpy.column_stack((arrayBifurcations[selector, indexDistinctCrossings][curveLocations < curveLocationsMAXIMUM], curveLocations[curveLocations < curveLocationsMAXIMUM])))

		# bifurcationAlphaCurves
		this = numpy.bitwise_or.reduce((
			arrayBifurcations[arrayBifurcations[:, indexBifurcationAlpha] != numpy.uint64(1), indexBifurcationAlpha] >> numpy.uint64(2)
			, arrayBifurcations[arrayBifurcations[:, indexBifurcationAlpha] != numpy.uint64(1), indexBifurcationZulu] << numpy.uint64(3)
			, (numpy.uint64(1) - (arrayBifurcations[arrayBifurcations[:, indexBifurcationAlpha] != numpy.uint64(1), indexBifurcationAlpha] & numpy.uint64(1))) << numpy.uint64(1)
		))
		curveLocations: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.uint64]] = numpy.where(this < curveLocationsMAXIMUM, this, numpy.uint64(0))
		# print(curveLocations.astype(numpy.bool_))
		print(curveLocations)
		distinctCrossings = arrayBifurcations[arrayBifurcations[:, indexBifurcationAlpha] != numpy.uint64(1), indexDistinctCrossings]
		print(distinctCrossings)
		listArrayCurveLocationsAnalyzed.append(
			numpy.column_stack((distinctCrossings, curveLocations))
		)
		# print(arrayBifurcations)
		# print(listArrayCurveLocationsAnalyzed[-1])

		# bifurcationZuluCurves
		selector = selectBifurcationZuluCurves
		curveLocations: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.uint64]] = numpy.bitwise_or.reduce((
			arrayBifurcations[selector, indexBifurcationZulu] >> numpy.uint64(1)
			, arrayBifurcations[selector, indexBifurcationAlpha] << numpy.uint64(2)
			, (numpy.uint64(1) - (arrayBifurcations[selector, indexBifurcationZulu] & numpy.uint64(1)))
		))
		listArrayCurveLocationsAnalyzed.append(numpy.column_stack((arrayBifurcations[selector, indexDistinctCrossings][curveLocations < curveLocationsMAXIMUM], curveLocations[curveLocations < curveLocationsMAXIMUM])))

		# Z0Z_bridgesBifurcationAlphaToRepair
		selector: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool_]] = numpy.logical_and.reduce((
			selectBifurcationAlphaCurves, selectBifurcationZuluCurves, selectBifurcationAlphaEven, ~selectBifurcationZuluEven
		))

		# Initialize
		XOrHere2makePair = numpy.uint64(1)

		while selector.any():
			XOrHere2makePair <<= numpy.uint64(2)

			selectUnpaired_0b1: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool_]] = (arrayBifurcations[:, indexBifurcationAlpha] & XOrHere2makePair) == numpy.uint64(0)
			selectorUnified: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool_]] = numpy.logical_and.reduce((selector, selectUnpaired_0b1))

			# Modify in place
			arrayBifurcations[selectorUnified, indexBifurcationAlpha] ^= XOrHere2makePair

			# Remove the modified elements
			selector: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool_]] = numpy.logical_and.reduce((selector, ~selectorUnified))

		selector: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool_]] = numpy.logical_and.reduce((
			selectBifurcationAlphaCurves, selectBifurcationZuluCurves, selectBifurcationAlphaEven, ~selectBifurcationZuluEven
		))
		curveLocations: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.uint64]] = (
			((arrayBifurcations[selector, indexBifurcationZulu] >> numpy.uint64(2)) << numpy.uint64(1))
			| (arrayBifurcations[selector, indexBifurcationAlpha] >> numpy.uint64(2))
		)

		listArrayCurveLocationsAnalyzed.append(numpy.column_stack((arrayBifurcations[selector, indexDistinctCrossings][curveLocations < curveLocationsMAXIMUM], curveLocations[curveLocations < curveLocationsMAXIMUM])))

		# Z0Z_bridgesBifurcationZuluToRepair
		selector: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool_]] = numpy.logical_and.reduce((
			selectBifurcationAlphaCurves, selectBifurcationZuluCurves, ~selectBifurcationAlphaEven, selectBifurcationZuluEven
		))

		# Initialize
		XOrHere2makePair: numpy.uint64 = numpy.uint64(1)

		while selector.any():
			XOrHere2makePair <<= numpy.uint64(2)

			# New condition
			selectUnpaired_0b1: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool_]] = (arrayBifurcations[:, indexBifurcationZulu] & XOrHere2makePair) == numpy.uint64(0)
			selectorUnified: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool_]] = numpy.logical_and.reduce((selector, selectUnpaired_0b1))

			# Modify in place
			arrayBifurcations[selectorUnified, indexBifurcationZulu] ^= XOrHere2makePair

			# Remove the modified elements from the selector
			selector: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool_]] = numpy.logical_and.reduce((selector, ~selectorUnified))

		selector: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool_]] = numpy.logical_and.reduce((
			selectBifurcationAlphaCurves, selectBifurcationZuluCurves, ~selectBifurcationAlphaEven, selectBifurcationZuluEven
		))

		curveLocations: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.uint64]] = (
			((arrayBifurcations[selector, indexBifurcationZulu] >> numpy.uint64(2)) << numpy.uint64(1))
			| (arrayBifurcations[selector, indexBifurcationAlpha] >> numpy.uint64(2))
		)

		listArrayCurveLocationsAnalyzed.append(numpy.column_stack((arrayBifurcations[selector, indexDistinctCrossings][curveLocations < curveLocationsMAXIMUM], curveLocations[curveLocations < curveLocationsMAXIMUM])))

		# Z0Z_bridgesAligned
		selector: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool_]] = numpy.logical_and.reduce((
			selectBifurcationAlphaCurves, selectBifurcationZuluCurves, selectBifurcationAlphaEven, selectBifurcationZuluEven
		))

		curveLocations: numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.uint64]] = (
			((arrayBifurcations[selector, indexBifurcationZulu] >> numpy.uint64(2)) << numpy.uint64(1))
			| (arrayBifurcations[selector, indexBifurcationAlpha] >> numpy.uint64(2))
		)

		listArrayCurveLocationsAnalyzed.append(numpy.column_stack((arrayBifurcations[selector, indexDistinctCrossings][curveLocations < curveLocationsMAXIMUM], curveLocations[curveLocations < curveLocationsMAXIMUM])))

		arrayBifurcations = make1array(listArrayCurveLocationsAnalyzed)

		listArrayCurveLocationsAnalyzed.clear()

		# print(int(sum(arrayBifurcations[:, 0])))
	return int(sum(arrayBifurcations[:, 0]))

