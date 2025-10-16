from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal import Conversions
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class PlcIdCls:
	"""PlcId commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("plcId", core, parent)

	def set(self, phys_layer_cell_id: int, segment=repcap.Segment.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:PLCid \n
		Snippet: driver.configure.lteMeas.multiEval.listPy.segment.plcId.set(phys_layer_cell_id = 1, segment = repcap.Segment.Default) \n
		Specifies the physical cell ID for segment <no>. See also method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.ListPy.
		plcMode. \n
			:param phys_layer_cell_id: No help available
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
		"""
		param = Conversions.decimal_value_to_str(phys_layer_cell_id)
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:PLCid {param}')

	def get(self, segment=repcap.Segment.Default) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:PLCid \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.listPy.segment.plcId.get(segment = repcap.Segment.Default) \n
		Specifies the physical cell ID for segment <no>. See also method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.ListPy.
		plcMode. \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:return: phys_layer_cell_id: No help available"""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		response = self._core.io.query_str(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:PLCid?')
		return Conversions.str_to_int(response)
