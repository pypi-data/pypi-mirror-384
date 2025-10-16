from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal import Conversions
from ......Internal.ArgSingleSuppressed import ArgSingleSuppressed
from ......Internal.Types import DataType
from ......Internal.ArgSingleList import ArgSingleList
from ......Internal.ArgSingle import ArgSingle
from ...... import enums
from ...... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class EvMagnitudeCls:
	"""EvMagnitude commands group definition. 2 total commands, 1 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("evMagnitude", core, parent)

	@property
	def peak(self):
		"""peak commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_peak'):
			from .Peak import PeakCls
			self._peak = PeakCls(self._core, self._cmd_group)
		return self._peak

	def fetch(self, xvalue: int or bool, trace_select: enums.TraceSelect, deltaMarker=repcap.DeltaMarker.Default) -> float:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:DMARker<No>:EVMagnitude \n
		Snippet: value: float = driver.lteMeas.multiEval.dmarker.evMagnitude.fetch(xvalue = 1, trace_select = enums.TraceSelect.AVERage, deltaMarker = repcap.DeltaMarker.Default) \n
		Uses the markers 1 and 2 with relative values on the diagrams: EVM RMS, EVM peak, magnitude error and phase error vs
		SC-FDMA symbol. \n
		Suppressed linked return values: reliability \n
			:param xvalue: (integer or boolean) X-value of the marker position relative to the x-value of the reference marker There are two x-values per SC-FDMA symbol on the x-axis (symbol 0 low, symbol 0 high, ..., symbol 6 low, symbol 6 high) .
			:param trace_select: No help available
			:param deltaMarker: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Dmarker')
			:return: yvalue: Y-value of the marker position relative to the y-value of the reference marker"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('xvalue', xvalue, DataType.IntegerExt), ArgSingle('trace_select', trace_select, DataType.Enum, enums.TraceSelect))
		deltaMarker_cmd_val = self._cmd_group.get_repcap_cmd_value(deltaMarker, repcap.DeltaMarker)
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_str_suppressed(f'FETCh:LTE:MEASurement<Instance>:MEValuation:DMARker{deltaMarker_cmd_val}:EVMagnitude? {param}'.rstrip(), suppressed)
		return Conversions.str_to_float(response)

	def clone(self) -> 'EvMagnitudeCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = EvMagnitudeCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
