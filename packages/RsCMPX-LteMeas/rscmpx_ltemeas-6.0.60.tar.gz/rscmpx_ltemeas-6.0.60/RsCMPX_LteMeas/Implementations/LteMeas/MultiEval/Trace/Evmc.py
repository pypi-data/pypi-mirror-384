from typing import List

from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal.ArgSingleSuppressed import ArgSingleSuppressed
from .....Internal.Types import DataType


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class EvmcCls:
	"""Evmc commands group definition. 2 total commands, 0 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("evmc", core, parent)

	def read(self) -> List[float]:
		"""READ:LTE:MEASurement<Instance>:MEValuation:TRACe:EVMC \n
		Snippet: value: List[float] = driver.lteMeas.multiEval.trace.evmc.read() \n
		Returns the values of the EVM vs subcarrier trace. See also 'Square EVM vs Subcarrier'. \n
		Suppressed linked return values: reliability \n
			:return: ratio: Comma-separated list of EVM values, one value per subcarrier For not allocated subcarriers, NCAP is returned."""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_bin_or_ascii_float_list_suppressed(f'READ:LTE:MEASurement<Instance>:MEValuation:TRACe:EVMC?', suppressed)
		return response

	def fetch(self) -> List[float]:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:TRACe:EVMC \n
		Snippet: value: List[float] = driver.lteMeas.multiEval.trace.evmc.fetch() \n
		Returns the values of the EVM vs subcarrier trace. See also 'Square EVM vs Subcarrier'. \n
		Suppressed linked return values: reliability \n
			:return: ratio: Comma-separated list of EVM values, one value per subcarrier For not allocated subcarriers, NCAP is returned."""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_bin_or_ascii_float_list_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:TRACe:EVMC?', suppressed)
		return response
