from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SflatnessCls:
	"""Sflatness commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("sflatness", core, parent)

	# noinspection PyTypeChecker
	class SflatnessStruct(StructBase):
		"""Structure for setting input parameters. Fields: \n
			- Enable: bool: No parameter help available
			- Lower: float: No parameter help available
			- Upper: float: No parameter help available
			- Edge_Lower: float: No parameter help available
			- Edge_Upper: float: No parameter help available
			- Edge_Frequency: float: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_bool('Enable'),
			ArgStruct.scalar_float('Lower'),
			ArgStruct.scalar_float('Upper'),
			ArgStruct.scalar_float('Edge_Lower'),
			ArgStruct.scalar_float('Edge_Upper'),
			ArgStruct.scalar_float('Edge_Frequency')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Enable: bool=None
			self.Lower: float=None
			self.Upper: float=None
			self.Edge_Lower: float=None
			self.Edge_Upper: float=None
			self.Edge_Frequency: float=None

	def set(self, structure: SflatnessStruct, qAMmodOrder=repcap.QAMmodOrder.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM<ModOrder>:SFLatness \n
		Snippet with structure: \n
		structure = driver.configure.lteMeas.multiEval.limit.qam.sflatness.SflatnessStruct() \n
		structure.Enable: bool = False \n
		structure.Lower: float = 1.0 \n
		structure.Upper: float = 1.0 \n
		structure.Edge_Lower: float = 1.0 \n
		structure.Edge_Upper: float = 1.0 \n
		structure.Edge_Frequency: float = 1.0 \n
		driver.configure.lteMeas.multiEval.limit.qam.sflatness.set(structure, qAMmodOrder = repcap.QAMmodOrder.Default) \n
		No command help available \n
			:param structure: for set value, see the help for SflatnessStruct structure arguments.
			:param qAMmodOrder: optional repeated capability selector. Default value: Qam16 (settable in the interface 'Qam')
		"""
		qAMmodOrder_cmd_val = self._cmd_group.get_repcap_cmd_value(qAMmodOrder, repcap.QAMmodOrder)
		self._core.io.write_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM{qAMmodOrder_cmd_val}:SFLatness', structure)

	def get(self, qAMmodOrder=repcap.QAMmodOrder.Default) -> SflatnessStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM<ModOrder>:SFLatness \n
		Snippet: value: SflatnessStruct = driver.configure.lteMeas.multiEval.limit.qam.sflatness.get(qAMmodOrder = repcap.QAMmodOrder.Default) \n
		No command help available \n
			:param qAMmodOrder: optional repeated capability selector. Default value: Qam16 (settable in the interface 'Qam')
			:return: structure: for return value, see the help for SflatnessStruct structure arguments."""
		qAMmodOrder_cmd_val = self._cmd_group.get_repcap_cmd_value(qAMmodOrder, repcap.QAMmodOrder)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM{qAMmodOrder_cmd_val}:SFLatness?', self.__class__.SflatnessStruct())
