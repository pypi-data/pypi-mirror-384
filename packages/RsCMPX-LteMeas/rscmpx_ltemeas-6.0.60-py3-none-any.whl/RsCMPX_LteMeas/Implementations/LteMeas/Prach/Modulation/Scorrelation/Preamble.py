from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal import Conversions
from ......Internal.ArgSingleSuppressed import ArgSingleSuppressed
from ......Internal.Types import DataType
from ......Internal.RepeatedCapability import RepeatedCapability
from ...... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class PreambleCls:
	"""Preamble commands group definition. 1 total commands, 0 Subgroups, 1 group commands
	Repeated Capability: Preamble, default value after init: Preamble.Nr1"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("preamble", core, parent)
		self._cmd_group.rep_cap = RepeatedCapability(self._cmd_group.group_name, 'repcap_preamble_get', 'repcap_preamble_set', repcap.Preamble.Nr1)

	def repcap_preamble_set(self, preamble: repcap.Preamble) -> None:
		"""Repeated Capability default value numeric suffix.
		This value is used, if you do not explicitely set it in the child set/get methods, or if you leave it to Preamble.Default.
		Default value after init: Preamble.Nr1"""
		self._cmd_group.set_repcap_enum_value(preamble)

	def repcap_preamble_get(self) -> repcap.Preamble:
		"""Returns the current default repeated capability for the child set/get methods"""
		# noinspection PyTypeChecker
		return self._cmd_group.get_repcap_enum_value()

	def fetch(self, preamble=repcap.Preamble.Default) -> float:
		"""FETCh:LTE:MEASurement<Instance>:PRACh:MODulation:SCORrelation:PREamble<Number> \n
		Snippet: value: float = driver.lteMeas.prach.modulation.scorrelation.preamble.fetch(preamble = repcap.Preamble.Default) \n
		Returns the sequence correlation for a selected preamble of multi-preamble measurements. It indicates the correlation
		between the ideal preamble sequence determined from the parameter settings and the measured preamble sequence. A value of
		1 corresponds to perfect correlation. A value close to 0 indicates that the preamble sequence was not found. \n
		Suppressed linked return values: reliability \n
			:param preamble: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Preamble')
			:return: seq_correlation: Sequence correlation"""
		preamble_cmd_val = self._cmd_group.get_repcap_cmd_value(preamble, repcap.Preamble)
		suppressed = ArgSingleSuppressed(0, DataType.Integer, False, 1, 'Reliability')
		response = self._core.io.query_str_suppressed(f'FETCh:LTE:MEASurement<Instance>:PRACh:MODulation:SCORrelation:PREamble{preamble_cmd_val}?', suppressed)
		return Conversions.str_to_float(response)

	def clone(self) -> 'PreambleCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = PreambleCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
