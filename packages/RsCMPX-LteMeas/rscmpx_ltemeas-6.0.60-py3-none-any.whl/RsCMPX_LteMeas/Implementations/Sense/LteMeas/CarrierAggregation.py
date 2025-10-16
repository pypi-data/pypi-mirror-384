from ....Internal.Core import Core
from ....Internal.CommandsGroup import CommandsGroup
from ....Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class CarrierAggregationCls:
	"""CarrierAggregation commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("carrierAggregation", core, parent)

	def get_fshware(self) -> bool:
		"""SENSe:LTE:MEASurement<Instance>:CAGGregation:FSHWare \n
		Snippet: value: bool = driver.sense.lteMeas.carrierAggregation.get_fshware() \n
		No command help available \n
			:return: value: No help available
		"""
		response = self._core.io.query_str('SENSe:LTE:MEASurement<Instance>:CAGGregation:FSHWare?')
		return Conversions.str_to_bool(response)
