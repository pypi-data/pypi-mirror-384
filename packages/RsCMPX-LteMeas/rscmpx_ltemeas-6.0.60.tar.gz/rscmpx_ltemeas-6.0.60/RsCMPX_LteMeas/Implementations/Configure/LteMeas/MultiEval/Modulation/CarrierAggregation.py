from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal import Conversions
from ...... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class CarrierAggregationCls:
	"""CarrierAggregation commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("carrierAggregation", core, parent)

	# noinspection PyTypeChecker
	def get_llocation(self) -> enums.CarrAggrLocalOscLocation:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:MODulation:CAGGregation:LLOCation \n
		Snippet: value: enums.CarrAggrLocalOscLocation = driver.configure.lteMeas.multiEval.modulation.carrierAggregation.get_llocation() \n
		Specifies the UE transmitter architecture (local oscillator location) used for contiguous carrier aggregation. \n
			:return: value: CACB: Center of aggregated channel bandwidth CECC: Center of each component carrier
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:MODulation:CAGGregation:LLOCation?')
		return Conversions.str_to_scalar_enum(response, enums.CarrAggrLocalOscLocation)

	def set_llocation(self, value: enums.CarrAggrLocalOscLocation) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:MODulation:CAGGregation:LLOCation \n
		Snippet: driver.configure.lteMeas.multiEval.modulation.carrierAggregation.set_llocation(value = enums.CarrAggrLocalOscLocation.AUTO) \n
		Specifies the UE transmitter architecture (local oscillator location) used for contiguous carrier aggregation. \n
			:param value: CACB: Center of aggregated channel bandwidth CECC: Center of each component carrier
		"""
		param = Conversions.enum_scalar_to_str(value, enums.CarrAggrLocalOscLocation)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:MODulation:CAGGregation:LLOCation {param}')
