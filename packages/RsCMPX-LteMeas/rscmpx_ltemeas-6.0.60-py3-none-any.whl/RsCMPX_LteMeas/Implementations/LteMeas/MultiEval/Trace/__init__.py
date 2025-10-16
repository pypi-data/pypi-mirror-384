from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class TraceCls:
	"""Trace commands group definition. 60 total commands, 10 Subgroups, 0 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("trace", core, parent)

	@property
	def rbaTable(self):
		"""rbaTable commands group. 4 Sub-classes, 0 commands."""
		if not hasattr(self, '_rbaTable'):
			from .RbaTable import RbaTableCls
			self._rbaTable = RbaTableCls(self._core, self._cmd_group)
		return self._rbaTable

	@property
	def iq(self):
		"""iq commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_iq'):
			from .Iq import IqCls
			self._iq = IqCls(self._core, self._cmd_group)
		return self._iq

	@property
	def iemissions(self):
		"""iemissions commands group. 4 Sub-classes, 0 commands."""
		if not hasattr(self, '_iemissions'):
			from .Iemissions import IemissionsCls
			self._iemissions = IemissionsCls(self._core, self._cmd_group)
		return self._iemissions

	@property
	def evmc(self):
		"""evmc commands group. 0 Sub-classes, 2 commands."""
		if not hasattr(self, '_evmc'):
			from .Evmc import EvmcCls
			self._evmc = EvmcCls(self._core, self._cmd_group)
		return self._evmc

	@property
	def evmSymbol(self):
		"""evmSymbol commands group. 3 Sub-classes, 0 commands."""
		if not hasattr(self, '_evmSymbol'):
			from .EvmSymbol import EvmSymbolCls
			self._evmSymbol = EvmSymbolCls(self._core, self._cmd_group)
		return self._evmSymbol

	@property
	def esFlatness(self):
		"""esFlatness commands group. 1 Sub-classes, 2 commands."""
		if not hasattr(self, '_esFlatness'):
			from .EsFlatness import EsFlatnessCls
			self._esFlatness = EsFlatnessCls(self._core, self._cmd_group)
		return self._esFlatness

	@property
	def seMask(self):
		"""seMask commands group. 1 Sub-classes, 0 commands."""
		if not hasattr(self, '_seMask'):
			from .SeMask import SeMaskCls
			self._seMask = SeMaskCls(self._core, self._cmd_group)
		return self._seMask

	@property
	def aclr(self):
		"""aclr commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_aclr'):
			from .Aclr import AclrCls
			self._aclr = AclrCls(self._core, self._cmd_group)
		return self._aclr

	@property
	def pmonitor(self):
		"""pmonitor commands group. 4 Sub-classes, 0 commands."""
		if not hasattr(self, '_pmonitor'):
			from .Pmonitor import PmonitorCls
			self._pmonitor = PmonitorCls(self._core, self._cmd_group)
		return self._pmonitor

	@property
	def pdynamics(self):
		"""pdynamics commands group. 3 Sub-classes, 0 commands."""
		if not hasattr(self, '_pdynamics'):
			from .Pdynamics import PdynamicsCls
			self._pdynamics = PdynamicsCls(self._core, self._cmd_group)
		return self._pdynamics

	def clone(self) -> 'TraceCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = TraceCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
