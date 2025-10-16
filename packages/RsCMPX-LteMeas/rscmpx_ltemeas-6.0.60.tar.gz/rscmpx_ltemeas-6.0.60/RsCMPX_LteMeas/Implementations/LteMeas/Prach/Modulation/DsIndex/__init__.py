from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal import Conversions
from ......Internal.ArgSingleSuppressed import ArgSingleSuppressed
from ......Internal.Types import DataType


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class DsIndexCls:
	"""DsIndex commands group definition. 2 total commands, 1 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("dsIndex", core, parent)

	@property
	def preamble(self):
		"""preamble commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_preamble'):
			from .Preamble import PreambleCls
			self._preamble = PreambleCls(self._core, self._cmd_group)
		return self._preamble

	def fetch(self) -> int:
		"""FETCh:LTE:MEASurement<Instance>:PRACh:MODulation:DSINdex \n
		Snippet: value: int = driver.lteMeas.prach.modulation.dsIndex.fetch() \n
		Returns the automatically detected or manually configured sequence index for single-preamble measurements. \n
		Suppressed linked return values: reliability \n
			:return: sequence_index: Sequence index"""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_str_suppressed(f'FETCh:LTE:MEASurement<Instance>:PRACh:MODulation:DSINdex?', suppressed)
		return Conversions.str_to_int(response)

	def clone(self) -> 'DsIndexCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = DsIndexCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
