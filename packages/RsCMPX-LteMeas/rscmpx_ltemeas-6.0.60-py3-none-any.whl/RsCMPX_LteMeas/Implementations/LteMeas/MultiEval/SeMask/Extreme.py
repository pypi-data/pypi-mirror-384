from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal.StructBase import StructBase
from .....Internal.ArgStruct import ArgStruct


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ExtremeCls:
	"""Extreme commands group definition. 3 total commands, 0 Subgroups, 3 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("extreme", core, parent)

	# noinspection PyTypeChecker
	class ResultData(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Out_Of_Tolerance: int: Out of tolerance result, i.e. the percentage of measurement intervals of the statistic count for spectrum emission measurements exceeding the specified spectrum emission mask limits.
			- 3 Obw: float: Occupied bandwidth
			- 4 Tx_Power_Min: float: Minimum total TX power in the slot
			- 5 Tx_Power_Max: float: Maximum total TX power in the slot"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct.scalar_float('Obw'),
			ArgStruct.scalar_float('Tx_Power_Min'),
			ArgStruct.scalar_float('Tx_Power_Max')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Out_Of_Tolerance: int = None
			self.Obw: float = None
			self.Tx_Power_Min: float = None
			self.Tx_Power_Max: float = None

	def read(self) -> ResultData:
		"""READ:LTE:MEASurement<Instance>:MEValuation:SEMask:EXTReme \n
		Snippet: value: ResultData = driver.lteMeas.multiEval.seMask.extreme.read() \n
		Return the extreme single-value results of the spectrum emission measurement. The values described below are returned by
		FETCh and READ commands. A CALCulate command returns limit check results instead, one value for each result listed below. \n
			:return: structure: for return value, see the help for ResultData structure arguments."""
		return self._core.io.query_struct(f'READ:LTE:MEASurement<Instance>:MEValuation:SEMask:EXTReme?', self.__class__.ResultData())

	def fetch(self) -> ResultData:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:SEMask:EXTReme \n
		Snippet: value: ResultData = driver.lteMeas.multiEval.seMask.extreme.fetch() \n
		Return the extreme single-value results of the spectrum emission measurement. The values described below are returned by
		FETCh and READ commands. A CALCulate command returns limit check results instead, one value for each result listed below. \n
			:return: structure: for return value, see the help for ResultData structure arguments."""
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:SEMask:EXTReme?', self.__class__.ResultData())

	# noinspection PyTypeChecker
	class CalculateStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Out_Of_Tolerance: int: Out of tolerance result, i.e. the percentage of measurement intervals of the statistic count for spectrum emission measurements exceeding the specified spectrum emission mask limits.
			- 3 Obw: float or bool: Occupied bandwidth
			- 4 Tx_Power_Min: float or bool: Minimum total TX power in the slot
			- 5 Tx_Power_Max: float or bool: Maximum total TX power in the slot"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct.scalar_float_ext('Obw'),
			ArgStruct.scalar_float_ext('Tx_Power_Min'),
			ArgStruct.scalar_float_ext('Tx_Power_Max')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Out_Of_Tolerance: int = None
			self.Obw: float or bool = None
			self.Tx_Power_Min: float or bool = None
			self.Tx_Power_Max: float or bool = None

	def calculate(self) -> CalculateStruct:
		"""CALCulate:LTE:MEASurement<Instance>:MEValuation:SEMask:EXTReme \n
		Snippet: value: CalculateStruct = driver.lteMeas.multiEval.seMask.extreme.calculate() \n
		Return the extreme single-value results of the spectrum emission measurement. The values described below are returned by
		FETCh and READ commands. A CALCulate command returns limit check results instead, one value for each result listed below. \n
			:return: structure: for return value, see the help for CalculateStruct structure arguments."""
		return self._core.io.query_struct(f'CALCulate:LTE:MEASurement<Instance>:MEValuation:SEMask:EXTReme?', self.__class__.CalculateStruct())
