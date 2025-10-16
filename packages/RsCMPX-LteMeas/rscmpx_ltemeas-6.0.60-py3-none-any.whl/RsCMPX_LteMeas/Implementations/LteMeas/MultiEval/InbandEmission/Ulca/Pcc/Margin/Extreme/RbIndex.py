from .........Internal.Core import Core
from .........Internal.CommandsGroup import CommandsGroup
from .........Internal.StructBase import StructBase
from .........Internal.ArgStruct import ArgStruct


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class RbIndexCls:
	"""RbIndex commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("rbIndex", core, parent)

	# noinspection PyTypeChecker
	class FetchStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: No parameter help available
			- 2 Out_Of_Tolerance: int: No parameter help available
			- 3 Rb_Index: int: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct.scalar_int('Rb_Index')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Out_Of_Tolerance: int = None
			self.Rb_Index: int = None

	def fetch(self) -> FetchStruct:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:IEMission:ULCA[:PCC]:MARGin:EXTReme:RBINdex \n
		Snippet: value: FetchStruct = driver.lteMeas.multiEval.inbandEmission.ulca.pcc.margin.extreme.rbIndex.fetch() \n
		No command help available \n
			:return: structure: for return value, see the help for FetchStruct structure arguments."""
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:IEMission:ULCA:PCC:MARGin:EXTReme:RBINdex?', self.__class__.FetchStruct())
