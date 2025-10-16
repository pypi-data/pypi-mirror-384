from ..........Internal.Core import Core
from ..........Internal.CommandsGroup import CommandsGroup
from ..........Internal.StructBase import StructBase
from ..........Internal.ArgStruct import ArgStruct
from .......... import enums
from .......... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SidelinkCls:
	"""Sidelink commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("sidelink", core, parent)

	# noinspection PyTypeChecker
	class SidelinkStruct(StructBase):
		"""Structure for setting input parameters. Fields: \n
			- Enable: bool: OFF: Disables the check of these requirements. ON: Enables the check of these requirements.
			- Frequency_Start: float: Lower border of the area, relative to the edges of the channel bandwidth.
			- Frequency_End: float: Upper border of the area, relative to the edges of the channel bandwidth.
			- Level: float: Upper limit at FrequencyStart
			- Slope: float: Slope for the upper limit within the area
			- Rbw: enums.Rbw: Resolution bandwidth to be used for the area. K030: 30 kHz K100: 100 kHz M1: 1 MHz"""
		__meta_args_list = [
			ArgStruct.scalar_bool('Enable'),
			ArgStruct.scalar_float('Frequency_Start'),
			ArgStruct.scalar_float('Frequency_End'),
			ArgStruct.scalar_float('Level'),
			ArgStruct.scalar_float('Slope'),
			ArgStruct.scalar_enum('Rbw', enums.Rbw)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Enable: bool=None
			self.Frequency_Start: float=None
			self.Frequency_End: float=None
			self.Level: float=None
			self.Slope: float=None
			self.Rbw: enums.Rbw=None

	def set(self, structure: SidelinkStruct, limit=repcap.Limit.Default, table=repcap.Table.Default, channelBw=repcap.ChannelBw.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:LIMit<nr>:ADDitional<Table>:CBANdwidth<Band>:SIDelink \n
		Snippet with structure: \n
		structure = driver.configure.lteMeas.multiEval.limit.seMask.limit.additional.channelBw.sidelink.SidelinkStruct() \n
		structure.Enable: bool = False \n
		structure.Frequency_Start: float = 1.0 \n
		structure.Frequency_End: float = 1.0 \n
		structure.Level: float = 1.0 \n
		structure.Slope: float = 1.0 \n
		structure.Rbw: enums.Rbw = enums.Rbw.K030 \n
		driver.configure.lteMeas.multiEval.limit.seMask.limit.additional.channelBw.sidelink.set(structure, limit = repcap.Limit.Default, table = repcap.Table.Default, channelBw = repcap.ChannelBw.Default) \n
		Defines additional requirements for the emission mask area <no>, for sidelink measurements. The activation state, the
		area borders, the start value and slope of the upper limit and the resolution bandwidth must be specified. The emission
		mask applies to the channel bandwidth <Band>. \n
			:param structure: for set value, see the help for SidelinkStruct structure arguments.
			:param limit: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Limit')
			:param table: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Additional')
			:param channelBw: optional repeated capability selector. Default value: Bw14 (settable in the interface 'ChannelBw')
		"""
		limit_cmd_val = self._cmd_group.get_repcap_cmd_value(limit, repcap.Limit)
		table_cmd_val = self._cmd_group.get_repcap_cmd_value(table, repcap.Table)
		channelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(channelBw, repcap.ChannelBw)
		self._core.io.write_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:LIMit{limit_cmd_val}:ADDitional{table_cmd_val}:CBANdwidth{channelBw_cmd_val}:SIDelink', structure)

	def get(self, limit=repcap.Limit.Default, table=repcap.Table.Default, channelBw=repcap.ChannelBw.Default) -> SidelinkStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:LIMit<nr>:ADDitional<Table>:CBANdwidth<Band>:SIDelink \n
		Snippet: value: SidelinkStruct = driver.configure.lteMeas.multiEval.limit.seMask.limit.additional.channelBw.sidelink.get(limit = repcap.Limit.Default, table = repcap.Table.Default, channelBw = repcap.ChannelBw.Default) \n
		Defines additional requirements for the emission mask area <no>, for sidelink measurements. The activation state, the
		area borders, the start value and slope of the upper limit and the resolution bandwidth must be specified. The emission
		mask applies to the channel bandwidth <Band>. \n
			:param limit: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Limit')
			:param table: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Additional')
			:param channelBw: optional repeated capability selector. Default value: Bw14 (settable in the interface 'ChannelBw')
			:return: structure: for return value, see the help for SidelinkStruct structure arguments."""
		limit_cmd_val = self._cmd_group.get_repcap_cmd_value(limit, repcap.Limit)
		table_cmd_val = self._cmd_group.get_repcap_cmd_value(table, repcap.Table)
		channelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(channelBw, repcap.ChannelBw)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:LIMit{limit_cmd_val}:ADDitional{table_cmd_val}:CBANdwidth{channelBw_cmd_val}:SIDelink?', self.__class__.SidelinkStruct())
