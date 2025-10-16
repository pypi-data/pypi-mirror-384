from typing import List

from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal.ArgSingleSuppressed import ArgSingleSuppressed
from .....Internal.Types import DataType


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SreliabilityCls:
	"""Sreliability commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("sreliability", core, parent)

	def fetch(self) -> List[int]:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:SRELiability \n
		Snippet: value: List[int] = driver.lteMeas.multiEval.listPy.sreliability.fetch() \n
		Returns the segment reliability for all measured list mode segments. A common reliability indicator of zero indicates
		that the results in all measured segments are valid. A non-zero value indicates that an error occurred in at least one of
		the measured segments. If you get a non-zero common reliability indicator, you can use this command to retrieve the
		individual reliability values of all measured segments for further analysis. \n
		Suppressed linked return values: reliability \n
			:return: seg_reliability: Comma-separated list of values, one per measured segment The meaning of the returned values is the same as for the common reliability indicator, see previous parameter."""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_bin_or_ascii_int_list_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:SRELiability?', suppressed)
		return response
