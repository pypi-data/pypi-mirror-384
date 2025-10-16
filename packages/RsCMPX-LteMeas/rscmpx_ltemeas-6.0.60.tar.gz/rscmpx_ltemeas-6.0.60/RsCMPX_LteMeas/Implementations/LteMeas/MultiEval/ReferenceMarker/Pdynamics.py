from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions
from .....Internal.ArgSingleSuppressed import ArgSingleSuppressed
from .....Internal.Types import DataType
from .....Internal.ArgSingleList import ArgSingleList
from .....Internal.ArgSingle import ArgSingle
from ..... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class PdynamicsCls:
	"""Pdynamics commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("pdynamics", core, parent)

	def fetch(self, xvalue: float or bool, trace_select: enums.TraceSelect) -> float:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:REFMarker:PDYNamics \n
		Snippet: value: float = driver.lteMeas.multiEval.referenceMarker.pdynamics.fetch(xvalue = 1.0, trace_select = enums.TraceSelect.AVERage) \n
		Uses the reference marker on the power dynamics trace. \n
		Suppressed linked return values: reliability \n
			:param xvalue: (float or boolean) Absolute x-value of the marker position
			:param trace_select: No help available
			:return: yvalue: Absolute y-value of the marker position"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('xvalue', xvalue, DataType.FloatExt), ArgSingle('trace_select', trace_select, DataType.Enum, enums.TraceSelect))
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_str_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:REFMarker:PDYNamics? {param}'.rstrip(), suppressed)
		return Conversions.str_to_float(response)
