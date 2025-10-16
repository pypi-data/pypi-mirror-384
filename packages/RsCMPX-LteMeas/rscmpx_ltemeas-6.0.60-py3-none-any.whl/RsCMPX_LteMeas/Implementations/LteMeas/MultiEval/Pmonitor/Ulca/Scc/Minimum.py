from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class MinimumCls:
	"""Minimum commands group definition. 2 total commands, 0 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("minimum", core, parent)

	# noinspection PyTypeChecker
	class ResultData(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: No parameter help available
			- 2 Out_Of_Tolerance: int: No parameter help available
			- 3 Tx_Power: float: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct.scalar_float('Tx_Power')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Out_Of_Tolerance: int = None
			self.Tx_Power: float = None

	def read(self, secondaryCC=repcap.SecondaryCC.Default) -> ResultData:
		"""READ:LTE:MEASurement<Instance>:MEValuation:PMONitor:ULCA:SCC<Nr>:MINimum \n
		Snippet: value: ResultData = driver.lteMeas.multiEval.pmonitor.ulca.scc.minimum.read(secondaryCC = repcap.SecondaryCC.Default) \n
		No command help available \n
			:param secondaryCC: optional repeated capability selector. Default value: CC1 (settable in the interface 'Scc')
			:return: structure: for return value, see the help for ResultData structure arguments."""
		secondaryCC_cmd_val = self._cmd_group.get_repcap_cmd_value(secondaryCC, repcap.SecondaryCC)
		return self._core.io.query_struct(f'READ:LTE:MEASurement<Instance>:MEValuation:PMONitor:ULCA:SCC{secondaryCC_cmd_val}:MINimum?', self.__class__.ResultData())

	def fetch(self, secondaryCC=repcap.SecondaryCC.Default) -> ResultData:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:PMONitor:ULCA:SCC<Nr>:MINimum \n
		Snippet: value: ResultData = driver.lteMeas.multiEval.pmonitor.ulca.scc.minimum.fetch(secondaryCC = repcap.SecondaryCC.Default) \n
		No command help available \n
			:param secondaryCC: optional repeated capability selector. Default value: CC1 (settable in the interface 'Scc')
			:return: structure: for return value, see the help for ResultData structure arguments."""
		secondaryCC_cmd_val = self._cmd_group.get_repcap_cmd_value(secondaryCC, repcap.SecondaryCC)
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:PMONitor:ULCA:SCC{secondaryCC_cmd_val}:MINimum?', self.__class__.ResultData())
