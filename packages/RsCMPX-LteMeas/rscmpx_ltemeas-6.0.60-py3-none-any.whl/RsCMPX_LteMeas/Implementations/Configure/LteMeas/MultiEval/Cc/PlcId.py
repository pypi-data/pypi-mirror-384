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

	def set(self, phs_layer_cell_id: int, carrierComponent=repcap.CarrierComponent.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:CC<Nr>:PLCid \n
		Snippet: driver.configure.lteMeas.multiEval.cc.plcId.set(phs_layer_cell_id = 1, carrierComponent = repcap.CarrierComponent.Default) \n
		Specifies the physical layer cell ID of component carrier CC<no>. Without carrier aggregation, you can omit <no>.
		For Signal Path = Network, use [CONFigure:]SIGNaling:LTE:CELL:PCID. \n
			:param phs_layer_cell_id: No help available
			:param carrierComponent: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Cc')
		"""
		param = Conversions.decimal_value_to_str(phs_layer_cell_id)
		carrierComponent_cmd_val = self._cmd_group.get_repcap_cmd_value(carrierComponent, repcap.CarrierComponent)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:CC{carrierComponent_cmd_val}:PLCid {param}')

	def get(self, carrierComponent=repcap.CarrierComponent.Default) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:CC<Nr>:PLCid \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.cc.plcId.get(carrierComponent = repcap.CarrierComponent.Default) \n
		Specifies the physical layer cell ID of component carrier CC<no>. Without carrier aggregation, you can omit <no>.
		For Signal Path = Network, use [CONFigure:]SIGNaling:LTE:CELL:PCID. \n
			:param carrierComponent: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Cc')
			:return: phs_layer_cell_id: No help available"""
		carrierComponent_cmd_val = self._cmd_group.get_repcap_cmd_value(carrierComponent, repcap.CarrierComponent)
		response = self._core.io.query_str(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:CC{carrierComponent_cmd_val}:PLCid?')
		return Conversions.str_to_int(response)
