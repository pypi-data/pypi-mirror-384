from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal import Conversions
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class CidxCls:
	"""Cidx commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("cidx", core, parent)

	def set(self, connection_index: int, segment=repcap.Segment.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:CIDX \n
		Snippet: driver.configure.lteMeas.multiEval.listPy.segment.cidx.set(connection_index = 1, segment = repcap.Segment.Default) \n
		Selects the RF connection index for segment <no>. To define the connection indices, see ROUTe:LTE:MEAS<i>:SPATh. \n
			:param connection_index: No help available
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
		"""
		param = Conversions.decimal_value_to_str(connection_index)
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:CIDX {param}')

	def get(self, segment=repcap.Segment.Default) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:CIDX \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.listPy.segment.cidx.get(segment = repcap.Segment.Default) \n
		Selects the RF connection index for segment <no>. To define the connection indices, see ROUTe:LTE:MEAS<i>:SPATh. \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:return: connection_index: No help available"""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		response = self._core.io.query_str(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:CIDX?')
		return Conversions.str_to_int(response)
