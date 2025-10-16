from typing import List

from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal import Conversions
from ......Internal.ArgSingleSuppressed import ArgSingleSuppressed
from ......Internal.Types import DataType
from ...... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class DchTypeCls:
	"""DchType commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("dchType", core, parent)

	# noinspection PyTypeChecker
	def fetch(self) -> List[enums.UplinkChannelType]:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:MODulation:DCHType \n
		Snippet: value: List[enums.UplinkChannelType] = driver.lteMeas.multiEval.listPy.modulation.dchType.fetch() \n
		Return the uplink channel type for all measured list mode segments. The result is determined from the last measured slot
		of the statistical length of a segment. The individual measurements provide the same result when measuring the same slot.
		However different statistical lengths can be defined for the measurements so that the measured slots and returned results
		can differ. \n
		Suppressed linked return values: reliability \n
			:return: channel_type: Comma-separated list of values, one per measured segment"""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_str_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:MODulation:DCHType?', suppressed)
		return Conversions.str_to_list_enum(response, enums.UplinkChannelType)
