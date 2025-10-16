from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions
from ..... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class NsValueCls:
	"""NsValue commands group definition. 2 total commands, 0 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("nsValue", core, parent)

	# noinspection PyTypeChecker
	def get_carrier_aggregation(self) -> enums.NetworkSigValue:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:NSValue:CAGGregation \n
		Snippet: value: enums.NetworkSigValue = driver.configure.lteMeas.multiEval.nsValue.get_carrier_aggregation() \n
		Selects the 'network signaled value' for measurements with carrier aggregation. \n
			:return: value: Value CA_NS_01 to CA_NS_32
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:NSValue:CAGGregation?')
		return Conversions.str_to_scalar_enum(response, enums.NetworkSigValue)

	def set_carrier_aggregation(self, value: enums.NetworkSigValue) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:NSValue:CAGGregation \n
		Snippet: driver.configure.lteMeas.multiEval.nsValue.set_carrier_aggregation(value = enums.NetworkSigValue.NS01) \n
		Selects the 'network signaled value' for measurements with carrier aggregation. \n
			:param value: Value CA_NS_01 to CA_NS_32
		"""
		param = Conversions.enum_scalar_to_str(value, enums.NetworkSigValue)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:NSValue:CAGGregation {param}')

	# noinspection PyTypeChecker
	def get_value(self) -> enums.NetworkSigValueNoCarrAggr:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:NSValue \n
		Snippet: value: enums.NetworkSigValueNoCarrAggr = driver.configure.lteMeas.multiEval.nsValue.get_value() \n
		Selects the 'network signaled value' for measurements without carrier aggregation. For Signal Path = Network, the setting
		is not configurable. \n
			:return: value: Value NS_01 to NS_288
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:NSValue?')
		return Conversions.str_to_scalar_enum(response, enums.NetworkSigValueNoCarrAggr)

	def set_value(self, value: enums.NetworkSigValueNoCarrAggr) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:NSValue \n
		Snippet: driver.configure.lteMeas.multiEval.nsValue.set_value(value = enums.NetworkSigValueNoCarrAggr.NS01) \n
		Selects the 'network signaled value' for measurements without carrier aggregation. For Signal Path = Network, the setting
		is not configurable. \n
			:param value: Value NS_01 to NS_288
		"""
		param = Conversions.enum_scalar_to_str(value, enums.NetworkSigValueNoCarrAggr)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:NSValue {param}')
