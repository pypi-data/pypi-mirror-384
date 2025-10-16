from typing import List

from ........Internal.Core import Core
from ........Internal.CommandsGroup import CommandsGroup
from ........Internal.ArgSingleSuppressed import ArgSingleSuppressed
from ........Internal.Types import DataType
from ........ import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class CurrentCls:
	"""Current commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("current", core, parent)

	def fetch(self, maxRange=repcap.MaxRange.Default) -> List[int]:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:ESFLatness:SCINdex:MAXimum<nr>:CURRent \n
		Snippet: value: List[int] = driver.lteMeas.multiEval.listPy.esFlatness.scIndex.maximum.current.fetch(maxRange = repcap.MaxRange.Default) \n
		Return subcarrier indices of the equalizer spectrum flatness measurement for all measured list mode segments. At these SC
		indices, the current MINimum or MAXimum power of the equalizer coefficients has been detected within the selected range. \n
		Suppressed linked return values: reliability \n
			:param maxRange: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Maximum')
			:return: maximum: Comma-separated list of values, one per measured segment"""
		maxRange_cmd_val = self._cmd_group.get_repcap_cmd_value(maxRange, repcap.MaxRange)
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_bin_or_ascii_int_list_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:ESFLatness:SCINdex:MAXimum{maxRange_cmd_val}:CURRent?', suppressed)
		return response
