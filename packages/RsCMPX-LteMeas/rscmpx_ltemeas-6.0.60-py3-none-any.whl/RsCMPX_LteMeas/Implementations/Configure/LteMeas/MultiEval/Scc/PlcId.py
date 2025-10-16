from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal import Conversions
from ...... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class PlcIdCls:
	"""PlcId commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("plcId", core, parent)

	def set(self, phs_layer_cell_id: int, secondaryCC=repcap.SecondaryCC.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SCC<Nr>:PLCid \n
		Snippet: driver.configure.lteMeas.multiEval.scc.plcId.set(phs_layer_cell_id = 1, secondaryCC = repcap.SecondaryCC.Default) \n
		No command help available \n
			:param phs_layer_cell_id: No help available
			:param secondaryCC: optional repeated capability selector. Default value: CC1 (settable in the interface 'Scc')
		"""
		param = Conversions.decimal_value_to_str(phs_layer_cell_id)
		secondaryCC_cmd_val = self._cmd_group.get_repcap_cmd_value(secondaryCC, repcap.SecondaryCC)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:SCC{secondaryCC_cmd_val}:PLCid {param}')

	def get(self, secondaryCC=repcap.SecondaryCC.Default) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SCC<Nr>:PLCid \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.scc.plcId.get(secondaryCC = repcap.SecondaryCC.Default) \n
		No command help available \n
			:param secondaryCC: optional repeated capability selector. Default value: CC1 (settable in the interface 'Scc')
			:return: phs_layer_cell_id: No help available"""
		secondaryCC_cmd_val = self._cmd_group.get_repcap_cmd_value(secondaryCC, repcap.SecondaryCC)
		response = self._core.io.query_str(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:SCC{secondaryCC_cmd_val}:PLCid?')
		return Conversions.str_to_int(response)
