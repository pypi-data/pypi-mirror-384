from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ModulationCls:
	"""Modulation commands group definition. 21 total commands, 9 Subgroups, 0 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("modulation", core, parent)

	@property
	def current(self):
		"""current commands group. 0 Sub-classes, 3 commands."""
		if not hasattr(self, '_current'):
			from .Current import CurrentCls
			self._current = CurrentCls(self._core, self._cmd_group)
		return self._current

	@property
	def preamble(self):
		"""preamble commands group. 0 Sub-classes, 2 commands."""
		if not hasattr(self, '_preamble'):
			from .Preamble import PreambleCls
			self._preamble = PreambleCls(self._core, self._cmd_group)
		return self._preamble

	@property
	def average(self):
		"""average commands group. 0 Sub-classes, 3 commands."""
		if not hasattr(self, '_average'):
			from .Average import AverageCls
			self._average = AverageCls(self._core, self._cmd_group)
		return self._average

	@property
	def extreme(self):
		"""extreme commands group. 0 Sub-classes, 3 commands."""
		if not hasattr(self, '_extreme'):
			from .Extreme import ExtremeCls
			self._extreme = ExtremeCls(self._core, self._cmd_group)
		return self._extreme

	@property
	def standardDev(self):
		"""standardDev commands group. 0 Sub-classes, 3 commands."""
		if not hasattr(self, '_standardDev'):
			from .StandardDev import StandardDevCls
			self._standardDev = StandardDevCls(self._core, self._cmd_group)
		return self._standardDev

	@property
	def dpfOffset(self):
		"""dpfOffset commands group. 1 Sub-classes, 1 commands."""
		if not hasattr(self, '_dpfOffset'):
			from .DpfOffset import DpfOffsetCls
			self._dpfOffset = DpfOffsetCls(self._core, self._cmd_group)
		return self._dpfOffset

	@property
	def dsIndex(self):
		"""dsIndex commands group. 1 Sub-classes, 1 commands."""
		if not hasattr(self, '_dsIndex'):
			from .DsIndex import DsIndexCls
			self._dsIndex = DsIndexCls(self._core, self._cmd_group)
		return self._dsIndex

	@property
	def scorrelation(self):
		"""scorrelation commands group. 1 Sub-classes, 1 commands."""
		if not hasattr(self, '_scorrelation'):
			from .Scorrelation import ScorrelationCls
			self._scorrelation = ScorrelationCls(self._core, self._cmd_group)
		return self._scorrelation

	@property
	def nsymbol(self):
		"""nsymbol commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_nsymbol'):
			from .Nsymbol import NsymbolCls
			self._nsymbol = NsymbolCls(self._core, self._cmd_group)
		return self._nsymbol

	def clone(self) -> 'ModulationCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = ModulationCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
