from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class PccCls:
	"""Pcc commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("pcc", core, parent)

	def get_frequency(self) -> float:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings[:PCC]:FREQuency \n
		Snippet: value: float = driver.configure.lteMeas.rfSettings.pcc.get_frequency() \n
		No command help available \n
			:return: analyzer_freq: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:RFSettings:PCC:FREQuency?')
		return Conversions.str_to_float(response)

	def set_frequency(self, analyzer_freq: float) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings[:PCC]:FREQuency \n
		Snippet: driver.configure.lteMeas.rfSettings.pcc.set_frequency(analyzer_freq = 1.0) \n
		No command help available \n
			:param analyzer_freq: No help available
		"""
		param = Conversions.decimal_value_to_str(analyzer_freq)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:RFSettings:PCC:FREQuency {param}')
