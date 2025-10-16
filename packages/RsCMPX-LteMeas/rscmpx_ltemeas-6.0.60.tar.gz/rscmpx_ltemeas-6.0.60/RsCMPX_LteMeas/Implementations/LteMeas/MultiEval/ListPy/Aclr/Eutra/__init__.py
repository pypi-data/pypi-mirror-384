from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class EutraCls:
	"""Eutra commands group definition. 12 total commands, 4 Subgroups, 0 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("eutra", core, parent)

	@property
	def negativ(self):
		"""negativ commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_negativ'):
			from .Negativ import NegativCls
			self._negativ = NegativCls(self._core, self._cmd_group)
		return self._negativ

	@property
	def current(self):
		"""current commands group. 0 Sub-classes, 2 commands."""
		if not hasattr(self, '_current'):
			from .Current import CurrentCls
			self._current = CurrentCls(self._core, self._cmd_group)
		return self._current

	@property
	def positiv(self):
		"""positiv commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_positiv'):
			from .Positiv import PositivCls
			self._positiv = PositivCls(self._core, self._cmd_group)
		return self._positiv

	@property
	def average(self):
		"""average commands group. 0 Sub-classes, 2 commands."""
		if not hasattr(self, '_average'):
			from .Average import AverageCls
			self._average = AverageCls(self._core, self._cmd_group)
		return self._average

	def clone(self) -> 'EutraCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = EutraCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
