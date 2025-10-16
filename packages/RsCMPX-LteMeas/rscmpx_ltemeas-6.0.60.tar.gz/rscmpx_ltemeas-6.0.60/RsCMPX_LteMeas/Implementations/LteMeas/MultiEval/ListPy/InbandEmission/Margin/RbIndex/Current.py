from typing import List

from ........Internal.Core import Core
from ........Internal.CommandsGroup import CommandsGroup
from ........Internal.ArgSingleSuppressed import ArgSingleSuppressed
from ........Internal.Types import DataType


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class CurrentCls:
	"""Current commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("current", core, parent)

	def fetch(self) -> List[int]:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:IEMission:MARGin:RBINdex:CURRent \n
		Snippet: value: List[int] = driver.lteMeas.multiEval.listPy.inbandEmission.margin.rbIndex.current.fetch() \n
		Return resource block indices of the in-band emission measurement for all measured list mode segments.
		At these RB indices, the CURRent and EXTReme margins have been detected. \n
		Suppressed linked return values: reliability \n
			:return: rb_index: Comma-separated list of values, one per measured segment"""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_bin_or_ascii_int_list_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:IEMission:MARGin:RBINdex:CURRent?', suppressed)
		return response
