from ....Internal.Core import Core
from ....Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class LteMeasCls:
	"""LteMeas commands group definition. 6 total commands, 2 Subgroups, 0 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("lteMeas", core, parent)

	@property
	def carrierAggregation(self):
		"""carrierAggregation commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_carrierAggregation'):
			from .CarrierAggregation import CarrierAggregationCls
			self._carrierAggregation = CarrierAggregationCls(self._core, self._cmd_group)
		return self._carrierAggregation

	@property
	def multiEval(self):
		"""multiEval commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_multiEval'):
			from .MultiEval import MultiEvalCls
			self._multiEval = MultiEvalCls(self._core, self._cmd_group)
		return self._multiEval

	def clone(self) -> 'LteMeasCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = LteMeasCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
