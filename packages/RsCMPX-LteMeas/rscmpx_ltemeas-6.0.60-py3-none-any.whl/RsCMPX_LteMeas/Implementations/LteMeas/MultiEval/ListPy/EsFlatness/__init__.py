from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class EsFlatnessCls:
	"""EsFlatness commands group definition. 30 total commands, 5 Subgroups, 0 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("esFlatness", core, parent)

	@property
	def ripple(self):
		"""ripple commands group. 4 Sub-classes, 0 commands."""
		if not hasattr(self, '_ripple'):
			from .Ripple import RippleCls
			self._ripple = RippleCls(self._core, self._cmd_group)
		return self._ripple

	@property
	def difference(self):
		"""difference commands group. 4 Sub-classes, 0 commands."""
		if not hasattr(self, '_difference'):
			from .Difference import DifferenceCls
			self._difference = DifferenceCls(self._core, self._cmd_group)
		return self._difference

	@property
	def minr(self):
		"""minr commands group. 4 Sub-classes, 0 commands."""
		if not hasattr(self, '_minr'):
			from .Minr import MinrCls
			self._minr = MinrCls(self._core, self._cmd_group)
		return self._minr

	@property
	def maxr(self):
		"""maxr commands group. 4 Sub-classes, 0 commands."""
		if not hasattr(self, '_maxr'):
			from .Maxr import MaxrCls
			self._maxr = MaxrCls(self._core, self._cmd_group)
		return self._maxr

	@property
	def scIndex(self):
		"""scIndex commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_scIndex'):
			from .ScIndex import ScIndexCls
			self._scIndex = ScIndexCls(self._core, self._cmd_group)
		return self._scIndex

	def clone(self) -> 'EsFlatnessCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = EsFlatnessCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
