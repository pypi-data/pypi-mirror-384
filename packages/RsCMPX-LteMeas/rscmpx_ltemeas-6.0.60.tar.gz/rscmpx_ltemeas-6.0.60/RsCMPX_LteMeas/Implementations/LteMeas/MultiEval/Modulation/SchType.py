from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions
from .....Internal.ArgSingleSuppressed import ArgSingleSuppressed
from .....Internal.Types import DataType
from ..... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SchTypeCls:
	"""SchType commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("schType", core, parent)

	# noinspection PyTypeChecker
	def fetch(self) -> enums.SidelinkChannelType:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:MODulation:SCHType \n
		Snippet: value: enums.SidelinkChannelType = driver.lteMeas.multiEval.modulation.schType.fetch() \n
		Returns the sidelink channel type evaluated for modulation results. \n
		Suppressed linked return values: reliability \n
			:return: channel_type: No help available"""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_str_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:MODulation:SCHType?', suppressed)
		return Conversions.str_to_scalar_enum(response, enums.SidelinkChannelType)
