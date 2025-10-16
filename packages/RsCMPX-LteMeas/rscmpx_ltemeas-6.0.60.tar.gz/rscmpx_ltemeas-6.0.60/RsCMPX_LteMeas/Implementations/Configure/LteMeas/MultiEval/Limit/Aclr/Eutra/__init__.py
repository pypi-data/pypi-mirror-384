from ........Internal.Core import Core
from ........Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class EutraCls:
	"""Eutra commands group definition. 4 total commands, 2 Subgroups, 0 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("eutra", core, parent)

	@property
	def channelBw(self):
		"""channelBw commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_channelBw'):
			from .ChannelBw import ChannelBwCls
			self._channelBw = ChannelBwCls(self._core, self._cmd_group)
		return self._channelBw

	@property
	def carrierAggregation(self):
		"""carrierAggregation commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_carrierAggregation'):
			from .CarrierAggregation import CarrierAggregationCls
			self._carrierAggregation = CarrierAggregationCls(self._core, self._cmd_group)
		return self._carrierAggregation

	def clone(self) -> 'EutraCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = EutraCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
