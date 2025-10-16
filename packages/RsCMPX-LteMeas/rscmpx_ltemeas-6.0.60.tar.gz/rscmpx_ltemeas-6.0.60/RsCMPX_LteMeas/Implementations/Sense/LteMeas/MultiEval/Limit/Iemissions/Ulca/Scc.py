from typing import List

from ........Internal.Core import Core
from ........Internal.CommandsGroup import CommandsGroup
from ........Internal.RepeatedCapability import RepeatedCapability
from ........ import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SccCls:
	"""Scc commands group definition. 1 total commands, 0 Subgroups, 1 group commands
	Repeated Capability: SecondaryCC, default value after init: SecondaryCC.CC1"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("scc", core, parent)
		self._cmd_group.rep_cap = RepeatedCapability(self._cmd_group.group_name, 'repcap_secondaryCC_get', 'repcap_secondaryCC_set', repcap.SecondaryCC.CC1)

	def repcap_secondaryCC_set(self, secondaryCC: repcap.SecondaryCC) -> None:
		"""Repeated Capability default value numeric suffix.
		This value is used, if you do not explicitely set it in the child set/get methods, or if you leave it to SecondaryCC.Default.
		Default value after init: SecondaryCC.CC1"""
		self._cmd_group.set_repcap_enum_value(secondaryCC)

	def repcap_secondaryCC_get(self) -> repcap.SecondaryCC:
		"""Returns the current default repeated capability for the child set/get methods"""
		# noinspection PyTypeChecker
		return self._cmd_group.get_repcap_enum_value()

	def get(self, secondaryCC=repcap.SecondaryCC.Default) -> List[float]:
		"""SENSe:LTE:MEASurement<Instance>:MEValuation:LIMit:IEMissions:ULCA:SCC<Nr> \n
		Snippet: value: List[float] = driver.sense.lteMeas.multiEval.limit.iemissions.ulca.scc.get(secondaryCC = repcap.SecondaryCC.Default) \n
		No command help available \n
			:param secondaryCC: optional repeated capability selector. Default value: CC1 (settable in the interface 'Scc')
			:return: power: No help available"""
		secondaryCC_cmd_val = self._cmd_group.get_repcap_cmd_value(secondaryCC, repcap.SecondaryCC)
		response = self._core.io.query_bin_or_ascii_float_list(f'SENSe:LTE:MEASurement<Instance>:MEValuation:LIMit:IEMissions:ULCA:SCC{secondaryCC_cmd_val}?')
		return response

	def clone(self) -> 'SccCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = SccCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
