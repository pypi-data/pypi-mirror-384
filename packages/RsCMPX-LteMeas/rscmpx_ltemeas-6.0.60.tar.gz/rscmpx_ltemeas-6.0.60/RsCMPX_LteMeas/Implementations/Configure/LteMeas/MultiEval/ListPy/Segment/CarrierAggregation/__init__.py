from ........Internal.Core import Core
from ........Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class CarrierAggregationCls:
	"""CarrierAggregation commands group definition. 3 total commands, 2 Subgroups, 0 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("carrierAggregation", core, parent)

	@property
	def acSpacing(self):
		"""acSpacing commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_acSpacing'):
			from .AcSpacing import AcSpacingCls
			self._acSpacing = AcSpacingCls(self._core, self._cmd_group)
		return self._acSpacing

	@property
	def mcarrier(self):
		"""mcarrier commands group. 1 Sub-classes, 1 commands."""
		if not hasattr(self, '_mcarrier'):
			from .Mcarrier import McarrierCls
			self._mcarrier = McarrierCls(self._core, self._cmd_group)
		return self._mcarrier

	def clone(self) -> 'CarrierAggregationCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = CarrierAggregationCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
