from typing import List

from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal.Types import DataType
from ......Internal.StructBase import StructBase
from ......Internal.ArgStruct import ArgStruct


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class AllCls:
	"""All commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("all", core, parent)

	# noinspection PyTypeChecker
	class FetchStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Out_Of_Tolerance: int: Out of tolerance result, i.e. the percentage of measurement intervals of the statistic count for spectrum emission measurements exceeding the specified spectrum emission mask limits.
			- 3 Margin_Curr_Neg: List[float]: No parameter help available
			- 4 Margin_Curr_Pos: List[float]: No parameter help available
			- 5 Margin_Avg_Neg: List[float]: No parameter help available
			- 6 Margin_Avg_Pos: List[float]: No parameter help available
			- 7 Margin_Min_Neg: List[float]: No parameter help available
			- 8 Margin_Min_Pos: List[float]: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct('Margin_Curr_Neg', DataType.FloatList, None, False, False, 12),
			ArgStruct('Margin_Curr_Pos', DataType.FloatList, None, False, False, 12),
			ArgStruct('Margin_Avg_Neg', DataType.FloatList, None, False, False, 12),
			ArgStruct('Margin_Avg_Pos', DataType.FloatList, None, False, False, 12),
			ArgStruct('Margin_Min_Neg', DataType.FloatList, None, False, False, 12),
			ArgStruct('Margin_Min_Pos', DataType.FloatList, None, False, False, 12)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Out_Of_Tolerance: int = None
			self.Margin_Curr_Neg: List[float] = None
			self.Margin_Curr_Pos: List[float] = None
			self.Margin_Avg_Neg: List[float] = None
			self.Margin_Avg_Pos: List[float] = None
			self.Margin_Min_Neg: List[float] = None
			self.Margin_Min_Pos: List[float] = None

	def fetch(self) -> FetchStruct:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:SEMask:MARGin:ALL \n
		Snippet: value: FetchStruct = driver.lteMeas.multiEval.seMask.margin.all.fetch() \n
		Returns spectrum emission mask margin results. A negative margin indicates that the trace is located above the limit line,
		i.e. the limit is exceeded. Results are provided for the current, average and maximum traces. For each trace, 24 values
		related to the negative (Neg) and positive (Pos) offset frequencies of emission mask areas 1 to 12 are provided.
		For inactive areas, NCAP is returned. \n
			:return: structure: for return value, see the help for FetchStruct structure arguments."""
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:SEMask:MARGin:ALL?', self.__class__.FetchStruct())
