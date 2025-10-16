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
		"""READ:LTE:MEASurement<Instance>:PRACh:TRACe:MERRor:MAXimum \n
		Snippet: value: List[float] = driver.lteMeas.prach.trace.merror.maximum.read() \n
		Return the values of the magnitude error traces. Each value is averaged over the samples in one preamble subcarrier. The
		results of the current, average and maximum traces can be retrieved. See also 'Square EVM, Magnitude Error, Phase Error'. \n
		Suppressed linked return values: reliability \n
			:return: results: The number of results depends on the preamble format. Format 0 to 3: 839 EVM values, format 4: 139 EVM values"""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_bin_or_ascii_float_list_suppressed(f'READ:LTE:MEASurement<Instance>:PRACh:TRACe:MERRor:MAXimum?', suppressed)
		return response

	def fetch(self) -> List[float]:
		"""FETCh:LTE:MEASurement<Instance>:PRACh:TRACe:MERRor:MAXimum \n
		Snippet: value: List[float] = driver.lteMeas.prach.trace.merror.maximum.fetch() \n
		Return the values of the magnitude error traces. Each value is averaged over the samples in one preamble subcarrier. The
		results of the current, average and maximum traces can be retrieved. See also 'Square EVM, Magnitude Error, Phase Error'. \n
		Suppressed linked return values: reliability \n
			:return: results: The number of results depends on the preamble format. Format 0 to 3: 839 EVM values, format 4: 139 EVM values"""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_bin_or_ascii_float_list_suppressed(f'FETCh:LTE:MEASurement<Instance>:PRACh:TRACe:MERRor:MAXimum?', suppressed)
		return response
