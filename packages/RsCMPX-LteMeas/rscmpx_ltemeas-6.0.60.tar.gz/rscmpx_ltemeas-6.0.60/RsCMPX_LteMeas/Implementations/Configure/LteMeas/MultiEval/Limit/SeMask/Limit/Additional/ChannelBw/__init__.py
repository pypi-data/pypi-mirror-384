from ..........Internal.Core import Core
from ..........Internal.CommandsGroup import CommandsGroup
from ..........Internal.Types import DataType
from ..........Internal.StructBase import StructBase
from ..........Internal.ArgStruct import ArgStruct
from ..........Internal.ArgSingleList import ArgSingleList
from ..........Internal.ArgSingle import ArgSingle
from ..........Internal.RepeatedCapability import RepeatedCapability
from .......... import enums
from .......... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ChannelBwCls:
	"""ChannelBw commands group definition. 2 total commands, 1 Subgroups, 1 group commands
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

	@property
	def sidelink(self):
		"""sidelink commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_sidelink'):
			from .Sidelink import SidelinkCls
			self._sidelink = SidelinkCls(self._core, self._cmd_group)
		return self._sidelink

	def set(self, enable: bool, frequency_start: float, frequency_end: float, level: float, rbw: enums.RbwExtended, limit=repcap.Limit.Default, table=repcap.Table.Default, channelBw=repcap.ChannelBw.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:LIMit<nr>:ADDitional<Table>:CBANdwidth<Band> \n
		Snippet: driver.configure.lteMeas.multiEval.limit.seMask.limit.additional.channelBw.set(enable = False, frequency_start = 1.0, frequency_end = 1.0, level = 1.0, rbw = enums.RbwExtended.K030, limit = repcap.Limit.Default, table = repcap.Table.Default, channelBw = repcap.ChannelBw.Default) \n
		Defines additional requirements for the emission mask area <no>, for uplink measurements. The activation state, the area
		borders, an upper limit and the resolution bandwidth must be specified. The emission mask applies to the channel
		bandwidth <Band>. Several tables of additional requirements are available. \n
			:param enable: OFF: Disables the check of these requirements. ON: Enables the check of these requirements.
			:param frequency_start: Lower border of the area, relative to the edges of the channel bandwidth.
			:param frequency_end: Upper border of the area, relative to the edges of the channel bandwidth.
			:param level: Upper limit for the area
			:param rbw: Resolution bandwidth to be used for the area. Only a subset of the values is allowed, depending on Table and Band, see table below. K030: 30 kHz K050: 50 kHz K100: 100 kHz K150: 150 kHz K200: 200 kHz M1: 1 MHz
			:param limit: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Limit')
			:param table: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Additional')
			:param channelBw: optional repeated capability selector. Default value: Bw14 (settable in the interface 'ChannelBw')
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('enable', enable, DataType.Boolean), ArgSingle('frequency_start', frequency_start, DataType.Float), ArgSingle('frequency_end', frequency_end, DataType.Float), ArgSingle('level', level, DataType.Float), ArgSingle('rbw', rbw, DataType.Enum, enums.RbwExtended))
		limit_cmd_val = self._cmd_group.get_repcap_cmd_value(limit, repcap.Limit)
		table_cmd_val = self._cmd_group.get_repcap_cmd_value(table, repcap.Table)
		channelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(channelBw, repcap.ChannelBw)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:LIMit{limit_cmd_val}:ADDitional{table_cmd_val}:CBANdwidth{channelBw_cmd_val} {param}'.rstrip())

	# noinspection PyTypeChecker
	class ChannelBwStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Enable: bool: OFF: Disables the check of these requirements. ON: Enables the check of these requirements.
			- 2 Frequency_Start: float: Lower border of the area, relative to the edges of the channel bandwidth.
			- 3 Frequency_End: float: Upper border of the area, relative to the edges of the channel bandwidth.
			- 4 Level: float: Upper limit for the area
			- 5 Rbw: enums.RbwExtended: Resolution bandwidth to be used for the area. Only a subset of the values is allowed, depending on Table and Band, see table below. K030: 30 kHz K050: 50 kHz K100: 100 kHz K150: 150 kHz K200: 200 kHz M1: 1 MHz"""
		__meta_args_list = [
			ArgStruct.scalar_bool('Enable'),
			ArgStruct.scalar_float('Frequency_Start'),
			ArgStruct.scalar_float('Frequency_End'),
			ArgStruct.scalar_float('Level'),
			ArgStruct.scalar_enum('Rbw', enums.RbwExtended)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Enable: bool = None
			self.Frequency_Start: float = None
			self.Frequency_End: float = None
			self.Level: float = None
			self.Rbw: enums.RbwExtended = None

	def get(self, limit=repcap.Limit.Default, table=repcap.Table.Default, channelBw=repcap.ChannelBw.Default) -> ChannelBwStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:LIMit<nr>:ADDitional<Table>:CBANdwidth<Band> \n
		Snippet: value: ChannelBwStruct = driver.configure.lteMeas.multiEval.limit.seMask.limit.additional.channelBw.get(limit = repcap.Limit.Default, table = repcap.Table.Default, channelBw = repcap.ChannelBw.Default) \n
		Defines additional requirements for the emission mask area <no>, for uplink measurements. The activation state, the area
		borders, an upper limit and the resolution bandwidth must be specified. The emission mask applies to the channel
		bandwidth <Band>. Several tables of additional requirements are available. \n
			:param limit: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Limit')
			:param table: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Additional')
			:param channelBw: optional repeated capability selector. Default value: Bw14 (settable in the interface 'ChannelBw')
			:return: structure: for return value, see the help for ChannelBwStruct structure arguments."""
		limit_cmd_val = self._cmd_group.get_repcap_cmd_value(limit, repcap.Limit)
		table_cmd_val = self._cmd_group.get_repcap_cmd_value(table, repcap.Table)
		channelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(channelBw, repcap.ChannelBw)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:LIMit{limit_cmd_val}:ADDitional{table_cmd_val}:CBANdwidth{channelBw_cmd_val}?', self.__class__.ChannelBwStruct())

	def clone(self) -> 'ChannelBwCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = ChannelBwCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
