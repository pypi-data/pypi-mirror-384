from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.Types import DataType
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct
from .......Internal.ArgSingleList import ArgSingleList
from .......Internal.ArgSingle import ArgSingle
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class PowerCls:
	"""Power commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("power", core, parent)

	def set(self, power_statistics: int, power_enable: bool, segment=repcap.Segment.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:POWer \n
		Snippet: driver.configure.lteMeas.multiEval.listPy.segment.power.set(power_statistics = 1, power_enable = False, segment = repcap.Segment.Default) \n
		Defines settings for the measurement of the total TX power of all carriers for segment <no>. \n
			:param power_statistics: Statistical length in subframes
			:param power_enable: Enables or disables the measurement of the total TX power.
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('power_statistics', power_statistics, DataType.Integer), ArgSingle('power_enable', power_enable, DataType.Boolean))
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:POWer {param}'.rstrip())

	# noinspection PyTypeChecker
	class PowerStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Power_Statistics: int: Statistical length in subframes
			- 2 Power_Enable: bool: Enables or disables the measurement of the total TX power."""
		__meta_args_list = [
			ArgStruct.scalar_int('Power_Statistics'),
			ArgStruct.scalar_bool('Power_Enable')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Power_Statistics: int = None
			self.Power_Enable: bool = None

	def get(self, segment=repcap.Segment.Default) -> PowerStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:POWer \n
		Snippet: value: PowerStruct = driver.configure.lteMeas.multiEval.listPy.segment.power.get(segment = repcap.Segment.Default) \n
		Defines settings for the measurement of the total TX power of all carriers for segment <no>. \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:return: structure: for return value, see the help for PowerStruct structure arguments."""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:POWer?', self.__class__.PowerStruct())
