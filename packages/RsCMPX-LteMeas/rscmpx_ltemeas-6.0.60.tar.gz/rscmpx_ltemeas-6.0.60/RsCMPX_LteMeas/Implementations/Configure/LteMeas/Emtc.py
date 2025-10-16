from ....Internal.Core import Core
from ....Internal.CommandsGroup import CommandsGroup
from ....Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class EmtcCls:
	"""Emtc commands group definition. 3 total commands, 0 Subgroups, 3 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("emtc", core, parent)

	def get_enable(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:EMTC:ENABle \n
		Snippet: value: bool = driver.configure.lteMeas.emtc.get_enable() \n
		Enables or disables eMTC. For Signal Path = Network, the setting is not configurable. \n
			:return: enable: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:EMTC:ENABle?')
		return Conversions.str_to_bool(response)

	def set_enable(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:EMTC:ENABle \n
		Snippet: driver.configure.lteMeas.emtc.set_enable(enable = False) \n
		Enables or disables eMTC. For Signal Path = Network, the setting is not configurable. \n
			:param enable: No help available
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:EMTC:ENABle {param}')

	def get_mb(self) -> bool:
		"""CONFigure:LTE:MEASurement<instance>:EMTC:MB<number> \n
		Snippet: value: bool = driver.configure.lteMeas.emtc.get_mb() \n
		Selects the maximum eMTC bandwidth. \n
			:return: enable: OFF: Max bandwidth 1.4 MHz ON: Max bandwidth 5 MHz
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:EMTC:MB5?')
		return Conversions.str_to_bool(response)

	def set_mb(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<instance>:EMTC:MB<number> \n
		Snippet: driver.configure.lteMeas.emtc.set_mb(enable = False) \n
		Selects the maximum eMTC bandwidth. \n
			:param enable: OFF: Max bandwidth 1.4 MHz ON: Max bandwidth 5 MHz
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:EMTC:MB5 {param}')

	def get_nband(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:EMTC:NBANd \n
		Snippet: value: int = driver.configure.lteMeas.emtc.get_nband() \n
		Selects the narrowband used for eMTC. \n
			:return: number: The maximum depends on the channel BW, see 'RB allocation, narrowbands and widebands for eMTC'.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:EMTC:NBANd?')
		return Conversions.str_to_int(response)

	def set_nband(self, number: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:EMTC:NBANd \n
		Snippet: driver.configure.lteMeas.emtc.set_nband(number = 1) \n
		Selects the narrowband used for eMTC. \n
			:param number: The maximum depends on the channel BW, see 'RB allocation, narrowbands and widebands for eMTC'.
		"""
		param = Conversions.decimal_value_to_str(number)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:EMTC:NBANd {param}')
