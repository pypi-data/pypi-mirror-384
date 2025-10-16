from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.Types import DataType
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct
from .......Internal.ArgSingleList import ArgSingleList
from .......Internal.ArgSingle import ArgSingle
from .......Internal.RepeatedCapability import RepeatedCapability
from ....... import repcap


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

	def set(self, enable: bool, on_power_upper: float, on_power_lower: float, off_power_upper: float, channelBw=repcap.ChannelBw.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:PDYNamics:CBANdwidth<Band> \n
		Snippet: driver.configure.lteMeas.multiEval.limit.pdynamics.channelBw.set(enable = False, on_power_upper = 1.0, on_power_lower = 1.0, off_power_upper = 1.0, channelBw = repcap.ChannelBw.Default) \n
		Defines limits for the ON power and OFF power determined with the power dynamics measurement. Separate limits can be
		defined for each channel bandwidth. \n
			:param enable: OFF: disables the limit check ON: enables the limit check
			:param on_power_upper: Upper limit for the 'ON power'
			:param on_power_lower: Lower limit for the 'ON power'
			:param off_power_upper: Upper limit for the 'OFF power' and the 'SRS OFF' power
			:param channelBw: optional repeated capability selector. Default value: Bw14 (settable in the interface 'ChannelBw')
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('enable', enable, DataType.Boolean), ArgSingle('on_power_upper', on_power_upper, DataType.Float), ArgSingle('on_power_lower', on_power_lower, DataType.Float), ArgSingle('off_power_upper', off_power_upper, DataType.Float))
		channelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(channelBw, repcap.ChannelBw)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:PDYNamics:CBANdwidth{channelBw_cmd_val} {param}'.rstrip())

	# noinspection PyTypeChecker
	class ChannelBwStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Enable: bool: OFF: disables the limit check ON: enables the limit check
			- 2 On_Power_Upper: float: Upper limit for the 'ON power'
			- 3 On_Power_Lower: float: Lower limit for the 'ON power'
			- 4 Off_Power_Upper: float: Upper limit for the 'OFF power' and the 'SRS OFF' power"""
		__meta_args_list = [
			ArgStruct.scalar_bool('Enable'),
			ArgStruct.scalar_float('On_Power_Upper'),
			ArgStruct.scalar_float('On_Power_Lower'),
			ArgStruct.scalar_float('Off_Power_Upper')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Enable: bool = None
			self.On_Power_Upper: float = None
			self.On_Power_Lower: float = None
			self.Off_Power_Upper: float = None

	def get(self, channelBw=repcap.ChannelBw.Default) -> ChannelBwStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:PDYNamics:CBANdwidth<Band> \n
		Snippet: value: ChannelBwStruct = driver.configure.lteMeas.multiEval.limit.pdynamics.channelBw.get(channelBw = repcap.ChannelBw.Default) \n
		Defines limits for the ON power and OFF power determined with the power dynamics measurement. Separate limits can be
		defined for each channel bandwidth. \n
			:param channelBw: optional repeated capability selector. Default value: Bw14 (settable in the interface 'ChannelBw')
			:return: structure: for return value, see the help for ChannelBwStruct structure arguments."""
		channelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(channelBw, repcap.ChannelBw)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:PDYNamics:CBANdwidth{channelBw_cmd_val}?', self.__class__.ChannelBwStruct())

	def clone(self) -> 'ChannelBwCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = ChannelBwCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
