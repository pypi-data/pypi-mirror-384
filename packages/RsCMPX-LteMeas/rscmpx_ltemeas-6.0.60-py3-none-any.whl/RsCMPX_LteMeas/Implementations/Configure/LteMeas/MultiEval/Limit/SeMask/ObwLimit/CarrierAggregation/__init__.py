from .........Internal.Core import Core
from .........Internal.CommandsGroup import CommandsGroup
from .........Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class CarrierAggregationCls:
	"""CarrierAggregation commands group definition. 3 total commands, 1 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("carrierAggregation", core, parent)

	@property
	def channelBw1st(self):
		"""channelBw1st commands group. 1 Sub-classes, 0 commands."""
		if not hasattr(self, '_channelBw1st'):
			from .ChannelBw1st import ChannelBw1stCls
			self._channelBw1st = ChannelBw1stCls(self._core, self._cmd_group)
		return self._channelBw1st

	def get_ocombination(self) -> float or bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:OBWLimit:CAGGregation:OCOMbination \n
		Snippet: value: float or bool = driver.configure.lteMeas.multiEval.limit.seMask.obwLimit.carrierAggregation.get_ocombination() \n
		Defines an upper limit for the occupied bandwidth. The setting applies to all 'other' channel bandwidth combinations, not
		covered by other commands in this section. \n
			:return: obw_limit: (float or boolean) No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:OBWLimit:CAGGregation:OCOMbination?')
		return Conversions.str_to_float_or_bool(response)

	def set_ocombination(self, obw_limit: float or bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:OBWLimit:CAGGregation:OCOMbination \n
		Snippet: driver.configure.lteMeas.multiEval.limit.seMask.obwLimit.carrierAggregation.set_ocombination(obw_limit = 1.0) \n
		Defines an upper limit for the occupied bandwidth. The setting applies to all 'other' channel bandwidth combinations, not
		covered by other commands in this section. \n
			:param obw_limit: (float or boolean) No help available
		"""
		param = Conversions.decimal_or_bool_value_to_str(obw_limit)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:OBWLimit:CAGGregation:OCOMbination {param}')

	def clone(self) -> 'CarrierAggregationCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = CarrierAggregationCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
