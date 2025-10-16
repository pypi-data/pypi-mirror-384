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
class MerrorCls:
	"""Merror commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("merror", core, parent)

	def fetch(self, xvalue: int or bool, trace_select: enums.TraceSelect, absMarker=repcap.AbsMarker.Default) -> float:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:AMARker<No>:MERRor \n
		Snippet: value: float = driver.lteMeas.multiEval.amarker.merror.fetch(xvalue = 1, trace_select = enums.TraceSelect.AVERage, absMarker = repcap.AbsMarker.Default) \n
		Uses the markers 1 and 2 with absolute values on the diagrams: EVM RMS, EVM peak, magnitude error and phase error vs
		SC-FDMA symbol. \n
		Suppressed linked return values: reliability \n
			:param xvalue: (integer or boolean) Absolute x-value of the marker position There are two x-values per SC-FDMA symbol on the x-axis (symbol 0 low, symbol 0 high, ..., symbol 6 low, symbol 6 high) .
			:param trace_select: No help available
			:param absMarker: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Amarker')
			:return: yvalue: Absolute y-value of the marker position"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('xvalue', xvalue, DataType.IntegerExt), ArgSingle('trace_select', trace_select, DataType.Enum, enums.TraceSelect))
		absMarker_cmd_val = self._cmd_group.get_repcap_cmd_value(absMarker, repcap.AbsMarker)
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_str_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:AMARker{absMarker_cmd_val}:MERRor? {param}'.rstrip(), suppressed)
		return Conversions.str_to_float(response)
