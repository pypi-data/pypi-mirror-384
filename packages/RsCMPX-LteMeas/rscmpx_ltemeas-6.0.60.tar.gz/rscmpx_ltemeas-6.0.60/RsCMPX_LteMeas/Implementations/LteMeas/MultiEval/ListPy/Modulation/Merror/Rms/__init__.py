from ........Internal.Core import Core
from ........Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class RmsCls:
	"""Rms commands group definition. 14 total commands, 2 Subgroups, 0 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("rms", core, parent)

	@property
	def low(self):
		"""low commands group. 4 Sub-classes, 0 commands."""
		if not hasattr(self, '_low'):
			from .Low import LowCls
			self._low = LowCls(self._core, self._cmd_group)
		return self._low

	@property
	def high(self):
		"""high commands group. 4 Sub-classes, 0 commands."""
		if not hasattr(self, '_high'):
			from .High import HighCls
			self._high = HighCls(self._core, self._cmd_group)
		return self._high

	def clone(self) -> 'RmsCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = RmsCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
