from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct
from ....... import enums
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SetupCls:
	"""Setup commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("setup", core, parent)

	# noinspection PyTypeChecker
	class SetupStruct(StructBase):
		"""Structure for setting input parameters. Contains optional setting parameters. Fields: \n
			- Segment_Length: int: Number of subframes in the segment
			- Level: float: Expected nominal power in the segment. The range can be calculated as follows: Range (Expected Nominal Power) = Range (Input Power) + External Attenuation - User Margin The input power range is stated in the specifications document.
			- Duplex_Mode: enums.Mode: Duplex mode used in the segment
			- Band: enums.Band: TDD UL: OB33 | ... | OB45 | OB48 | OB50 | ... | OB53 | OB250 Sidelink: OB47 Operating band used in the segment
			- Frequency: float: Center frequency of CC1 used in the segment For the supported range, see 'Frequency ranges'.
			- Ch_Bandwidth: enums.ChannelBandwidth: Channel bandwidth of CC1 used in the segment. B014: 1.4 MHz B030: 3 MHz B050: 5 MHz B100: 10 MHz B150: 15 MHz B200: 20 MHz
			- Cyclic_Prefix: enums.CyclicPrefix: Type of cyclic prefix used in the segment
			- Channel_Type: enums.SegmentChannelTypeExtended: Channel type to be measured in the segment (AUTO for automatic detection) . Uplink: AUTO, PUSCh, PUCCh Sidelink: PSSCh, PSCCh, PSBCh
			- Retrigger_Flag: enums.RetriggerFlag: Specifies whether the measurement waits for a trigger event before measuring the segment, or not. The retrigger flag is ignored for trigger mode ONCE and evaluated for trigger mode SEGMent, see [CMDLINKRESOLVED Trigger.LteMeas.MultiEval.ListPy#Mode CMDLINKRESOLVED].
				- OFF: Measure the segment without retrigger. For the first segment, the value OFF is interpreted as ON.
				- ON: Wait for a trigger event from the trigger source configured via TRIGger:LTE:MEASi:MEValuation:SOURce.
				- IFPower: Wait for a trigger event from the trigger source IF Power.The trigger evaluation bandwidth is 160 MHz.
				- IFPNarrowband: Wait for a trigger event from the trigger source IF Power.The trigger evaluation bandwidth is configured via TRIGger:LTE:MEASi:MEValuation:LIST:NBANdwidth.
			- Evaluat_Offset: int: Number of subframes at the beginning of the segment that are not evaluated.
			- Network_Sig_Value: enums.NetworkSigValueNoCarrAggr: Optional setting parameter. Network signaled value to be used
			for the segment."""
		__meta_args_list = [
			ArgStruct.scalar_int('Segment_Length'),
			ArgStruct.scalar_float('Level'),
			ArgStruct.scalar_enum('Duplex_Mode', enums.Mode),
			ArgStruct.scalar_enum('Band', enums.Band),
			ArgStruct.scalar_float('Frequency'),
			ArgStruct.scalar_enum('Ch_Bandwidth', enums.ChannelBandwidth),
			ArgStruct.scalar_enum('Cyclic_Prefix', enums.CyclicPrefix),
			ArgStruct.scalar_enum('Channel_Type', enums.SegmentChannelTypeExtended),
			ArgStruct.scalar_enum('Retrigger_Flag', enums.RetriggerFlag),
			ArgStruct.scalar_int('Evaluat_Offset'),
			ArgStruct.scalar_enum_optional('Network_Sig_Value', enums.NetworkSigValueNoCarrAggr)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Segment_Length: int=None
			self.Level: float=None
			self.Duplex_Mode: enums.Mode=None
			self.Band: enums.Band=None
			self.Frequency: float=None
			self.Ch_Bandwidth: enums.ChannelBandwidth=None
			self.Cyclic_Prefix: enums.CyclicPrefix=None
			self.Channel_Type: enums.SegmentChannelTypeExtended=None
			self.Retrigger_Flag: enums.RetriggerFlag=None
			self.Evaluat_Offset: int=None
			self.Network_Sig_Value: enums.NetworkSigValueNoCarrAggr=None

	def set(self, structure: SetupStruct, segment=repcap.Segment.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:SETup \n
		Snippet with structure: \n
		structure = driver.configure.lteMeas.multiEval.listPy.segment.setup.SetupStruct() \n
		structure.Segment_Length: int = 1 \n
		structure.Level: float = 1.0 \n
		structure.Duplex_Mode: enums.Mode = enums.Mode.FDD \n
		structure.Band: enums.Band = enums.Band.OB1 \n
		structure.Frequency: float = 1.0 \n
		structure.Ch_Bandwidth: enums.ChannelBandwidth = enums.ChannelBandwidth.B014 \n
		structure.Cyclic_Prefix: enums.CyclicPrefix = enums.CyclicPrefix.EXTended \n
		structure.Channel_Type: enums.SegmentChannelTypeExtended = enums.SegmentChannelTypeExtended.AUTO \n
		structure.Retrigger_Flag: enums.RetriggerFlag = enums.RetriggerFlag.IFPNarrow \n
		structure.Evaluat_Offset: int = 1 \n
		structure.Network_Sig_Value: enums.NetworkSigValueNoCarrAggr = enums.NetworkSigValueNoCarrAggr.NS01 \n
		driver.configure.lteMeas.multiEval.listPy.segment.setup.set(structure, segment = repcap.Segment.Default) \n
		Defines the length and analyzer settings of segment <no>. Send this command for all segments to be measured (method
		RsCMPX_LteMeas.Configure.LteMeas.MultiEval.ListPy.Lrange.set) . For uplink signals with TDD mode, see also method
		RsCMPX_LteMeas.Configure.LteMeas.MultiEval.ListPy.Segment.Tdd.set. For carrier-specific settings for carrier aggregation,
		see CONFigure:LTE:MEAS<i>:MEValuation:LIST:SEGMent<no>:CC<c>. \n
			:param structure: for set value, see the help for SetupStruct structure arguments.
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
		"""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		self._core.io.write_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:SETup', structure)

	def get(self, segment=repcap.Segment.Default) -> SetupStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:SETup \n
		Snippet: value: SetupStruct = driver.configure.lteMeas.multiEval.listPy.segment.setup.get(segment = repcap.Segment.Default) \n
		Defines the length and analyzer settings of segment <no>. Send this command for all segments to be measured (method
		RsCMPX_LteMeas.Configure.LteMeas.MultiEval.ListPy.Lrange.set) . For uplink signals with TDD mode, see also method
		RsCMPX_LteMeas.Configure.LteMeas.MultiEval.ListPy.Segment.Tdd.set. For carrier-specific settings for carrier aggregation,
		see CONFigure:LTE:MEAS<i>:MEValuation:LIST:SEGMent<no>:CC<c>. \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:return: structure: for return value, see the help for SetupStruct structure arguments."""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:SETup?', self.__class__.SetupStruct())
