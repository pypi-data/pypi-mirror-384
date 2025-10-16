from ........Internal.Core import Core
from ........Internal.CommandsGroup import CommandsGroup
from ........Internal.Types import DataType
from ........Internal.StructBase import StructBase
from ........Internal.ArgStruct import ArgStruct
from ........Internal.ArgSingleList import ArgSingleList
from ........Internal.ArgSingle import ArgSingle
from ........ import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SidelinkCls:
	"""Sidelink commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("sidelink", core, parent)

	def set(self, auto: bool, no_rb_pssch: int, offset_pssch: int, offset_pscch: int, segment=repcap.Segment.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:RBALlocation:SIDelink \n
		Snippet: driver.configure.lteMeas.multiEval.listPy.segment.rbAllocation.sidelink.set(auto = False, no_rb_pssch = 1, offset_pssch = 1, offset_pscch = 1, segment = repcap.Segment.Default) \n
		Defines the sidelink resource block allocation manually for segment <no>. By default, the RB allocation is detected
		automatically. Most allowed input ranges depend on other settings, see 'Sidelink resource block allocation'. \n
			:param auto: OFF: manual definition via the other settings ON: automatic detection of RB allocation
			:param no_rb_pssch: Number of allocated RBs for the PSSCH in each measured slot
			:param offset_pssch: Offset of the first allocated PSSCH resource block
			:param offset_pscch: Offset of the first allocated PSCCH resource block
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('auto', auto, DataType.Boolean), ArgSingle('no_rb_pssch', no_rb_pssch, DataType.Integer), ArgSingle('offset_pssch', offset_pssch, DataType.Integer), ArgSingle('offset_pscch', offset_pscch, DataType.Integer))
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:RBALlocation:SIDelink {param}'.rstrip())

	# noinspection PyTypeChecker
	class SidelinkStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Auto: bool: OFF: manual definition via the other settings ON: automatic detection of RB allocation
			- 2 No_Rb_Pssch: int: Number of allocated RBs for the PSSCH in each measured slot
			- 3 Offset_Pssch: int: Offset of the first allocated PSSCH resource block
			- 4 Offset_Pscch: int: Offset of the first allocated PSCCH resource block"""
		__meta_args_list = [
			ArgStruct.scalar_bool('Auto'),
			ArgStruct.scalar_int('No_Rb_Pssch'),
			ArgStruct.scalar_int('Offset_Pssch'),
			ArgStruct.scalar_int('Offset_Pscch')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Auto: bool = None
			self.No_Rb_Pssch: int = None
			self.Offset_Pssch: int = None
			self.Offset_Pscch: int = None

	def get(self, segment=repcap.Segment.Default) -> SidelinkStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:RBALlocation:SIDelink \n
		Snippet: value: SidelinkStruct = driver.configure.lteMeas.multiEval.listPy.segment.rbAllocation.sidelink.get(segment = repcap.Segment.Default) \n
		Defines the sidelink resource block allocation manually for segment <no>. By default, the RB allocation is detected
		automatically. Most allowed input ranges depend on other settings, see 'Sidelink resource block allocation'. \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:return: structure: for return value, see the help for SidelinkStruct structure arguments."""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:RBALlocation:SIDelink?', self.__class__.SidelinkStruct())
