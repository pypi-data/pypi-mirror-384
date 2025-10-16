from ...........Internal.Core import Core
from ...........Internal.CommandsGroup import CommandsGroup
from ...........Internal.Types import DataType
from ...........Internal.StructBase import StructBase
from ...........Internal.ArgStruct import ArgStruct
from ...........Internal.ArgSingleList import ArgSingleList
from ...........Internal.ArgSingle import ArgSingle
from ...........Internal.RepeatedCapability import RepeatedCapability
from ........... import enums
from ........... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ChannelBw2ndCls:
	"""ChannelBw2nd commands group definition. 2 total commands, 1 Subgroups, 1 group commands
	Repeated Capability: SecondChannelBw, default value after init: SecondChannelBw.Bw50"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("channelBw2nd", core, parent)
		self._cmd_group.rep_cap = RepeatedCapability(self._cmd_group.group_name, 'repcap_secondChannelBw_get', 'repcap_secondChannelBw_set', repcap.SecondChannelBw.Bw50)

	def repcap_secondChannelBw_set(self, secondChannelBw: repcap.SecondChannelBw) -> None:
		"""Repeated Capability default value numeric suffix.
		This value is used, if you do not explicitely set it in the child set/get methods, or if you leave it to SecondChannelBw.Default.
		Default value after init: SecondChannelBw.Bw50"""
		self._cmd_group.set_repcap_enum_value(secondChannelBw)

	def repcap_secondChannelBw_get(self) -> repcap.SecondChannelBw:
		"""Returns the current default repeated capability for the child set/get methods"""
		# noinspection PyTypeChecker
		return self._cmd_group.get_repcap_enum_value()

	@property
	def channelBw3rd(self):
		"""channelBw3rd commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_channelBw3rd'):
			from .ChannelBw3rd import ChannelBw3rdCls
			self._channelBw3rd = ChannelBw3rdCls(self._core, self._cmd_group)
		return self._channelBw3rd

	def set(self, enable: bool, frequency_start: float, frequency_end: float, level: float, rbw: enums.Rbw, limit=repcap.Limit.Default, firstChannelBw=repcap.FirstChannelBw.Default, secondChannelBw=repcap.SecondChannelBw.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:LIMit<nr>:CAGGregation:CBANdwidth<Band1>:CBANdwidth<Band2> \n
		Snippet: driver.configure.lteMeas.multiEval.limit.seMask.limit.carrierAggregation.channelBw1st.channelBw2nd.set(enable = False, frequency_start = 1.0, frequency_end = 1.0, level = 1.0, rbw = enums.Rbw.K030, limit = repcap.Limit.Default, firstChannelBw = repcap.FirstChannelBw.Default, secondChannelBw = repcap.SecondChannelBw.Default) \n
		Defines general requirements for the emission mask area <no>. The activation state, the area borders, an upper limit and
		the resolution bandwidth must be specified. The settings are defined separately for each channel bandwidth combination,
		for two aggregated carriers.
			Table Header:  \n
			- <Band1> / 50 / 100 / 150 / 100 / 150 / 200 / 200 / 150 / 200 / 200
			- <Band2> / 50 / 50 / 50 / 100 / 100 / 50 / 100 / 150 / 150 / 200 \n
			:param enable: OFF: Disables the check of these requirements. ON: Enables the check of these requirements.
			:param frequency_start: Start frequency of the area, relative to the edges of the aggregated channel bandwidth.
			:param frequency_end: Stop frequency of the area, relative to the edges of the aggregated channel bandwidth.
			:param level: Upper limit for the area
			:param rbw: Resolution bandwidth to be used for the area. K030: 30 kHz K100: 100 kHz M1: 1 MHz
			:param limit: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Limit')
			:param firstChannelBw: optional repeated capability selector. Default value: Bw50 (settable in the interface 'ChannelBw1st')
			:param secondChannelBw: optional repeated capability selector. Default value: Bw50 (settable in the interface 'ChannelBw2nd')
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('enable', enable, DataType.Boolean), ArgSingle('frequency_start', frequency_start, DataType.Float), ArgSingle('frequency_end', frequency_end, DataType.Float), ArgSingle('level', level, DataType.Float), ArgSingle('rbw', rbw, DataType.Enum, enums.Rbw))
		limit_cmd_val = self._cmd_group.get_repcap_cmd_value(limit, repcap.Limit)
		firstChannelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(firstChannelBw, repcap.FirstChannelBw)
		secondChannelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(secondChannelBw, repcap.SecondChannelBw)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:LIMit{limit_cmd_val}:CAGGregation:CBANdwidth{firstChannelBw_cmd_val}:CBANdwidth{secondChannelBw_cmd_val} {param}'.rstrip())

	# noinspection PyTypeChecker
	class ChannelBw2ndStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Enable: bool: OFF: Disables the check of these requirements. ON: Enables the check of these requirements.
			- 2 Frequency_Start: float: Start frequency of the area, relative to the edges of the aggregated channel bandwidth.
			- 3 Frequency_End: float: Stop frequency of the area, relative to the edges of the aggregated channel bandwidth.
			- 4 Level: float: Upper limit for the area
			- 5 Rbw: enums.Rbw: Resolution bandwidth to be used for the area. K030: 30 kHz K100: 100 kHz M1: 1 MHz"""
		__meta_args_list = [
			ArgStruct.scalar_bool('Enable'),
			ArgStruct.scalar_float('Frequency_Start'),
			ArgStruct.scalar_float('Frequency_End'),
			ArgStruct.scalar_float('Level'),
			ArgStruct.scalar_enum('Rbw', enums.Rbw)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Enable: bool = None
			self.Frequency_Start: float = None
			self.Frequency_End: float = None
			self.Level: float = None
			self.Rbw: enums.Rbw = None

	def get(self, limit=repcap.Limit.Default, firstChannelBw=repcap.FirstChannelBw.Default, secondChannelBw=repcap.SecondChannelBw.Default) -> ChannelBw2ndStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:LIMit<nr>:CAGGregation:CBANdwidth<Band1>:CBANdwidth<Band2> \n
		Snippet: value: ChannelBw2ndStruct = driver.configure.lteMeas.multiEval.limit.seMask.limit.carrierAggregation.channelBw1st.channelBw2nd.get(limit = repcap.Limit.Default, firstChannelBw = repcap.FirstChannelBw.Default, secondChannelBw = repcap.SecondChannelBw.Default) \n
		Defines general requirements for the emission mask area <no>. The activation state, the area borders, an upper limit and
		the resolution bandwidth must be specified. The settings are defined separately for each channel bandwidth combination,
		for two aggregated carriers.
			Table Header:  \n
			- <Band1> / 50 / 100 / 150 / 100 / 150 / 200 / 200 / 150 / 200 / 200
			- <Band2> / 50 / 50 / 50 / 100 / 100 / 50 / 100 / 150 / 150 / 200 \n
			:param limit: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Limit')
			:param firstChannelBw: optional repeated capability selector. Default value: Bw50 (settable in the interface 'ChannelBw1st')
			:param secondChannelBw: optional repeated capability selector. Default value: Bw50 (settable in the interface 'ChannelBw2nd')
			:return: structure: for return value, see the help for ChannelBw2ndStruct structure arguments."""
		limit_cmd_val = self._cmd_group.get_repcap_cmd_value(limit, repcap.Limit)
		firstChannelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(firstChannelBw, repcap.FirstChannelBw)
		secondChannelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(secondChannelBw, repcap.SecondChannelBw)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:LIMit{limit_cmd_val}:CAGGregation:CBANdwidth{firstChannelBw_cmd_val}:CBANdwidth{secondChannelBw_cmd_val}?', self.__class__.ChannelBw2ndStruct())

	def clone(self) -> 'ChannelBw2ndCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = ChannelBw2ndCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
