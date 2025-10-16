from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class PowerCls:
	"""Power commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("power", core, parent)

	def get_hdmode(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:POWer:HDMode \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.power.get_hdmode() \n
		Enables or disables the high dynamic mode for power dynamics measurements. \n
			:return: high_dynamic_mode: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:POWer:HDMode?')
		return Conversions.str_to_bool(response)

	def set_hdmode(self, high_dynamic_mode: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:POWer:HDMode \n
		Snippet: driver.configure.lteMeas.multiEval.power.set_hdmode(high_dynamic_mode = False) \n
		Enables or disables the high dynamic mode for power dynamics measurements. \n
			:param high_dynamic_mode: No help available
		"""
		param = Conversions.bool_to_str(high_dynamic_mode)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:POWer:HDMode {param}')
