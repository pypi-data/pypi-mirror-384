from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class EsFlatnessCls:
	"""EsFlatness commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("esFlatness", core, parent)

	# noinspection PyTypeChecker
	class EsFlatnessStruct(StructBase):
		"""Structure for setting input parameters. Fields: \n
			- Enable: bool: OFF: disables the limit check ON: enables the limit check
			- Range_1: float: Upper limit for max(range 1) - min(range 1)
			- Range_2: float: Upper limit for max(range 2) - min(range 2)
			- Max_1_Min_2: float: Upper limit for max(range 1) - min(range 2)
			- Max_2_Min_1: float: Upper limit for max(range 2) - min(range 1)
			- Edge_Frequency: float: Frequency band edge distance of border between range 1 and range 2"""
		__meta_args_list = [
			ArgStruct.scalar_bool('Enable'),
			ArgStruct.scalar_float('Range_1'),
			ArgStruct.scalar_float('Range_2'),
			ArgStruct.scalar_float('Max_1_Min_2'),
			ArgStruct.scalar_float('Max_2_Min_1'),
			ArgStruct.scalar_float('Edge_Frequency')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Enable: bool=None
			self.Range_1: float=None
			self.Range_2: float=None
			self.Max_1_Min_2: float=None
			self.Max_2_Min_1: float=None
			self.Edge_Frequency: float=None

	def set(self, structure: EsFlatnessStruct, qAMmodOrder=repcap.QAMmodOrder.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM<ModOrder>:ESFLatness \n
		Snippet with structure: \n
		structure = driver.configure.lteMeas.multiEval.limit.qam.esFlatness.EsFlatnessStruct() \n
		structure.Enable: bool = False \n
		structure.Range_1: float = 1.0 \n
		structure.Range_2: float = 1.0 \n
		structure.Max_1_Min_2: float = 1.0 \n
		structure.Max_2_Min_1: float = 1.0 \n
		structure.Edge_Frequency: float = 1.0 \n
		driver.configure.lteMeas.multiEval.limit.qam.esFlatness.set(structure, qAMmodOrder = repcap.QAMmodOrder.Default) \n
		Defines limits for the equalizer spectrum flatness, for QAM modulations. \n
			:param structure: for set value, see the help for EsFlatnessStruct structure arguments.
			:param qAMmodOrder: optional repeated capability selector. Default value: Qam16 (settable in the interface 'Qam')
		"""
		qAMmodOrder_cmd_val = self._cmd_group.get_repcap_cmd_value(qAMmodOrder, repcap.QAMmodOrder)
		self._core.io.write_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM{qAMmodOrder_cmd_val}:ESFLatness', structure)

	def get(self, qAMmodOrder=repcap.QAMmodOrder.Default) -> EsFlatnessStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM<ModOrder>:ESFLatness \n
		Snippet: value: EsFlatnessStruct = driver.configure.lteMeas.multiEval.limit.qam.esFlatness.get(qAMmodOrder = repcap.QAMmodOrder.Default) \n
		Defines limits for the equalizer spectrum flatness, for QAM modulations. \n
			:param qAMmodOrder: optional repeated capability selector. Default value: Qam16 (settable in the interface 'Qam')
			:return: structure: for return value, see the help for EsFlatnessStruct structure arguments."""
		qAMmodOrder_cmd_val = self._cmd_group.get_repcap_cmd_value(qAMmodOrder, repcap.QAMmodOrder)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM{qAMmodOrder_cmd_val}:ESFLatness?', self.__class__.EsFlatnessStruct())
