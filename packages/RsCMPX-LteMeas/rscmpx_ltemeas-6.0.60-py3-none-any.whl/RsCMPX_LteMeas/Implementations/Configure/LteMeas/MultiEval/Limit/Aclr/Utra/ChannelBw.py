from ........Internal.Core import Core
from ........Internal.CommandsGroup import CommandsGroup
from ........Internal.Types import DataType
from ........Internal.StructBase import StructBase
from ........Internal.ArgStruct import ArgStruct
from ........Internal.ArgSingleList import ArgSingleList
from ........Internal.ArgSingle import ArgSingle
from ........Internal.RepeatedCapability import RepeatedCapability
from ........ import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ChannelBwCls:
	"""ChannelBw commands group definition. 1 total commands, 0 Subgroups, 1 group commands
	Repeated Capability: ChannelBw, default value after init: ChannelBw.Bw14"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("channelBw", core, parent)
		self._cmd_group.rep_cap = RepeatedCapability(self._cmd_group.group_name, 'repcap_channelBw_get', 'repcap_channelBw_set', repcap.ChannelBw.Bw14)

	def repcap_channelBw_set(self, channelBw: repcap.ChannelBw) -> None:
		"""Repeated Capability default value numeric suffix.
		This value is used, if you do not explicitely set it in the child set/get methods, or if you leave it to ChannelBw.Default.
		Default value after init: ChannelBw.Bw14"""
		self._cmd_group.set_repcap_enum_value(channelBw)

	def repcap_channelBw_get(self) -> repcap.ChannelBw:
		"""Returns the current default repeated capability for the child set/get methods"""
		# noinspection PyTypeChecker
		return self._cmd_group.get_repcap_enum_value()

	def set(self, relative_level: float or bool, absolute_level: float or bool, utraAdjChannel=repcap.UtraAdjChannel.Default, channelBw=repcap.ChannelBw.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:ACLR:UTRA<nr>:CBANdwidth<Band> \n
		Snippet: driver.configure.lteMeas.multiEval.limit.aclr.utra.channelBw.set(relative_level = 1.0, absolute_level = 1.0, utraAdjChannel = repcap.UtraAdjChannel.Default, channelBw = repcap.ChannelBw.Default) \n
		Defines relative and absolute limits for the ACLR measured in the first or second adjacent UTRA channel, depending on
		<no>. The settings are defined separately for each channel bandwidth. \n
			:param relative_level: (float or boolean) No help available
			:param absolute_level: (float or boolean) No help available
			:param utraAdjChannel: optional repeated capability selector. Default value: Ch1 (settable in the interface 'Utra')
			:param channelBw: optional repeated capability selector. Default value: Bw14 (settable in the interface 'ChannelBw')
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('relative_level', relative_level, DataType.FloatExt), ArgSingle('absolute_level', absolute_level, DataType.FloatExt))
		utraAdjChannel_cmd_val = self._cmd_group.get_repcap_cmd_value(utraAdjChannel, repcap.UtraAdjChannel)
		channelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(channelBw, repcap.ChannelBw)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:ACLR:UTRA{utraAdjChannel_cmd_val}:CBANdwidth{channelBw_cmd_val} {param}'.rstrip())

	# noinspection PyTypeChecker
	class ChannelBwStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Relative_Level: float or bool: No parameter help available
			- 2 Absolute_Level: float or bool: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_float_ext('Relative_Level'),
			ArgStruct.scalar_float_ext('Absolute_Level')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Relative_Level: float or bool = None
			self.Absolute_Level: float or bool = None

	def get(self, utraAdjChannel=repcap.UtraAdjChannel.Default, channelBw=repcap.ChannelBw.Default) -> ChannelBwStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:ACLR:UTRA<nr>:CBANdwidth<Band> \n
		Snippet: value: ChannelBwStruct = driver.configure.lteMeas.multiEval.limit.aclr.utra.channelBw.get(utraAdjChannel = repcap.UtraAdjChannel.Default, channelBw = repcap.ChannelBw.Default) \n
		Defines relative and absolute limits for the ACLR measured in the first or second adjacent UTRA channel, depending on
		<no>. The settings are defined separately for each channel bandwidth. \n
			:param utraAdjChannel: optional repeated capability selector. Default value: Ch1 (settable in the interface 'Utra')
			:param channelBw: optional repeated capability selector. Default value: Bw14 (settable in the interface 'ChannelBw')
			:return: structure: for return value, see the help for ChannelBwStruct structure arguments."""
		utraAdjChannel_cmd_val = self._cmd_group.get_repcap_cmd_value(utraAdjChannel, repcap.UtraAdjChannel)
		channelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(channelBw, repcap.ChannelBw)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:ACLR:UTRA{utraAdjChannel_cmd_val}:CBANdwidth{channelBw_cmd_val}?', self.__class__.ChannelBwStruct())

	def clone(self) -> 'ChannelBwCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = ChannelBwCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
