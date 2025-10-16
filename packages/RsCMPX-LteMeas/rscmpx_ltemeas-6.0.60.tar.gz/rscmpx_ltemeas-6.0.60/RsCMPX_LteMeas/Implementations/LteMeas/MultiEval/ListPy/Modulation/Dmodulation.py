from typing import List

from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal import Conversions
from ......Internal.ArgSingleSuppressed import ArgSingleSuppressed
from ......Internal.Types import DataType
from ...... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class DmodulationCls:
	"""Dmodulation commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("dmodulation", core, parent)

	# noinspection PyTypeChecker
	def fetch(self) -> List[enums.Modulation]:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:MODulation:DMODulation \n
		Snippet: value: List[enums.Modulation] = driver.lteMeas.multiEval.listPy.modulation.dmodulation.fetch() \n
		Return the detected modulation scheme for all measured list mode segments. The result is determined from the last
		measured slot of the statistical length of a segment. If channel type PUCCH is detected, QPSK is returned for the
		modulation scheme because the QPSK limits are applied in that case. \n
		Suppressed linked return values: reliability \n
			:return: modulation: Comma-separated list of values, one per measured segment QPSK, 16QAM, 64QAM, 256QAM"""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_str_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:MODulation:DMODulation?', suppressed)
		return Conversions.str_to_list_enum(response, enums.Modulation)
