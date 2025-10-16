from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.Types import DataType
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct
from .......Internal.ArgSingleList import ArgSingleList
from .......Internal.ArgSingle import ArgSingle
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SeMaskCls:
	"""SeMask commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("seMask", core, parent)

	def set(self, sem_statistics: int, se_enable: bool, obw_enable: bool, sem_enable: bool, segment=repcap.Segment.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:SEMask \n
		Snippet: driver.configure.lteMeas.multiEval.listPy.segment.seMask.set(sem_statistics = 1, se_enable = False, obw_enable = False, sem_enable = False, segment = repcap.Segment.Default) \n
		Defines settings for spectrum emission measurements in list mode for segment <no>. \n
			:param sem_statistics: Statistical length in slots.
			:param se_enable: Enable or disable the measurement of spectrum emission results. ON: Spectrum emission results are measured according to the other ...enable flags in this command. Results for which there is no explicit enable flag are also measured. OFF: No spectrum emission results at all are measured. The other enable flags in this command are ignored.
			:param obw_enable: Enable or disable measurement of occupied bandwidth.
			:param sem_enable: Enable or disable measurement of spectrum emission trace and margin results.
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('sem_statistics', sem_statistics, DataType.Integer), ArgSingle('se_enable', se_enable, DataType.Boolean), ArgSingle('obw_enable', obw_enable, DataType.Boolean), ArgSingle('sem_enable', sem_enable, DataType.Boolean))
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:SEMask {param}'.rstrip())

	# noinspection PyTypeChecker
	class SeMaskStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Sem_Statistics: int: Statistical length in slots.
			- 2 Se_Enable: bool: Enable or disable the measurement of spectrum emission results. ON: Spectrum emission results are measured according to the other ...enable flags in this command. Results for which there is no explicit enable flag are also measured. OFF: No spectrum emission results at all are measured. The other enable flags in this command are ignored.
			- 3 Obw_Enable: bool: Enable or disable measurement of occupied bandwidth.
			- 4 Sem_Enable: bool: Enable or disable measurement of spectrum emission trace and margin results."""
		__meta_args_list = [
			ArgStruct.scalar_int('Sem_Statistics'),
			ArgStruct.scalar_bool('Se_Enable'),
			ArgStruct.scalar_bool('Obw_Enable'),
			ArgStruct.scalar_bool('Sem_Enable')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Sem_Statistics: int = None
			self.Se_Enable: bool = None
			self.Obw_Enable: bool = None
			self.Sem_Enable: bool = None

	def get(self, segment=repcap.Segment.Default) -> SeMaskStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:SEMask \n
		Snippet: value: SeMaskStruct = driver.configure.lteMeas.multiEval.listPy.segment.seMask.get(segment = repcap.Segment.Default) \n
		Defines settings for spectrum emission measurements in list mode for segment <no>. \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:return: structure: for return value, see the help for SeMaskStruct structure arguments."""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:SEMask?', self.__class__.SeMaskStruct())
