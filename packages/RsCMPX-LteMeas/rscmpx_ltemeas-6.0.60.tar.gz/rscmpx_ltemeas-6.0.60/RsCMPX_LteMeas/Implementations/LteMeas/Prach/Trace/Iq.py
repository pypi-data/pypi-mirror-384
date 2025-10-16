from typing import List

from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal.Types import DataType
from .....Internal.StructBase import StructBase
from .....Internal.ArgStruct import ArgStruct


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class IqCls:
	"""Iq commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("iq", core, parent)

	# noinspection PyTypeChecker
	class FetchStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Iphase: List[float]: Normalized I amplitude.
			- 3 Qphase: List[float]: Normalized Q amplitude."""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct('Iphase', DataType.FloatList, None, False, True, 1),
			ArgStruct('Qphase', DataType.FloatList, None, False, True, 1)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Iphase: List[float] = None
			self.Qphase: List[float] = None

	def fetch(self) -> FetchStruct:
		"""FETCh:LTE:MEASurement<Instance>:PRACh:TRACe:IQ \n
		Snippet: value: FetchStruct = driver.lteMeas.prach.trace.iq.fetch() \n
		Returns the results in the I/Q constellation diagram. There is one pair of values per modulation symbol. For preamble
		format 4, there are 139 symbols. For preamble format 0 to 3, there are 839 symbols. The results are returned in the
		following order: <Reliability>, {<IPhase>, <QPhase>}symbol 1, ..., {<IPhase>, <QPhase>}symbol n See also 'Square I/Q
		Constellation'. \n
			:return: structure: for return value, see the help for FetchStruct structure arguments."""
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:PRACh:TRACe:IQ?', self.__class__.FetchStruct())
