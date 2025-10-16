from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions
from .....Internal.ArgSingleSuppressed import ArgSingleSuppressed
from .....Internal.Types import DataType
from ..... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class DmodulationCls:
	"""Dmodulation commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("dmodulation", core, parent)

	# noinspection PyTypeChecker
	def fetch(self) -> enums.Modulation:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:MODulation:DMODulation \n
		Snippet: value: enums.Modulation = driver.lteMeas.multiEval.modulation.dmodulation.fetch() \n
		Returns the detected modulation scheme in the measured slot. If channel type PUCCH is detected, QPSK is returned for the
		modulation scheme because the QPSK limits are applied in that case. \n
		Suppressed linked return values: reliability \n
			:return: modulation: QPSK, 16QAM, 64QAM, 256QAM"""
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_str_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:MODulation:DMODulation?', suppressed)
		return Conversions.str_to_scalar_enum(response, enums.Modulation)
