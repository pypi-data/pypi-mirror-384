from ........Internal.Core import Core
from ........Internal.CommandsGroup import CommandsGroup
from ........Internal.Types import DataType
from ........Internal.StructBase import StructBase
from ........Internal.ArgStruct import ArgStruct
from ........Internal.ArgSingleList import ArgSingleList
from ........Internal.ArgSingle import ArgSingle
from ........ import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class RbAllocationCls:
	"""RbAllocation commands group definition. 2 total commands, 1 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("rbAllocation", core, parent)

	@property
	def sidelink(self):
		"""sidelink commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_sidelink'):
			from .Sidelink import SidelinkCls
			self._sidelink = SidelinkCls(self._core, self._cmd_group)
		return self._sidelink

	def set(self, auto: bool, no_rb: int, offset: int, segment=repcap.Segment.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:RBALlocation \n
		Snippet: driver.configure.lteMeas.multiEval.listPy.segment.rbAllocation.set(auto = False, no_rb = 1, offset = 1, segment = repcap.Segment.Default) \n
		Defines the uplink resource block allocation manually for segment <no>. By default, the RB allocation is detected
		automatically. \n
			:param auto: OFF: manual definition via NoRB and Offset ON: automatic detection of RB allocation
			:param no_rb: Number of allocated resource blocks in each measured slot
			:param offset: Offset of first allocated resource block from edge of allocated UL transmission bandwidth
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('auto', auto, DataType.Boolean), ArgSingle('no_rb', no_rb, DataType.Integer), ArgSingle('offset', offset, DataType.Integer))
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:RBALlocation {param}'.rstrip())

	# noinspection PyTypeChecker
	class RbAllocationStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Auto: bool: OFF: manual definition via NoRB and Offset ON: automatic detection of RB allocation
			- 2 No_Rb: int: Number of allocated resource blocks in each measured slot
			- 3 Offset: int: Offset of first allocated resource block from edge of allocated UL transmission bandwidth"""
		__meta_args_list = [
			ArgStruct.scalar_bool('Auto'),
			ArgStruct.scalar_int('No_Rb'),
			ArgStruct.scalar_int('Offset')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Auto: bool = None
			self.No_Rb: int = None
			self.Offset: int = None

	def get(self, segment=repcap.Segment.Default) -> RbAllocationStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:RBALlocation \n
		Snippet: value: RbAllocationStruct = driver.configure.lteMeas.multiEval.listPy.segment.rbAllocation.get(segment = repcap.Segment.Default) \n
		Defines the uplink resource block allocation manually for segment <no>. By default, the RB allocation is detected
		automatically. \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:return: structure: for return value, see the help for RbAllocationStruct structure arguments."""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:RBALlocation?', self.__class__.RbAllocationStruct())

	def clone(self) -> 'RbAllocationCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = RbAllocationCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
