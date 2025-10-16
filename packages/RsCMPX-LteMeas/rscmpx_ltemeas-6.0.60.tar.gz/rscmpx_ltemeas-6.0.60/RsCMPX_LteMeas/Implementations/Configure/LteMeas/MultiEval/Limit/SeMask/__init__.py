from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SeMaskCls:
	"""SeMask commands group definition. 13 total commands, 3 Subgroups, 0 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("seMask", core, parent)

	@property
	def obwLimit(self):
		"""obwLimit commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_obwLimit'):
			from .ObwLimit import ObwLimitCls
			self._obwLimit = ObwLimitCls(self._core, self._cmd_group)
		return self._obwLimit

	@property
	def limit(self):
		"""limit commands group. 3 Sub-classes, 0 commands."""
		if not hasattr(self, '_limit'):
			from .Limit import LimitCls
			self._limit = LimitCls(self._core, self._cmd_group)
		return self._limit

	@property
	def atTolerance(self):
		"""atTolerance commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_atTolerance'):
			from .AtTolerance import AtToleranceCls
			self._atTolerance = AtToleranceCls(self._core, self._cmd_group)
		return self._atTolerance

	def clone(self) -> 'SeMaskCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = SeMaskCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
