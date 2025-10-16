from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions
from .....Internal.ArgSingleSuppressed import ArgSingleSuppressed
from .....Internal.Types import DataType
from ..... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class DchTypeCls:
	"""DchType commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("dchType", core, parent)

	# noinspection PyTypeChecker
	def fetch(self) -> enums.UplinkChannelType:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:SEMask:DCHType \n
		Snippet: value: enums.UplinkChannelType = driver.lteMeas.multiEval.seMask.dchType.fetch() \n
		Returns the uplink channel type for the measured slot. If the same slot is measured by the individual measurements, all
		commands yield the same result. If different statistic counts are defined for the modulation, ACLR and spectrum emission
		mask measurements, different slots can be measured and different results can be returned by the individual commands. \n
		Suppressed linked return values: reliability \n
			:return: channel_type: No help available"""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_str_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:SEMask:DCHType?', suppressed)
		return Conversions.str_to_scalar_enum(response, enums.UplinkChannelType)
