from typing import List

from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.Types import DataType
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct
from .......Internal.RepeatedCapability import RepeatedCapability
from ....... import enums
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SccCls:
	"""Scc commands group definition. 2 total commands, 0 Subgroups, 2 group commands
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

	# noinspection PyTypeChecker
	class ResultData(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: No parameter help available
			- 2 Channel_Type: List[enums.RbTableChannelType]: No parameter help available
			- 3 Offset_Rb: List[int]: No parameter help available
			- 4 No_Rb: List[int]: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct('Channel_Type', DataType.EnumList, enums.RbTableChannelType, False, True, 1),
			ArgStruct('Offset_Rb', DataType.IntegerList, None, False, True, 1),
			ArgStruct('No_Rb', DataType.IntegerList, None, False, True, 1)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Channel_Type: List[enums.RbTableChannelType] = None
			self.Offset_Rb: List[int] = None
			self.No_Rb: List[int] = None

	def read(self, secondaryCC=repcap.SecondaryCC.Default) -> ResultData:
		"""READ:LTE:MEASurement<Instance>:MEValuation:TRACe:RBATable:ULCA:SCC<Nr> \n
		Snippet: value: ResultData = driver.lteMeas.multiEval.trace.rbaTable.ulca.scc.read(secondaryCC = repcap.SecondaryCC.Default) \n
		No command help available \n
			:param secondaryCC: optional repeated capability selector. Default value: CC1 (settable in the interface 'Scc')
			:return: structure: for return value, see the help for ResultData structure arguments."""
		secondaryCC_cmd_val = self._cmd_group.get_repcap_cmd_value(secondaryCC, repcap.SecondaryCC)
		return self._core.io.query_struct(f'READ:LTE:MEASurement<Instance>:MEValuation:TRACe:RBATable:ULCA:SCC{secondaryCC_cmd_val}?', self.__class__.ResultData())

	def fetch(self, secondaryCC=repcap.SecondaryCC.Default) -> ResultData:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:TRACe:RBATable:ULCA:SCC<Nr> \n
		Snippet: value: ResultData = driver.lteMeas.multiEval.trace.rbaTable.ulca.scc.fetch(secondaryCC = repcap.SecondaryCC.Default) \n
		No command help available \n
			:param secondaryCC: optional repeated capability selector. Default value: CC1 (settable in the interface 'Scc')
			:return: structure: for return value, see the help for ResultData structure arguments."""
		secondaryCC_cmd_val = self._cmd_group.get_repcap_cmd_value(secondaryCC, repcap.SecondaryCC)
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:TRACe:RBATable:ULCA:SCC{secondaryCC_cmd_val}?', self.__class__.ResultData())

	def clone(self) -> 'SccCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = SccCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
