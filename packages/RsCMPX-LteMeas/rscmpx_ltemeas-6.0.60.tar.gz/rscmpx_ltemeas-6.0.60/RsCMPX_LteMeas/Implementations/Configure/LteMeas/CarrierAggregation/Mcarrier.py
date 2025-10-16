from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions
from ..... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class McarrierCls:
	"""Mcarrier commands group definition. 2 total commands, 0 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("mcarrier", core, parent)

	# noinspection PyTypeChecker
	def get_enhanced(self) -> enums.MeasCarrierEnhanced:
		"""CONFigure:LTE:MEASurement<Instance>:CAGGregation:MCARrier:ENHanced \n
		Snippet: value: enums.MeasCarrierEnhanced = driver.configure.lteMeas.carrierAggregation.mcarrier.get_enhanced() \n
		Selects a component carrier for single carrier measurements. \n
			:return: meas_carrier: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:CAGGregation:MCARrier:ENHanced?')
		return Conversions.str_to_scalar_enum(response, enums.MeasCarrierEnhanced)

	def set_enhanced(self, meas_carrier: enums.MeasCarrierEnhanced) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:CAGGregation:MCARrier:ENHanced \n
		Snippet: driver.configure.lteMeas.carrierAggregation.mcarrier.set_enhanced(meas_carrier = enums.MeasCarrierEnhanced.CC1) \n
		Selects a component carrier for single carrier measurements. \n
			:param meas_carrier: No help available
		"""
		param = Conversions.enum_scalar_to_str(meas_carrier, enums.MeasCarrierEnhanced)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:CAGGregation:MCARrier:ENHanced {param}')

	# noinspection PyTypeChecker
	def get_value(self) -> enums.MeasCarrierB:
		"""CONFigure:LTE:MEASurement<Instance>:CAGGregation:MCARrier \n
		Snippet: value: enums.MeasCarrierB = driver.configure.lteMeas.carrierAggregation.mcarrier.get_value() \n
		No command help available \n
			:return: meas_carrier: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:CAGGregation:MCARrier?')
		return Conversions.str_to_scalar_enum(response, enums.MeasCarrierB)

	def set_value(self, meas_carrier: enums.MeasCarrierB) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:CAGGregation:MCARrier \n
		Snippet: driver.configure.lteMeas.carrierAggregation.mcarrier.set_value(meas_carrier = enums.MeasCarrierB.PCC) \n
		No command help available \n
			:param meas_carrier: No help available
		"""
		param = Conversions.enum_scalar_to_str(meas_carrier, enums.MeasCarrierB)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:CAGGregation:MCARrier {param}')
