from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal.StructBase import StructBase
from ......Internal.ArgStruct import ArgStruct


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class NrefCls:
	"""Nref commands group definition. 2 total commands, 0 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("nref", core, parent)

	# noinspection PyTypeChecker
	class ResultData(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: No parameter help available
			- 2 Sym_1_L: float: No parameter help available
			- 3 Sym_1_H: float: No parameter help available
			- 4 Sym_2_L: float: No parameter help available
			- 5 Sym_2_H: float: No parameter help available
			- 6 Sym_3_L: float: No parameter help available
			- 7 Sym_3_H: float: No parameter help available
			- 8 Sym_5_L: float: No parameter help available
			- 9 Sym_5_H: float: No parameter help available
			- 10 Sym_6_L: float: No parameter help available
			- 11 Sym_6_H: float: No parameter help available
			- 12 Sym_7_L: float: No parameter help available
			- 13 Sym_7_H: float: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_float('Sym_1_L'),
			ArgStruct.scalar_float('Sym_1_H'),
			ArgStruct.scalar_float('Sym_2_L'),
			ArgStruct.scalar_float('Sym_2_H'),
			ArgStruct.scalar_float('Sym_3_L'),
			ArgStruct.scalar_float('Sym_3_H'),
			ArgStruct.scalar_float('Sym_5_L'),
			ArgStruct.scalar_float('Sym_5_H'),
			ArgStruct.scalar_float('Sym_6_L'),
			ArgStruct.scalar_float('Sym_6_H'),
			ArgStruct.scalar_float('Sym_7_L'),
			ArgStruct.scalar_float('Sym_7_H')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Sym_1_L: float = None
			self.Sym_1_H: float = None
			self.Sym_2_L: float = None
			self.Sym_2_H: float = None
			self.Sym_3_L: float = None
			self.Sym_3_H: float = None
			self.Sym_5_L: float = None
			self.Sym_5_H: float = None
			self.Sym_6_L: float = None
			self.Sym_6_H: float = None
			self.Sym_7_L: float = None
			self.Sym_7_H: float = None

	def read(self) -> ResultData:
		"""READ:LTE:MEASurement<Instance>:MEValuation:EVMagnitude:AVERage:NREF \n
		Snippet: value: ResultData = driver.lteMeas.multiEval.evMagnitude.average.nref.read() \n
		No command help available \n
			:return: structure: for return value, see the help for ResultData structure arguments."""
		return self._core.io.query_struct(f'READ:LTE:MEASurement<Instance>:MEValuation:EVMagnitude:AVERage:NREF?', self.__class__.ResultData())

	def fetch(self) -> ResultData:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:EVMagnitude:AVERage:NREF \n
		Snippet: value: ResultData = driver.lteMeas.multiEval.evMagnitude.average.nref.fetch() \n
		No command help available \n
			:return: structure: for return value, see the help for ResultData structure arguments."""
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:EVMagnitude:AVERage:NREF?', self.__class__.ResultData())
