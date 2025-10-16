from ..........Internal.Core import Core
from ..........Internal.CommandsGroup import CommandsGroup
from ..........Internal.Types import DataType
from ..........Internal.StructBase import StructBase
from ..........Internal.ArgStruct import ArgStruct
from ..........Internal.ArgSingleList import ArgSingleList
from ..........Internal.ArgSingle import ArgSingle
from .......... import enums
from .......... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class OcombinationCls:
	"""Ocombination commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("ocombination", core, parent)

	def set(self, enable: bool, frequency_start: float, frequency_end: float, level: float, rbw: enums.Rbw, limit=repcap.Limit.Default, table=repcap.Table.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:LIMit<nr>:ADDitional<Table>:CAGGregation:OCOMbination \n
		Snippet: driver.configure.lteMeas.multiEval.limit.seMask.limit.additional.carrierAggregation.ocombination.set(enable = False, frequency_start = 1.0, frequency_end = 1.0, level = 1.0, rbw = enums.Rbw.K030, limit = repcap.Limit.Default, table = repcap.Table.Default) \n
		Defines additional requirements for the emission mask area <no>. The activation state, the area borders, an upper limit
		and the resolution bandwidth must be specified. The settings apply to all 'other' channel bandwidth combinations, not
		covered by other commands in this section. \n
			:param enable: OFF: Disables the check of these requirements. ON: Enables the check of these requirements.
			:param frequency_start: Start frequency of the area, relative to the edges of the aggregated channel bandwidth.
			:param frequency_end: Stop frequency of the area, relative to the edges of the aggregated channel bandwidth.
			:param level: Upper limit for the area.
			:param rbw: Resolution bandwidth to be used for the area. K030: 30 kHz K100: 100 kHz M1: 1 MHz
			:param limit: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Limit')
			:param table: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Additional')
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('enable', enable, DataType.Boolean), ArgSingle('frequency_start', frequency_start, DataType.Float), ArgSingle('frequency_end', frequency_end, DataType.Float), ArgSingle('level', level, DataType.Float), ArgSingle('rbw', rbw, DataType.Enum, enums.Rbw))
		limit_cmd_val = self._cmd_group.get_repcap_cmd_value(limit, repcap.Limit)
		table_cmd_val = self._cmd_group.get_repcap_cmd_value(table, repcap.Table)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:LIMit{limit_cmd_val}:ADDitional{table_cmd_val}:CAGGregation:OCOMbination {param}'.rstrip())

	# noinspection PyTypeChecker
	class OcombinationStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Enable: bool: OFF: Disables the check of these requirements. ON: Enables the check of these requirements.
			- 2 Frequency_Start: float: Start frequency of the area, relative to the edges of the aggregated channel bandwidth.
			- 3 Frequency_End: float: Stop frequency of the area, relative to the edges of the aggregated channel bandwidth.
			- 4 Level: float: Upper limit for the area.
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

	def get(self, limit=repcap.Limit.Default, table=repcap.Table.Default) -> OcombinationStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:LIMit<nr>:ADDitional<Table>:CAGGregation:OCOMbination \n
		Snippet: value: OcombinationStruct = driver.configure.lteMeas.multiEval.limit.seMask.limit.additional.carrierAggregation.ocombination.get(limit = repcap.Limit.Default, table = repcap.Table.Default) \n
		Defines additional requirements for the emission mask area <no>. The activation state, the area borders, an upper limit
		and the resolution bandwidth must be specified. The settings apply to all 'other' channel bandwidth combinations, not
		covered by other commands in this section. \n
			:param limit: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Limit')
			:param table: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Additional')
			:return: structure: for return value, see the help for OcombinationStruct structure arguments."""
		limit_cmd_val = self._cmd_group.get_repcap_cmd_value(limit, repcap.Limit)
		table_cmd_val = self._cmd_group.get_repcap_cmd_value(table, repcap.Table)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:LIMit{limit_cmd_val}:ADDitional{table_cmd_val}:CAGGregation:OCOMbination?', self.__class__.OcombinationStruct())
