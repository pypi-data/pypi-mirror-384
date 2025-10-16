from typing import List

from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal.Types import DataType
from ......Internal.StructBase import StructBase
from ......Internal.ArgStruct import ArgStruct
from ......Internal.RepeatedCapability import RepeatedCapability
from ...... import enums
from ...... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class CcCls:
	"""Cc commands group definition. 2 total commands, 0 Subgroups, 2 group commands
	Repeated Capability: CarrierComponent, default value after init: CarrierComponent.Nr1"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("cc", core, parent)
		self._cmd_group.rep_cap = RepeatedCapability(self._cmd_group.group_name, 'repcap_carrierComponent_get', 'repcap_carrierComponent_set', repcap.CarrierComponent.Nr1)

	def repcap_carrierComponent_set(self, carrierComponent: repcap.CarrierComponent) -> None:
		"""Repeated Capability default value numeric suffix.
		This value is used, if you do not explicitely set it in the child set/get methods, or if you leave it to CarrierComponent.Default.
		Default value after init: CarrierComponent.Nr1"""
		self._cmd_group.set_repcap_enum_value(carrierComponent)

	def repcap_carrierComponent_get(self) -> repcap.CarrierComponent:
		"""Returns the current default repeated capability for the child set/get methods"""
		# noinspection PyTypeChecker
		return self._cmd_group.get_repcap_enum_value()

	# noinspection PyTypeChecker
	class ResultData(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Channel_Type: List[enums.RbTableChannelType]: PUSCh / PUCCH: for UL slot with RB allocation PSSCh / PSCCh / PSBCh: for SL subframe with RB allocation NONE: UL slot or SL subframe contains no allocated RBs. DL: DL slot (only for TDD UL measurements) SSUB: part of special SF (only for TDD UL measurements)
			- 3 Offset_Rb: List[int]: Offset of first allocated RB for the given channel type
			- 4 No_Rb: List[int]: Number of allocated RBs for the given channel type"""
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

	def read(self, carrierComponent=repcap.CarrierComponent.Default) -> ResultData:
		"""READ:LTE:MEASurement<Instance>:MEValuation:TRACe:RBATable:CC<Nr> \n
		Snippet: value: ResultData = driver.lteMeas.multiEval.trace.rbaTable.cc.read(carrierComponent = repcap.CarrierComponent.Default) \n
		Returns the information of the CC<no> RB allocation table. See also 'Square RB Allocation Table'. For uplink measurements,
		there are three results per captured slot (n = number of captured subframes) : <Reliability>, {<ChannelType>, <OffsetRB>,
		<NoRB>}slot 1, ..., {...}slot (n*2) For sidelink measurements, there are six results per captured subframe (SF) , three
		for the PSCCH and three for the PSSCH: <Reliability>, {...}SF 1 (PSCCH) , {...}SF 1 (PSSCH) , ..., {...}SF n (PSCCH) , {..
		.}SF n (PSSCH) \n
			:param carrierComponent: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Cc')
			:return: structure: for return value, see the help for ResultData structure arguments."""
		carrierComponent_cmd_val = self._cmd_group.get_repcap_cmd_value(carrierComponent, repcap.CarrierComponent)
		return self._core.io.query_struct(f'READ:LTE:MEASurement<Instance>:MEValuation:TRACe:RBATable:CC{carrierComponent_cmd_val}?', self.__class__.ResultData())

	def fetch(self, carrierComponent=repcap.CarrierComponent.Default) -> ResultData:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:TRACe:RBATable:CC<Nr> \n
		Snippet: value: ResultData = driver.lteMeas.multiEval.trace.rbaTable.cc.fetch(carrierComponent = repcap.CarrierComponent.Default) \n
		Returns the information of the CC<no> RB allocation table. See also 'Square RB Allocation Table'. For uplink measurements,
		there are three results per captured slot (n = number of captured subframes) : <Reliability>, {<ChannelType>, <OffsetRB>,
		<NoRB>}slot 1, ..., {...}slot (n*2) For sidelink measurements, there are six results per captured subframe (SF) , three
		for the PSCCH and three for the PSSCH: <Reliability>, {...}SF 1 (PSCCH) , {...}SF 1 (PSSCH) , ..., {...}SF n (PSCCH) , {..
		.}SF n (PSSCH) \n
			:param carrierComponent: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Cc')
			:return: structure: for return value, see the help for ResultData structure arguments."""
		carrierComponent_cmd_val = self._cmd_group.get_repcap_cmd_value(carrierComponent, repcap.CarrierComponent)
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:TRACe:RBATable:CC{carrierComponent_cmd_val}?', self.__class__.ResultData())

	def clone(self) -> 'CcCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = CcCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
