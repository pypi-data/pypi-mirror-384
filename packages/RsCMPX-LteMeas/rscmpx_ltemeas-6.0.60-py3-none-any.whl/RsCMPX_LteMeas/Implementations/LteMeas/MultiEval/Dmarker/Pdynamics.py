from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions
from .....Internal.ArgSingleSuppressed import ArgSingleSuppressed
from .....Internal.Types import DataType
from .....Internal.ArgSingleList import ArgSingleList
from .....Internal.ArgSingle import ArgSingle
from ..... import enums
from ..... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class PdynamicsCls:
	"""Pdynamics commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("pdynamics", core, parent)

	def fetch(self, xvalue: float or bool, trace_select: enums.TraceSelect, deltaMarker=repcap.DeltaMarker.Default) -> float:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:DMARker<No>:PDYNamics \n
		Snippet: value: float = driver.lteMeas.multiEval.dmarker.pdynamics.fetch(xvalue = 1.0, trace_select = enums.TraceSelect.AVERage, deltaMarker = repcap.DeltaMarker.Default) \n
		Uses the markers 1 and 2 with relative values on the power dynamics trace. \n
		Suppressed linked return values: reliability \n
			:param xvalue: (float or boolean) X-value of the marker position relative to the x-value of the reference marker
			:param trace_select: No help available
			:param deltaMarker: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Dmarker')
			:return: yvalue: Y-value of the marker position relative to the y-value of the reference marker"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('xvalue', xvalue, DataType.FloatExt), ArgSingle('trace_select', trace_select, DataType.Enum, enums.TraceSelect))
		deltaMarker_cmd_val = self._cmd_group.get_repcap_cmd_value(deltaMarker, repcap.DeltaMarker)
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_str_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:DMARker{deltaMarker_cmd_val}:PDYNamics? {param}'.rstrip(), suppressed)
		return Conversions.str_to_float(response)
