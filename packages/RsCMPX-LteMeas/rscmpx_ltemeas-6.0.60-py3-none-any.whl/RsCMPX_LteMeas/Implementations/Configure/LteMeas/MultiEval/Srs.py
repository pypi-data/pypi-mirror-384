from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SrsCls:
	"""Srs commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("srs", core, parent)

	def get_enable(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SRS:ENABle \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.srs.get_enable() \n
		Specifies whether a sounding reference signal is allowed (ON) or not (OFF) . For Signal Path = Network, the setting is
		not configurable. \n
			:return: enable: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:SRS:ENABle?')
		return Conversions.str_to_bool(response)

	def set_enable(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SRS:ENABle \n
		Snippet: driver.configure.lteMeas.multiEval.srs.set_enable(enable = False) \n
		Specifies whether a sounding reference signal is allowed (ON) or not (OFF) . For Signal Path = Network, the setting is
		not configurable. \n
			:param enable: No help available
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:SRS:ENABle {param}')
