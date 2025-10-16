from typing import List

from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal.Types import DataType
from ......Internal.StructBase import StructBase
from ......Internal.ArgStruct import ArgStruct
from ...... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class MaximumCls:
	"""Maximum commands group definition. 5 total commands, 1 Subgroups, 3 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("maximum", core, parent)

	@property
	def nref(self):
		"""nref commands group. 0 Sub-classes, 2 commands."""
		if not hasattr(self, '_nref'):
			from .Nref import NrefCls
			self._nref = NrefCls(self._core, self._cmd_group)
		return self._nref

	# noinspection PyTypeChecker
	class ResultData(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Low: List[float]: EVM value for low EVM window position
			- 3 High: List[float]: EVM value for high EVM window position"""
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
		"""READ:LTE:MEASurement<Instance>:MEValuation:EVMagnitude:MAXimum \n
		Snippet: value: ResultData = driver.lteMeas.multiEval.evMagnitude.maximum.read() \n
		Returns the values of the EVM RMS diagrams for the SC-FDMA symbols in the measured slot. The results of the current,
		average and maximum diagrams can be retrieved. There is one pair of EVM values per SC-FDMA symbol, returned in the
		following order: <Reliability>, {<Low>, <High>}symbol 0, {<Low>, <High>}symbol 1, ... See also 'Square EVM'. \n
			:return: structure: for return value, see the help for ResultData structure arguments."""
		return self._core.io.query_struct(f'READ:LTE:MEASurement<Instance>:MEValuation:EVMagnitude:MAXimum?', self.__class__.ResultData())

	def fetch(self) -> ResultData:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:EVMagnitude:MAXimum \n
		Snippet: value: ResultData = driver.lteMeas.multiEval.evMagnitude.maximum.fetch() \n
		Returns the values of the EVM RMS diagrams for the SC-FDMA symbols in the measured slot. The results of the current,
		average and maximum diagrams can be retrieved. There is one pair of EVM values per SC-FDMA symbol, returned in the
		following order: <Reliability>, {<Low>, <High>}symbol 0, {<Low>, <High>}symbol 1, ... See also 'Square EVM'. \n
			:return: structure: for return value, see the help for ResultData structure arguments."""
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:EVMagnitude:MAXimum?', self.__class__.ResultData())

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
		"""CALCulate:LTE:MEASurement<Instance>:MEValuation:EVMagnitude:MAXimum \n
		Snippet: value: CalculateStruct = driver.lteMeas.multiEval.evMagnitude.maximum.calculate() \n
		No command help available \n
			:return: structure: for return value, see the help for CalculateStruct structure arguments."""
		return self._core.io.query_struct(f'CALCulate:LTE:MEASurement<Instance>:MEValuation:EVMagnitude:MAXimum?', self.__class__.CalculateStruct())

	def clone(self) -> 'MaximumCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = MaximumCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
