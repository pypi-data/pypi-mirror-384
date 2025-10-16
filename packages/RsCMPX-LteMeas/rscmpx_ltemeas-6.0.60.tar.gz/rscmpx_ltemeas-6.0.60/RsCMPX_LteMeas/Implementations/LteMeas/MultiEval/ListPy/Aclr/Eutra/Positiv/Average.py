from typing import List

from ........Internal.Core import Core
from ........Internal.CommandsGroup import CommandsGroup
from ........Internal import Conversions
from ........Internal.ArgSingleSuppressed import ArgSingleSuppressed
from ........Internal.Types import DataType
from ........ import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class AverageCls:
	"""Average commands group definition. 2 total commands, 0 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("average", core, parent)

	def fetch(self) -> List[float]:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:ACLR:EUTRa:POSitiv:AVERage \n
		Snippet: value: List[float] = driver.lteMeas.multiEval.listPy.aclr.eutra.positiv.average.fetch() \n
		Return the ACLR for the first adjacent E-UTRA channel above (POSitiv) or below (NEGativ) the carrier frequency for all
		measured list mode segments. The values described below are returned by FETCh commands. A CALCulate command returns limit
		check results instead, one value for each result listed below. \n
		Suppressed linked return values: reliability \n
			:return: eutra_positiv: Comma-separated list of values, one per measured segment"""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_bin_or_ascii_float_list_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:ACLR:EUTRa:POSitiv:AVERage?', suppressed)
		return response

	# noinspection PyTypeChecker
	def calculate(self) -> List[enums.ResultStatus2]:
		"""CALCulate:LTE:MEASurement<Instance>:MEValuation:LIST:ACLR:EUTRa:POSitiv:AVERage \n
		Snippet: value: List[enums.ResultStatus2] = driver.lteMeas.multiEval.listPy.aclr.eutra.positiv.average.calculate() \n
		Return the ACLR for the first adjacent E-UTRA channel above (POSitiv) or below (NEGativ) the carrier frequency for all
		measured list mode segments. The values described below are returned by FETCh commands. A CALCulate command returns limit
		check results instead, one value for each result listed below. \n
		Suppressed linked return values: reliability \n
			:return: eutra_positiv: Comma-separated list of values, one per measured segment"""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_str_suppressed(f'CALCulate:LTE:MEASurement<Instance>:MEValuation:LIST:ACLR:EUTRa:POSitiv:AVERage?', suppressed)
		return Conversions.str_to_list_enum(response, enums.ResultStatus2)
