from typing import List

from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.ArgSingleSuppressed import ArgSingleSuppressed
from .......Internal.Types import DataType
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class StandardDevCls:
	"""StandardDev commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("standardDev", core, parent)

	def fetch(self, ripple=repcap.Ripple.Default) -> List[float]:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:ESFLatness:RIPPle<nr>:SDEViation \n
		Snippet: value: List[float] = driver.lteMeas.multiEval.listPy.esFlatness.ripple.standardDev.fetch(ripple = repcap.Ripple.Default) \n
		Return equalizer spectrum flatness single value results (ripple 1 or ripple 2) for all measured list mode segments. The
		values described below are returned by FETCh commands. A CALCulate command returns limit check results instead, one value
		for each result listed below. \n
		Suppressed linked return values: reliability \n
			:param ripple: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Ripple')
			:return: ripple: Comma-separated list of values, one per measured segment"""
		ripple_cmd_val = self._cmd_group.get_repcap_cmd_value(ripple, repcap.Ripple)
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_bin_or_ascii_float_list_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:ESFLatness:RIPPle{ripple_cmd_val}:SDEViation?', suppressed)
		return response
