from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.Types import DataType
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct
from .......Internal.ArgSingleList import ArgSingleList
from .......Internal.ArgSingle import ArgSingle
from .......Internal.RepeatedCapability import RepeatedCapability
from ....... import enums
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SccCls:
	"""Scc commands group definition. 1 total commands, 0 Subgroups, 1 group commands
	Repeated Capability: SecondaryCC, default value after init: SecondaryCC.CC1"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("scc", core, parent)
		self._cmd_group.rep_cap = RepeatedCapability(self._cmd_group.group_name, 'repcap_secondaryCC_get', 'repcap_secondaryCC_set', repcap.SecondaryCC.CC1)

	def repcap_secondaryCC_set(self, secondaryCC: repcap.SecondaryCC) -> None:
		"""Repeated Capability default value numeric suffix.
		This value is used, if you do not explicitely set it in the child set/get methods, or if you leave it to SecondaryCC.Default.
		Default value after init: SecondaryCC.CC1"""
		self._cmd_group.set_repcap_enum_value(secondaryCC)

	def repcap_secondaryCC_get(self) -> repcap.SecondaryCC:
		"""Returns the current default repeated capability for the child set/get methods"""
		# noinspection PyTypeChecker
		return self._cmd_group.get_repcap_enum_value()

	def set(self, frequency: float, ch_bandwidth: enums.ChannelBandwidth, segment=repcap.Segment.Default, secondaryCC=repcap.SecondaryCC.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:SCC<c> \n
		Snippet: driver.configure.lteMeas.multiEval.listPy.segment.scc.set(frequency = 1.0, ch_bandwidth = enums.ChannelBandwidth.B014, segment = repcap.Segment.Default, secondaryCC = repcap.SecondaryCC.Default) \n
		No command help available \n
			:param frequency: No help available
			:param ch_bandwidth: No help available
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:param secondaryCC: optional repeated capability selector. Default value: CC1 (settable in the interface 'Scc')
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('frequency', frequency, DataType.Float), ArgSingle('ch_bandwidth', ch_bandwidth, DataType.Enum, enums.ChannelBandwidth))
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		secondaryCC_cmd_val = self._cmd_group.get_repcap_cmd_value(secondaryCC, repcap.SecondaryCC)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:SCC{secondaryCC_cmd_val} {param}'.rstrip())

	# noinspection PyTypeChecker
	class SccStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Frequency: float: No parameter help available
			- 2 Ch_Bandwidth: enums.ChannelBandwidth: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_float('Frequency'),
			ArgStruct.scalar_enum('Ch_Bandwidth', enums.ChannelBandwidth)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Frequency: float = None
			self.Ch_Bandwidth: enums.ChannelBandwidth = None

	def get(self, segment=repcap.Segment.Default, secondaryCC=repcap.SecondaryCC.Default) -> SccStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:SCC<c> \n
		Snippet: value: SccStruct = driver.configure.lteMeas.multiEval.listPy.segment.scc.get(segment = repcap.Segment.Default, secondaryCC = repcap.SecondaryCC.Default) \n
		No command help available \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:param secondaryCC: optional repeated capability selector. Default value: CC1 (settable in the interface 'Scc')
			:return: structure: for return value, see the help for SccStruct structure arguments."""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		secondaryCC_cmd_val = self._cmd_group.get_repcap_cmd_value(secondaryCC, repcap.SecondaryCC)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:SCC{secondaryCC_cmd_val}?', self.__class__.SccStruct())

	def clone(self) -> 'SccCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = SccCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
