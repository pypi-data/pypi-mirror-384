from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class AeoPowerCls:
	"""AeoPower commands group definition. 2 total commands, 0 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("aeoPower", core, parent)

	def get_leading(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:PDYNamics:AEOPower:LEADing \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.pdynamics.aeoPower.get_leading() \n
		Shifts the beginning of the evaluation period for OFF power measurements. \n
			:return: leading: Positive values reduce the evaluation period (starts later) . Negative values increase the evaluation period (starts earlier) .
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:PDYNamics:AEOPower:LEADing?')
		return Conversions.str_to_int(response)

	def set_leading(self, leading: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:PDYNamics:AEOPower:LEADing \n
		Snippet: driver.configure.lteMeas.multiEval.pdynamics.aeoPower.set_leading(leading = 1) \n
		Shifts the beginning of the evaluation period for OFF power measurements. \n
			:param leading: Positive values reduce the evaluation period (starts later) . Negative values increase the evaluation period (starts earlier) .
		"""
		param = Conversions.decimal_value_to_str(leading)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:PDYNamics:AEOPower:LEADing {param}')

	def get_lagging(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:PDYNamics:AEOPower:LAGGing \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.pdynamics.aeoPower.get_lagging() \n
		Shifts the end of the evaluation period for OFF power measurements. \n
			:return: lagging: Positive values reduce the evaluation period (ends earlier) . Negative values increase the evaluation period (ends later) .
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:PDYNamics:AEOPower:LAGGing?')
		return Conversions.str_to_int(response)

	def set_lagging(self, lagging: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:PDYNamics:AEOPower:LAGGing \n
		Snippet: driver.configure.lteMeas.multiEval.pdynamics.aeoPower.set_lagging(lagging = 1) \n
		Shifts the end of the evaluation period for OFF power measurements. \n
			:param lagging: Positive values reduce the evaluation period (ends earlier) . Negative values increase the evaluation period (ends later) .
		"""
		param = Conversions.decimal_value_to_str(lagging)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:PDYNamics:AEOPower:LAGGing {param}')
