from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ScountCls:
	"""Scount commands group definition. 2 total commands, 0 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("scount", core, parent)

	def get_modulation(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:SCOunt:MODulation \n
		Snippet: value: int = driver.configure.lteMeas.prach.scount.get_modulation() \n
		Specifies the statistic count of the measurement. The statistic count is equal to the number of measurement intervals per
		single shot. \n
			:return: statistic_count: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:PRACh:SCOunt:MODulation?')
		return Conversions.str_to_int(response)

	def set_modulation(self, statistic_count: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:SCOunt:MODulation \n
		Snippet: driver.configure.lteMeas.prach.scount.set_modulation(statistic_count = 1) \n
		Specifies the statistic count of the measurement. The statistic count is equal to the number of measurement intervals per
		single shot. \n
			:param statistic_count: No help available
		"""
		param = Conversions.decimal_value_to_str(statistic_count)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:PRACh:SCOunt:MODulation {param}')

	def get_pdynamics(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:SCOunt:PDYNamics \n
		Snippet: value: int = driver.configure.lteMeas.prach.scount.get_pdynamics() \n
		Specifies the statistic count of the measurement. The statistic count is equal to the number of measurement intervals per
		single shot. \n
			:return: statistic_count: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:PRACh:SCOunt:PDYNamics?')
		return Conversions.str_to_int(response)

	def set_pdynamics(self, statistic_count: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:SCOunt:PDYNamics \n
		Snippet: driver.configure.lteMeas.prach.scount.set_pdynamics(statistic_count = 1) \n
		Specifies the statistic count of the measurement. The statistic count is equal to the number of measurement intervals per
		single shot. \n
			:param statistic_count: No help available
		"""
		param = Conversions.decimal_value_to_str(statistic_count)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:PRACh:SCOunt:PDYNamics {param}')
