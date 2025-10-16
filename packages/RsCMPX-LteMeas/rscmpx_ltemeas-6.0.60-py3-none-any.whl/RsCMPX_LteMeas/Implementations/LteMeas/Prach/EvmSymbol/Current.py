from typing import List

from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal.Types import DataType
from .....Internal.StructBase import StructBase
from .....Internal.ArgStruct import ArgStruct
from ..... import enums


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
			- 2 Low: List[float]: EVM value for low EVM window position.
			- 3 High: List[float]: EVM value for high EVM window position."""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct('Low', DataType.FloatList, None, False, True, 1),
			ArgStruct('High', DataType.FloatList, None, False, True, 1)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Low: List[float] = None
			self.High: List[float] = None

	def read(self) -> ResultData:
		"""READ:LTE:MEASurement<Instance>:PRACh:EVMSymbol:CURRent \n
		Snippet: value: ResultData = driver.lteMeas.prach.evmSymbol.current.read() \n
		Returns the values of the EVM RMS diagrams for the OFDM symbols in the measured preamble. The results of the current,
		average and maximum diagrams can be retrieved. There is one pair of EVM values per OFDM symbol, returned in the following
		order: <Reliability>, {<Low>, <High>}symbol 0, {<Low>, <High>}symbol 1 If the preamble contains only one symbol, NCAPs
		are returned for the remaining symbol. See also 'Square EVM vs Symbol'. \n
			:return: structure: for return value, see the help for ResultData structure arguments."""
		return self._core.io.query_struct(f'READ:LTE:MEASurement<Instance>:PRACh:EVMSymbol:CURRent?', self.__class__.ResultData())

	def fetch(self) -> ResultData:
		"""FETCh:LTE:MEASurement<Instance>:PRACh:EVMSymbol:CURRent \n
		Snippet: value: ResultData = driver.lteMeas.prach.evmSymbol.current.fetch() \n
		Returns the values of the EVM RMS diagrams for the OFDM symbols in the measured preamble. The results of the current,
		average and maximum diagrams can be retrieved. There is one pair of EVM values per OFDM symbol, returned in the following
		order: <Reliability>, {<Low>, <High>}symbol 0, {<Low>, <High>}symbol 1 If the preamble contains only one symbol, NCAPs
		are returned for the remaining symbol. See also 'Square EVM vs Symbol'. \n
			:return: structure: for return value, see the help for ResultData structure arguments."""
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:PRACh:EVMSymbol:CURRent?', self.__class__.ResultData())

	# noinspection PyTypeChecker
	class CalculateStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: No parameter help available
			- 2 Low: List[enums.ResultStatus2]: No parameter help available
			- 3 High: List[enums.ResultStatus2]: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct('Low', DataType.EnumList, enums.ResultStatus2, False, True, 1),
			ArgStruct('High', DataType.EnumList, enums.ResultStatus2, False, True, 1)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Low: List[enums.ResultStatus2] = None
			self.High: List[enums.ResultStatus2] = None

	def calculate(self) -> CalculateStruct:
		"""CALCulate:LTE:MEASurement<Instance>:PRACh:EVMSymbol:CURRent \n
		Snippet: value: CalculateStruct = driver.lteMeas.prach.evmSymbol.current.calculate() \n
		No command help available \n
			:return: structure: for return value, see the help for CalculateStruct structure arguments."""
		return self._core.io.query_struct(f'CALCulate:LTE:MEASurement<Instance>:PRACh:EVMSymbol:CURRent?', self.__class__.CalculateStruct())
