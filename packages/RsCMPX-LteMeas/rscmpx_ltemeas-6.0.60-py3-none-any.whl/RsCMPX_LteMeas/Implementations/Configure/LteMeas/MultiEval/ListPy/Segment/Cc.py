from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.Types import DataType
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct
from .......Internal.ArgSingleList import ArgSingleList
from .......Internal.ArgSingle import ArgSingle
from .......Internal.RepeatedCapability import RepeatedCapability
from ....... import enums
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class CcCls:
	"""Cc commands group definition. 1 total commands, 0 Subgroups, 1 group commands
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

	def set(self, frequency: float, ch_bandwidth: enums.ChannelBandwidth, segment=repcap.Segment.Default, carrierComponent=repcap.CarrierComponent.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:CC<c> \n
		Snippet: driver.configure.lteMeas.multiEval.listPy.segment.cc.set(frequency = 1.0, ch_bandwidth = enums.ChannelBandwidth.B014, segment = repcap.Segment.Default, carrierComponent = repcap.CarrierComponent.Default) \n
		Defines carrier-specific analyzer settings for component carrier CC<c>, in segment <no>. This command is only relevant
		for carrier aggregation. \n
			:param frequency: Center frequency of the component carrier For the supported range, see 'Frequency ranges'.
			:param ch_bandwidth: Channel bandwidth of the component carrier B014: 1.4 MHz B030: 3 MHz B050: 5 MHz B100: 10 MHz B150: 15 MHz B200: 20 MHz
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:param carrierComponent: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Cc')
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('frequency', frequency, DataType.Float), ArgSingle('ch_bandwidth', ch_bandwidth, DataType.Enum, enums.ChannelBandwidth))
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		carrierComponent_cmd_val = self._cmd_group.get_repcap_cmd_value(carrierComponent, repcap.CarrierComponent)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:CC{carrierComponent_cmd_val} {param}'.rstrip())

	# noinspection PyTypeChecker
	class CcStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Frequency: float: Center frequency of the component carrier For the supported range, see 'Frequency ranges'.
			- 2 Ch_Bandwidth: enums.ChannelBandwidth: Channel bandwidth of the component carrier B014: 1.4 MHz B030: 3 MHz B050: 5 MHz B100: 10 MHz B150: 15 MHz B200: 20 MHz"""
		__meta_args_list = [
			ArgStruct.scalar_float('Frequency'),
			ArgStruct.scalar_enum('Ch_Bandwidth', enums.ChannelBandwidth)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Frequency: float = None
			self.Ch_Bandwidth: enums.ChannelBandwidth = None

	def get(self, segment=repcap.Segment.Default, carrierComponent=repcap.CarrierComponent.Default) -> CcStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:CC<c> \n
		Snippet: value: CcStruct = driver.configure.lteMeas.multiEval.listPy.segment.cc.get(segment = repcap.Segment.Default, carrierComponent = repcap.CarrierComponent.Default) \n
		Defines carrier-specific analyzer settings for component carrier CC<c>, in segment <no>. This command is only relevant
		for carrier aggregation. \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:param carrierComponent: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Cc')
			:return: structure: for return value, see the help for CcStruct structure arguments."""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		carrierComponent_cmd_val = self._cmd_group.get_repcap_cmd_value(carrierComponent, repcap.CarrierComponent)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:CC{carrierComponent_cmd_val}?', self.__class__.CcStruct())

	def clone(self) -> 'CcCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = CcCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
