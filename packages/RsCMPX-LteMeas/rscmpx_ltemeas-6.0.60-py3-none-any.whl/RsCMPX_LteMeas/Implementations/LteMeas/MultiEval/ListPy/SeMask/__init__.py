from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SeMaskCls:
	"""SeMask commands group definition. 24 total commands, 5 Subgroups, 0 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("seMask", core, parent)

	@property
	def obw(self):
		"""obw commands group. 4 Sub-classes, 0 commands."""
		if not hasattr(self, '_obw'):
			from .Obw import ObwCls
			self._obw = ObwCls(self._core, self._cmd_group)
		return self._obw

	@property
	def txPower(self):
		"""txPower commands group. 5 Sub-classes, 0 commands."""
		if not hasattr(self, '_txPower'):
			from .TxPower import TxPowerCls
			self._txPower = TxPowerCls(self._core, self._cmd_group)
		return self._txPower

	@property
	def margin(self):
		"""margin commands group. 1 Sub-classes, 0 commands."""
		if not hasattr(self, '_margin'):
			from .Margin import MarginCls
			self._margin = MarginCls(self._core, self._cmd_group)
		return self._margin

	@property
	def dchType(self):
		"""dchType commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_dchType'):
			from .DchType import DchTypeCls
			self._dchType = DchTypeCls(self._core, self._cmd_group)
		return self._dchType

	@property
	def dallocation(self):
		"""dallocation commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_dallocation'):
			from .Dallocation import DallocationCls
			self._dallocation = DallocationCls(self._core, self._cmd_group)
		return self._dallocation

	def clone(self) -> 'SeMaskCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = SeMaskCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
