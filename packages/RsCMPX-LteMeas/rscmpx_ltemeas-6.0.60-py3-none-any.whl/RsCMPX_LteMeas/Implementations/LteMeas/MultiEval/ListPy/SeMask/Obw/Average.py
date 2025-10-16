from typing import List

from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal import Conversions
from .......Internal.ArgSingleSuppressed import ArgSingleSuppressed
from .......Internal.Types import DataType


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class AverageCls:
	"""Average commands group definition. 2 total commands, 0 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("average", core, parent)

	def fetch(self) -> List[float]:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:SEMask:OBW:AVERage \n
		Snippet: value: List[float] = driver.lteMeas.multiEval.listPy.seMask.obw.average.fetch() \n
		Return the occupied bandwidth for all measured list mode segments. The values described below are returned by FETCh
		commands. A CALCulate command returns limit check results instead, one value for each result listed below. \n
		Suppressed linked return values: reliability \n
			:return: obw: Comma-separated list of values, one per measured segment"""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_bin_or_ascii_float_list_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:SEMask:OBW:AVERage?', suppressed)
		return response

	def calculate(self) -> List[float or bool]:
		"""CALCulate:LTE:MEASurement<Instance>:MEValuation:LIST:SEMask:OBW:AVERage \n
		Snippet: value: List[float or bool] = driver.lteMeas.multiEval.listPy.seMask.obw.average.calculate() \n
		Return the occupied bandwidth for all measured list mode segments. The values described below are returned by FETCh
		commands. A CALCulate command returns limit check results instead, one value for each result listed below. \n
		Suppressed linked return values: reliability \n
			:return: obw: (float or boolean items) Comma-separated list of values, one per measured segment"""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_str_suppressed(f'CALCulate:LTE:MEASurement<Instance>:MEValuation:LIST:SEMask:OBW:AVERage?', suppressed)
		return Conversions.str_to_float_or_bool_list(response)
