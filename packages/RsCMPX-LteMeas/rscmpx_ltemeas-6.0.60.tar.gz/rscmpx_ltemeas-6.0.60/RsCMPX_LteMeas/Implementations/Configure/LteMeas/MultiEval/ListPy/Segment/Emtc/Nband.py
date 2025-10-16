from ........Internal.Core import Core
from ........Internal.CommandsGroup import CommandsGroup
from ........Internal import Conversions
from ........ import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class NbandCls:
	"""Nband commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("nband", core, parent)

	def set(self, number: int, segment=repcap.Segment.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:EMTC:NBANd \n
		Snippet: driver.configure.lteMeas.multiEval.listPy.segment.emtc.nband.set(number = 1, segment = repcap.Segment.Default) \n
		Selects the eMTC narrowband for segment <no>. \n
			:param number: The maximum depends on the channel BW, see 'RB allocation, narrowbands and widebands for eMTC'.
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
		"""
		param = Conversions.decimal_value_to_str(number)
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:EMTC:NBANd {param}')

	def get(self, segment=repcap.Segment.Default) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:EMTC:NBANd \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.listPy.segment.emtc.nband.get(segment = repcap.Segment.Default) \n
		Selects the eMTC narrowband for segment <no>. \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:return: number: The maximum depends on the channel BW, see 'RB allocation, narrowbands and widebands for eMTC'."""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		response = self._core.io.query_str(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:EMTC:NBANd?')
		return Conversions.str_to_int(response)
