from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class RbaTableCls:
	"""RbaTable commands group definition. 10 total commands, 4 Subgroups, 0 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("rbaTable", core, parent)

	@property
	def scc(self):
		"""scc commands group. 0 Sub-classes, 2 commands."""
		if not hasattr(self, '_scc'):
			from .Scc import SccCls
			self._scc = SccCls(self._core, self._cmd_group)
		return self._scc

	@property
	def ulca(self):
		"""ulca commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_ulca'):
			from .Ulca import UlcaCls
			self._ulca = UlcaCls(self._core, self._cmd_group)
		return self._ulca

	@property
	def cc(self):
		"""cc commands group. 0 Sub-classes, 2 commands."""
		if not hasattr(self, '_cc'):
			from .Cc import CcCls
			self._cc = CcCls(self._core, self._cmd_group)
		return self._cc

	@property
	def pcc(self):
		"""pcc commands group. 0 Sub-classes, 2 commands."""
		if not hasattr(self, '_pcc'):
			from .Pcc import PccCls
			self._pcc = PccCls(self._core, self._cmd_group)
		return self._pcc

	def clone(self) -> 'RbaTableCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = RbaTableCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
