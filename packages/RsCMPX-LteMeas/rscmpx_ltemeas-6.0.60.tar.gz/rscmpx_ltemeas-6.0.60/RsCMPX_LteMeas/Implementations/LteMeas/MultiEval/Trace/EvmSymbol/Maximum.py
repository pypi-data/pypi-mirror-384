from typing import List

from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal.ArgSingleSuppressed import ArgSingleSuppressed
from ......Internal.Types import DataType


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class MaximumCls:
	"""Maximum commands group definition. 2 total commands, 0 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("maximum", core, parent)

	def read(self) -> List[float]:
		"""READ:LTE:MEASurement<Instance>:MEValuation:TRACe:EVMSymbol:MAXimum \n
		Snippet: value: List[float] = driver.lteMeas.multiEval.trace.evmSymbol.maximum.read() \n
		Returns the values of the EVM vs modulation symbol trace. See also 'Square EVM'. \n
		Suppressed linked return values: reliability \n
			:return: ratio: Comma-separated list of EVM values, one value per modulation symbol"""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_bin_or_ascii_float_list_suppressed(f'READ:LTE:MEASurement<Instance>:MEValuation:TRACe:EVMSymbol:MAXimum?', suppressed)
		return response

	def fetch(self) -> List[float]:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:TRACe:EVMSymbol:MAXimum \n
		Snippet: value: List[float] = driver.lteMeas.multiEval.trace.evmSymbol.maximum.fetch() \n
		Returns the values of the EVM vs modulation symbol trace. See also 'Square EVM'. \n
		Suppressed linked return values: reliability \n
			:return: ratio: Comma-separated list of EVM values, one value per modulation symbol"""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_bin_or_ascii_float_list_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:TRACe:EVMSymbol:MAXimum?', suppressed)
		return response
