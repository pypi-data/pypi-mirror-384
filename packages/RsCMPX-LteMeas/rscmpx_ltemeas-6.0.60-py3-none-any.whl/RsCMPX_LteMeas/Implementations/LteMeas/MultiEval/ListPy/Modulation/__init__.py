from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ModulationCls:
	"""Modulation commands group definition. 178 total commands, 13 Subgroups, 0 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("modulation", core, parent)

	@property
	def evm(self):
		"""evm commands group. 3 Sub-classes, 0 commands."""
		if not hasattr(self, '_evm'):
			from .Evm import EvmCls
			self._evm = EvmCls(self._core, self._cmd_group)
		return self._evm

	@property
	def merror(self):
		"""merror commands group. 3 Sub-classes, 0 commands."""
		if not hasattr(self, '_merror'):
			from .Merror import MerrorCls
			self._merror = MerrorCls(self._core, self._cmd_group)
		return self._merror

	@property
	def perror(self):
		"""perror commands group. 3 Sub-classes, 0 commands."""
		if not hasattr(self, '_perror'):
			from .Perror import PerrorCls
			self._perror = PerrorCls(self._core, self._cmd_group)
		return self._perror

	@property
	def iqOffset(self):
		"""iqOffset commands group. 4 Sub-classes, 0 commands."""
		if not hasattr(self, '_iqOffset'):
			from .IqOffset import IqOffsetCls
			self._iqOffset = IqOffsetCls(self._core, self._cmd_group)
		return self._iqOffset

	@property
	def freqError(self):
		"""freqError commands group. 4 Sub-classes, 0 commands."""
		if not hasattr(self, '_freqError'):
			from .FreqError import FreqErrorCls
			self._freqError = FreqErrorCls(self._core, self._cmd_group)
		return self._freqError

	@property
	def terror(self):
		"""terror commands group. 4 Sub-classes, 0 commands."""
		if not hasattr(self, '_terror'):
			from .Terror import TerrorCls
			self._terror = TerrorCls(self._core, self._cmd_group)
		return self._terror

	@property
	def tpower(self):
		"""tpower commands group. 5 Sub-classes, 0 commands."""
		if not hasattr(self, '_tpower'):
			from .Tpower import TpowerCls
			self._tpower = TpowerCls(self._core, self._cmd_group)
		return self._tpower

	@property
	def ppower(self):
		"""ppower commands group. 5 Sub-classes, 0 commands."""
		if not hasattr(self, '_ppower'):
			from .Ppower import PpowerCls
			self._ppower = PpowerCls(self._core, self._cmd_group)
		return self._ppower

	@property
	def psd(self):
		"""psd commands group. 5 Sub-classes, 0 commands."""
		if not hasattr(self, '_psd'):
			from .Psd import PsdCls
			self._psd = PsdCls(self._core, self._cmd_group)
		return self._psd

	@property
	def dmodulation(self):
		"""dmodulation commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_dmodulation'):
			from .Dmodulation import DmodulationCls
			self._dmodulation = DmodulationCls(self._core, self._cmd_group)
		return self._dmodulation

	@property
	def dchType(self):
		"""dchType commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_dchType'):
			from .DchType import DchTypeCls
			self._dchType = DchTypeCls(self._core, self._cmd_group)
		return self._dchType

	@property
	def schType(self):
		"""schType commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_schType'):
			from .SchType import SchTypeCls
			self._schType = SchTypeCls(self._core, self._cmd_group)
		return self._schType

	@property
	def dallocation(self):
		"""dallocation commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_dallocation'):
			from .Dallocation import DallocationCls
			self._dallocation = DallocationCls(self._core, self._cmd_group)
		return self._dallocation

	def clone(self) -> 'ModulationCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = ModulationCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
