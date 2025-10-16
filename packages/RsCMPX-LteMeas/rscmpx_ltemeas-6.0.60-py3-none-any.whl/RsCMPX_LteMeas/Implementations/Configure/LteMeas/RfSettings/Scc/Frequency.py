from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal import Conversions
from ...... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class FrequencyCls:
	"""Frequency commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("frequency", core, parent)

	def set(self, analyzer_freq: float, secondaryCC=repcap.SecondaryCC.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings:SCC<Nr>:FREQuency \n
		Snippet: driver.configure.lteMeas.rfSettings.scc.frequency.set(analyzer_freq = 1.0, secondaryCC = repcap.SecondaryCC.Default) \n
		No command help available \n
			:param analyzer_freq: No help available
			:param secondaryCC: optional repeated capability selector. Default value: CC1 (settable in the interface 'Scc')
		"""
		param = Conversions.decimal_value_to_str(analyzer_freq)
		secondaryCC_cmd_val = self._cmd_group.get_repcap_cmd_value(secondaryCC, repcap.SecondaryCC)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:RFSettings:SCC{secondaryCC_cmd_val}:FREQuency {param}')

	def get(self, secondaryCC=repcap.SecondaryCC.Default) -> float:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings:SCC<Nr>:FREQuency \n
		Snippet: value: float = driver.configure.lteMeas.rfSettings.scc.frequency.get(secondaryCC = repcap.SecondaryCC.Default) \n
		No command help available \n
			:param secondaryCC: optional repeated capability selector. Default value: CC1 (settable in the interface 'Scc')
			:return: analyzer_freq: No help available"""
		secondaryCC_cmd_val = self._cmd_group.get_repcap_cmd_value(secondaryCC, repcap.SecondaryCC)
		response = self._core.io.query_str(f'CONFigure:LTE:MEASurement<Instance>:RFSettings:SCC{secondaryCC_cmd_val}:FREQuency?')
		return Conversions.str_to_float(response)
