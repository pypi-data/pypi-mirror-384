from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal import Conversions
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class PmonitorCls:
	"""Pmonitor commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("pmonitor", core, parent)

	def set(self, enable: bool, segment=repcap.Segment.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:PMONitor \n
		Snippet: driver.configure.lteMeas.multiEval.listPy.segment.pmonitor.set(enable = False, segment = repcap.Segment.Default) \n
		Enables or disables the measurement of power monitor results (power of one carrier) for segment <no>. \n
			:param enable: No help available
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
		"""
		param = Conversions.bool_to_str(enable)
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:PMONitor {param}')

	def get(self, segment=repcap.Segment.Default) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:PMONitor \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.listPy.segment.pmonitor.get(segment = repcap.Segment.Default) \n
		Enables or disables the measurement of power monitor results (power of one carrier) for segment <no>. \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:return: enable: No help available"""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		response = self._core.io.query_str(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:PMONitor?')
		return Conversions.str_to_bool(response)
