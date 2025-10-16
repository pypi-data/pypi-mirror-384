from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal import Conversions
from ......Internal.ArgSingleSuppressed import ArgSingleSuppressed
from ......Internal.Types import DataType


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ScorrelationCls:
	"""Scorrelation commands group definition. 2 total commands, 1 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("scorrelation", core, parent)

	@property
	def preamble(self):
		"""preamble commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_preamble'):
			from .Preamble import PreambleCls
			self._preamble = PreambleCls(self._core, self._cmd_group)
		return self._preamble

	def fetch(self) -> float:
		"""FETCh:LTE:MEASurement<Instance>:PRACh:MODulation:SCORrelation \n
		Snippet: value: float = driver.lteMeas.prach.modulation.scorrelation.fetch() \n
		Returns the sequence correlation for single-preamble measurements. It indicates the correlation between the ideal
		preamble sequence determined from the parameter settings and the measured preamble sequence. A value of 1 corresponds to
		perfect correlation. A value close to 0 indicates that the preamble sequence was not found. \n
		Suppressed linked return values: reliability \n
			:return: seq_correlation: Sequence correlation"""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_str_suppressed(f'FETCh:LTE:MEASurement<Instance>:PRACh:MODulation:SCORrelation?', suppressed)
		return Conversions.str_to_float(response)

	def clone(self) -> 'ScorrelationCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = ScorrelationCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
