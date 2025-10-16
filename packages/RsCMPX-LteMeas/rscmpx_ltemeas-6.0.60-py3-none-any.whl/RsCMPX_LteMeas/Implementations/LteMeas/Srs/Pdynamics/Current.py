from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal.StructBase import StructBase
from .....Internal.ArgStruct import ArgStruct


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class CurrentCls:
	"""Current commands group definition. 3 total commands, 0 Subgroups, 3 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("current", core, parent)

	# noinspection PyTypeChecker
	class ResultData(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Out_Of_Tolerance: int: Out of tolerance result, i.e. the percentage of measurement intervals of the statistic count for power dynamics measurements exceeding the specified power dynamics limits.
			- 3 Off_Power_Before: float: OFF power average value for the time period before the SRS symbol.
			- 4 On_Power_Rms_1: float: ON power average value over the first SRS symbol.
			- 5 On_Power_Peak_1: float: ON power peak value for the first SRS symbol.
			- 6 On_Power_Rms_2: float: ON power average value over the second SRS symbol (NCAP returned for FDD) .
			- 7 On_Power_Peak_2: float: ON power peak value for the second SRS symbol (NCAP returned for FDD) .
			- 8 Off_Power_After: float: OFF power average value for the subframe after the SRS symbol."""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct.scalar_float('Off_Power_Before'),
			ArgStruct.scalar_float('On_Power_Rms_1'),
			ArgStruct.scalar_float('On_Power_Peak_1'),
			ArgStruct.scalar_float('On_Power_Rms_2'),
			ArgStruct.scalar_float('On_Power_Peak_2'),
			ArgStruct.scalar_float('Off_Power_After')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Out_Of_Tolerance: int = None
			self.Off_Power_Before: float = None
			self.On_Power_Rms_1: float = None
			self.On_Power_Peak_1: float = None
			self.On_Power_Rms_2: float = None
			self.On_Power_Peak_2: float = None
			self.Off_Power_After: float = None

	def read(self) -> ResultData:
		"""READ:LTE:MEASurement<Instance>:SRS:PDYNamics:CURRent \n
		Snippet: value: ResultData = driver.lteMeas.srs.pdynamics.current.read() \n
		Return the current, average, minimum, maximum and standard deviation single-value results of the power dynamics
		measurement. The values described below are returned by FETCh and READ commands. A CALCulate command returns limit check
		results instead, one value for each result listed below. \n
			:return: structure: for return value, see the help for ResultData structure arguments."""
		return self._core.io.query_struct(f'READ:LTE:MEASurement<Instance>:SRS:PDYNamics:CURRent?', self.__class__.ResultData())

	def fetch(self) -> ResultData:
		"""FETCh:LTE:MEASurement<Instance>:SRS:PDYNamics:CURRent \n
		Snippet: value: ResultData = driver.lteMeas.srs.pdynamics.current.fetch() \n
		Return the current, average, minimum, maximum and standard deviation single-value results of the power dynamics
		measurement. The values described below are returned by FETCh and READ commands. A CALCulate command returns limit check
		results instead, one value for each result listed below. \n
			:return: structure: for return value, see the help for ResultData structure arguments."""
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:SRS:PDYNamics:CURRent?', self.__class__.ResultData())

	# noinspection PyTypeChecker
	class CalculateStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Out_Of_Tolerance: int: Out of tolerance result, i.e. the percentage of measurement intervals of the statistic count for power dynamics measurements exceeding the specified power dynamics limits.
			- 3 Off_Power_Before: float or bool: OFF power average value for the time period before the SRS symbol.
			- 4 On_Power_Rms_1: float or bool: ON power average value over the first SRS symbol.
			- 5 On_Power_Peak_1: float or bool: ON power peak value for the first SRS symbol.
			- 6 On_Power_Rms_2: float or bool: ON power average value over the second SRS symbol (NCAP returned for FDD) .
			- 7 On_Power_Peak_2: float or bool: ON power peak value for the second SRS symbol (NCAP returned for FDD) .
			- 8 Off_Power_After: float or bool: OFF power average value for the subframe after the SRS symbol."""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct.scalar_float_ext('Off_Power_Before'),
			ArgStruct.scalar_float_ext('On_Power_Rms_1'),
			ArgStruct.scalar_float_ext('On_Power_Peak_1'),
			ArgStruct.scalar_float_ext('On_Power_Rms_2'),
			ArgStruct.scalar_float_ext('On_Power_Peak_2'),
			ArgStruct.scalar_float_ext('Off_Power_After')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Out_Of_Tolerance: int = None
			self.Off_Power_Before: float or bool = None
			self.On_Power_Rms_1: float or bool = None
			self.On_Power_Peak_1: float or bool = None
			self.On_Power_Rms_2: float or bool = None
			self.On_Power_Peak_2: float or bool = None
			self.Off_Power_After: float or bool = None

	def calculate(self) -> CalculateStruct:
		"""CALCulate:LTE:MEASurement<Instance>:SRS:PDYNamics:CURRent \n
		Snippet: value: CalculateStruct = driver.lteMeas.srs.pdynamics.current.calculate() \n
		Return the current, average, minimum, maximum and standard deviation single-value results of the power dynamics
		measurement. The values described below are returned by FETCh and READ commands. A CALCulate command returns limit check
		results instead, one value for each result listed below. \n
			:return: structure: for return value, see the help for CalculateStruct structure arguments."""
		return self._core.io.query_struct(f'CALCulate:LTE:MEASurement<Instance>:SRS:PDYNamics:CURRent?', self.__class__.CalculateStruct())
