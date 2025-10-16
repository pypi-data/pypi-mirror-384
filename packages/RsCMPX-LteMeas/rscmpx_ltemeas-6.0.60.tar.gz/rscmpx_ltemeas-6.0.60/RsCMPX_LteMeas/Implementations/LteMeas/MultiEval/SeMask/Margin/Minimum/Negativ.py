from typing import List

from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.Types import DataType
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class NegativCls:
	"""Negativ commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("negativ", core, parent)

	# noinspection PyTypeChecker
	class FetchStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Out_Of_Tolerance: int: Out of tolerance result, i.e. the percentage of measurement intervals of the statistic count for spectrum emission measurements exceeding the specified spectrum emission mask limits.
			- 3 Margin_Min_Neg_X: List[float]: No parameter help available
			- 4 Margin_Min_Neg_Y: List[float]: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct('Margin_Min_Neg_X', DataType.FloatList, None, False, True, 1),
			ArgStruct('Margin_Min_Neg_Y', DataType.FloatList, None, False, True, 1)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Out_Of_Tolerance: int = None
			self.Margin_Min_Neg_X: List[float] = None
			self.Margin_Min_Neg_Y: List[float] = None

	def fetch(self) -> FetchStruct:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:SEMask:MARGin:MINimum:NEGativ \n
		Snippet: value: FetchStruct = driver.lteMeas.multiEval.seMask.margin.minimum.negativ.fetch() \n
		Returns spectrum emission mask margin results. A negative margin indicates that the trace is located above the limit line,
		i.e. the limit is exceeded. The individual commands provide results for the CURRent, AVERage and maximum traces
		(resulting in MINimum margins) . For each trace, the x-value and y-value of the margin for emission mask areas 1 to 12
		are provided for NEGative and POSitive offset frequencies. For inactive areas, NCAP is returned. Returned sequence:
		<Reliability>, <OutOfTolerance>, {<MarginX>, <MarginY>}area1, {...}area2, ..., {...}area12 \n
			:return: structure: for return value, see the help for FetchStruct structure arguments."""
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:SEMask:MARGin:MINimum:NEGativ?', self.__class__.FetchStruct())
