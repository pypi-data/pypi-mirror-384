from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions
from ..... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class MultiEvalCls:
	"""MultiEval commands group definition. 141 total commands, 17 Subgroups, 19 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("multiEval", core, parent)

	@property
	def listPy(self):
		"""listPy commands group. 3 Sub-classes, 5 commands."""
		if not hasattr(self, '_listPy'):
			from .ListPy import ListPyCls
			self._listPy = ListPyCls(self._core, self._cmd_group)
		return self._listPy

	@property
	def tmode(self):
		"""tmode commands group. 0 Sub-classes, 3 commands."""
		if not hasattr(self, '_tmode'):
			from .Tmode import TmodeCls
			self._tmode = TmodeCls(self._core, self._cmd_group)
		return self._tmode

	@property
	def pcc(self):
		"""pcc commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_pcc'):
			from .Pcc import PccCls
			self._pcc = PccCls(self._core, self._cmd_group)
		return self._pcc

	@property
	def scc(self):
		"""scc commands group. 1 Sub-classes, 0 commands."""
		if not hasattr(self, '_scc'):
			from .Scc import SccCls
			self._scc = SccCls(self._core, self._cmd_group)
		return self._scc

	@property
	def cc(self):
		"""cc commands group. 1 Sub-classes, 0 commands."""
		if not hasattr(self, '_cc'):
			from .Cc import CcCls
			self._cc = CcCls(self._core, self._cmd_group)
		return self._cc

	@property
	def nsValue(self):
		"""nsValue commands group. 0 Sub-classes, 2 commands."""
		if not hasattr(self, '_nsValue'):
			from .NsValue import NsValueCls
			self._nsValue = NsValueCls(self._core, self._cmd_group)
		return self._nsValue

	@property
	def srs(self):
		"""srs commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_srs'):
			from .Srs import SrsCls
			self._srs = SrsCls(self._core, self._cmd_group)
		return self._srs

	@property
	def modulation(self):
		"""modulation commands group. 3 Sub-classes, 3 commands."""
		if not hasattr(self, '_modulation'):
			from .Modulation import ModulationCls
			self._modulation = ModulationCls(self._core, self._cmd_group)
		return self._modulation

	@property
	def spectrum(self):
		"""spectrum commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_spectrum'):
			from .Spectrum import SpectrumCls
			self._spectrum = SpectrumCls(self._core, self._cmd_group)
		return self._spectrum

	@property
	def rbAllocation(self):
		"""rbAllocation commands group. 3 Sub-classes, 1 commands."""
		if not hasattr(self, '_rbAllocation'):
			from .RbAllocation import RbAllocationCls
			self._rbAllocation = RbAllocationCls(self._core, self._cmd_group)
		return self._rbAllocation

	@property
	def power(self):
		"""power commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_power'):
			from .Power import PowerCls
			self._power = PowerCls(self._core, self._cmd_group)
		return self._power

	@property
	def pdynamics(self):
		"""pdynamics commands group. 1 Sub-classes, 1 commands."""
		if not hasattr(self, '_pdynamics'):
			from .Pdynamics import PdynamicsCls
			self._pdynamics = PdynamicsCls(self._core, self._cmd_group)
		return self._pdynamics

	@property
	def msubFrames(self):
		"""msubFrames commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_msubFrames'):
			from .MsubFrames import MsubFramesCls
			self._msubFrames = MsubFramesCls(self._core, self._cmd_group)
		return self._msubFrames

	@property
	def scount(self):
		"""scount commands group. 1 Sub-classes, 2 commands."""
		if not hasattr(self, '_scount'):
			from .Scount import ScountCls
			self._scount = ScountCls(self._core, self._cmd_group)
		return self._scount

	@property
	def result(self):
		"""result commands group. 1 Sub-classes, 14 commands."""
		if not hasattr(self, '_result'):
			from .Result import ResultCls
			self._result = ResultCls(self._core, self._cmd_group)
		return self._result

	@property
	def limit(self):
		"""limit commands group. 5 Sub-classes, 0 commands."""
		if not hasattr(self, '_limit'):
			from .Limit import LimitCls
			self._limit = LimitCls(self._core, self._cmd_group)
		return self._limit

	@property
	def bler(self):
		"""bler commands group. 1 Sub-classes, 0 commands."""
		if not hasattr(self, '_bler'):
			from .Bler import BlerCls
			self._bler = BlerCls(self._core, self._cmd_group)
		return self._bler

	def get_timeout(self) -> float:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:TOUT \n
		Snippet: value: float = driver.configure.lteMeas.multiEval.get_timeout() \n
		Defines a timeout for the measurement. The timer is started when the measurement is initiated via a READ or INIT command.
		It is not started if the measurement is initiated manually. When the measurement has completed the first measurement
		cycle (first single shot) , the statistical depth is reached and the timer is reset. If the first measurement cycle has
		not been completed when the timer expires, the measurement is stopped. The measurement state changes to RDY.
		The reliability indicator is set to 1, indicating that a measurement timeout occurred. Still running READ, FETCh or
		CALCulate commands are completed, returning the available results. At least for some results, there are no values at all
		or the statistical depth has not been reached. A timeout of 0 s corresponds to an infinite measurement timeout. \n
			:return: timeout: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:TOUT?')
		return Conversions.str_to_float(response)

	def set_timeout(self, timeout: float) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:TOUT \n
		Snippet: driver.configure.lteMeas.multiEval.set_timeout(timeout = 1.0) \n
		Defines a timeout for the measurement. The timer is started when the measurement is initiated via a READ or INIT command.
		It is not started if the measurement is initiated manually. When the measurement has completed the first measurement
		cycle (first single shot) , the statistical depth is reached and the timer is reset. If the first measurement cycle has
		not been completed when the timer expires, the measurement is stopped. The measurement state changes to RDY.
		The reliability indicator is set to 1, indicating that a measurement timeout occurred. Still running READ, FETCh or
		CALCulate commands are completed, returning the available results. At least for some results, there are no values at all
		or the statistical depth has not been reached. A timeout of 0 s corresponds to an infinite measurement timeout. \n
			:param timeout: No help available
		"""
		param = Conversions.decimal_value_to_str(timeout)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:TOUT {param}')

	# noinspection PyTypeChecker
	def get_mmode(self) -> enums.MeasurementMode:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:MMODe \n
		Snippet: value: enums.MeasurementMode = driver.configure.lteMeas.multiEval.get_mmode() \n
		Selects the measurement mode. \n
			:return: measurement_mode: NORMal: normal mode TMODe: TPC mode MELMode: multi-evaluation list mode
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:MMODe?')
		return Conversions.str_to_scalar_enum(response, enums.MeasurementMode)

	def set_mmode(self, measurement_mode: enums.MeasurementMode) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:MMODe \n
		Snippet: driver.configure.lteMeas.multiEval.set_mmode(measurement_mode = enums.MeasurementMode.MELMode) \n
		Selects the measurement mode. \n
			:param measurement_mode: NORMal: normal mode TMODe: TPC mode MELMode: multi-evaluation list mode
		"""
		param = Conversions.enum_scalar_to_str(measurement_mode, enums.MeasurementMode)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:MMODe {param}')

	# noinspection PyTypeChecker
	def get_repetition(self) -> enums.Repeat:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:REPetition \n
		Snippet: value: enums.Repeat = driver.configure.lteMeas.multiEval.get_repetition() \n
		Specifies the repetition mode of the measurement. The repetition mode specifies whether the measurement is stopped after
		a single shot or repeated continuously. Use the CONFigure:...:MEAS<i>:...:SCOunt commands to specify the number of
		measurement intervals per single shot. \n
			:return: repetition: SINGleshot: Single-shot measurement CONTinuous: Continuous measurement
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:REPetition?')
		return Conversions.str_to_scalar_enum(response, enums.Repeat)

	def set_repetition(self, repetition: enums.Repeat) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:REPetition \n
		Snippet: driver.configure.lteMeas.multiEval.set_repetition(repetition = enums.Repeat.CONTinuous) \n
		Specifies the repetition mode of the measurement. The repetition mode specifies whether the measurement is stopped after
		a single shot or repeated continuously. Use the CONFigure:...:MEAS<i>:...:SCOunt commands to specify the number of
		measurement intervals per single shot. \n
			:param repetition: SINGleshot: Single-shot measurement CONTinuous: Continuous measurement
		"""
		param = Conversions.enum_scalar_to_str(repetition, enums.Repeat)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:REPetition {param}')

	# noinspection PyTypeChecker
	def get_scondition(self) -> enums.StopCondition:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SCONdition \n
		Snippet: value: enums.StopCondition = driver.configure.lteMeas.multiEval.get_scondition() \n
		Qualifies whether the measurement is stopped after a failed limit check or continued. With SLFail, the measurement is
		stopped and reaches the RDY state when one of the results exceeds the limits. \n
			:return: stop_condition: NONE: Continue measurement irrespective of the limit check. SLFail: Stop measurement on limit failure.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:SCONdition?')
		return Conversions.str_to_scalar_enum(response, enums.StopCondition)

	def set_scondition(self, stop_condition: enums.StopCondition) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SCONdition \n
		Snippet: driver.configure.lteMeas.multiEval.set_scondition(stop_condition = enums.StopCondition.NONE) \n
		Qualifies whether the measurement is stopped after a failed limit check or continued. With SLFail, the measurement is
		stopped and reaches the RDY state when one of the results exceeds the limits. \n
			:param stop_condition: NONE: Continue measurement irrespective of the limit check. SLFail: Stop measurement on limit failure.
		"""
		param = Conversions.enum_scalar_to_str(stop_condition, enums.StopCondition)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:SCONdition {param}')

	def get_ul_dl(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:ULDL \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.get_ul_dl() \n
		Selects an UL-DL configuration, defining the combination of uplink, downlink and special subframes within a radio frame.
		This parameter is only relevant for frame structure Type 2 (method RsCMPX_LteMeas.Configure.LteMeas.fstructure) .
		The UL-DL configurations are defined in 3GPP TS 36.211, section 4 'Frame Structure'. \n
			:return: uplink_downlink: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:ULDL?')
		return Conversions.str_to_int(response)

	def set_ul_dl(self, uplink_downlink: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:ULDL \n
		Snippet: driver.configure.lteMeas.multiEval.set_ul_dl(uplink_downlink = 1) \n
		Selects an UL-DL configuration, defining the combination of uplink, downlink and special subframes within a radio frame.
		This parameter is only relevant for frame structure Type 2 (method RsCMPX_LteMeas.Configure.LteMeas.fstructure) .
		The UL-DL configurations are defined in 3GPP TS 36.211, section 4 'Frame Structure'. \n
			:param uplink_downlink: No help available
		"""
		param = Conversions.decimal_value_to_str(uplink_downlink)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:ULDL {param}')

	def get_ssubframe(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SSUBframe \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.get_ssubframe() \n
		Selects a special subframe configuration, defining the inner structure of special subframes. This parameter is only
		relevant for frame structure Type 2 (method RsCMPX_LteMeas.Configure.LteMeas.fstructure) . The special subframe
		configurations are defined in 3GPP TS 36.211, section 4 'Frame Structure'. \n
			:return: special_subframe: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:SSUBframe?')
		return Conversions.str_to_int(response)

	def set_ssubframe(self, special_subframe: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SSUBframe \n
		Snippet: driver.configure.lteMeas.multiEval.set_ssubframe(special_subframe = 1) \n
		Selects a special subframe configuration, defining the inner structure of special subframes. This parameter is only
		relevant for frame structure Type 2 (method RsCMPX_LteMeas.Configure.LteMeas.fstructure) . The special subframe
		configurations are defined in 3GPP TS 36.211, section 4 'Frame Structure'. \n
			:param special_subframe: No help available
		"""
		param = Conversions.decimal_value_to_str(special_subframe)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:SSUBframe {param}')

	def get_mo_exception(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:MOEXception \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.get_mo_exception() \n
		Specifies whether measurement results identified as faulty or inaccurate are rejected. \n
			:return: meas_on_exception: OFF: Faulty results are rejected. ON: Results are never rejected.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:MOEXception?')
		return Conversions.str_to_bool(response)

	def set_mo_exception(self, meas_on_exception: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:MOEXception \n
		Snippet: driver.configure.lteMeas.multiEval.set_mo_exception(meas_on_exception = False) \n
		Specifies whether measurement results identified as faulty or inaccurate are rejected. \n
			:param meas_on_exception: OFF: Faulty results are rejected. ON: Results are never rejected.
		"""
		param = Conversions.bool_to_str(meas_on_exception)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:MOEXception {param}')

	# noinspection PyTypeChecker
	def get_cprefix(self) -> enums.CyclicPrefix:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:CPRefix \n
		Snippet: value: enums.CyclicPrefix = driver.configure.lteMeas.multiEval.get_cprefix() \n
		Selects the type of cyclic prefix of the LTE signal. For Signal Path = Network, the setting is not configurable. \n
			:return: cyclic_prefix: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:CPRefix?')
		return Conversions.str_to_scalar_enum(response, enums.CyclicPrefix)

	def set_cprefix(self, cyclic_prefix: enums.CyclicPrefix) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:CPRefix \n
		Snippet: driver.configure.lteMeas.multiEval.set_cprefix(cyclic_prefix = enums.CyclicPrefix.EXTended) \n
		Selects the type of cyclic prefix of the LTE signal. For Signal Path = Network, the setting is not configurable. \n
			:param cyclic_prefix: No help available
		"""
		param = Conversions.enum_scalar_to_str(cyclic_prefix, enums.CyclicPrefix)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:CPRefix {param}')

	# noinspection PyTypeChecker
	def get_ctype(self) -> enums.ChannelTypeDetection:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:CTYPe \n
		Snippet: value: enums.ChannelTypeDetection = driver.configure.lteMeas.multiEval.get_ctype() \n
		Configures the channel type detection for uplink measurements. \n
			:return: channel_type: Automatic detection of channel type or manual selection
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:CTYPe?')
		return Conversions.str_to_scalar_enum(response, enums.ChannelTypeDetection)

	def set_ctype(self, channel_type: enums.ChannelTypeDetection) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:CTYPe \n
		Snippet: driver.configure.lteMeas.multiEval.set_ctype(channel_type = enums.ChannelTypeDetection.AUTO) \n
		Configures the channel type detection for uplink measurements. \n
			:param channel_type: Automatic detection of channel type or manual selection
		"""
		param = Conversions.enum_scalar_to_str(channel_type, enums.ChannelTypeDetection)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:CTYPe {param}')

	# noinspection PyTypeChecker
	def get_sch_type(self) -> enums.SidelinkChannelType:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SCTYpe \n
		Snippet: value: enums.SidelinkChannelType = driver.configure.lteMeas.multiEval.get_sch_type() \n
		Configures the channel type for modulation results of sidelink measurements. \n
			:return: channel_type: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:SCTYpe?')
		return Conversions.str_to_scalar_enum(response, enums.SidelinkChannelType)

	def set_sch_type(self, channel_type: enums.SidelinkChannelType) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SCTYpe \n
		Snippet: driver.configure.lteMeas.multiEval.set_sch_type(channel_type = enums.SidelinkChannelType.PSBCh) \n
		Configures the channel type for modulation results of sidelink measurements. \n
			:param channel_type: No help available
		"""
		param = Conversions.enum_scalar_to_str(channel_type, enums.SidelinkChannelType)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:SCTYpe {param}')

	def get_peak_search(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:PSEarch \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.get_peak_search() \n
		No command help available \n
			:return: pucch_search: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:PSEarch?')
		return Conversions.str_to_bool(response)

	def set_peak_search(self, pucch_search: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:PSEarch \n
		Snippet: driver.configure.lteMeas.multiEval.set_peak_search(pucch_search = False) \n
		No command help available \n
			:param pucch_search: No help available
		"""
		param = Conversions.bool_to_str(pucch_search)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:PSEarch {param}')

	# noinspection PyTypeChecker
	def get_pformat(self) -> enums.PucchFormat:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:PFORmat \n
		Snippet: value: enums.PucchFormat = driver.configure.lteMeas.multiEval.get_pformat() \n
		Specifies the PUCCH format (only relevant for signals containing a PUCCH) . The formats are defined in 3GPP TS 36.211. \n
			:return: pucch_format: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:PFORmat?')
		return Conversions.str_to_scalar_enum(response, enums.PucchFormat)

	def set_pformat(self, pucch_format: enums.PucchFormat) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:PFORmat \n
		Snippet: driver.configure.lteMeas.multiEval.set_pformat(pucch_format = enums.PucchFormat.F1) \n
		Specifies the PUCCH format (only relevant for signals containing a PUCCH) . The formats are defined in 3GPP TS 36.211. \n
			:param pucch_format: No help available
		"""
		param = Conversions.enum_scalar_to_str(pucch_format, enums.PucchFormat)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:PFORmat {param}')

	def get_nvfilter(self) -> int or bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:NVFilter \n
		Snippet: value: int or bool = driver.configure.lteMeas.multiEval.get_nvfilter() \n
		Specifies, enables or disables the number of resource blocks (NRB) view filter. If the filter is active, only slots with
		a matching number of allocated resource blocks are measured. Within the indicated input range, only specific numbers are
		allowed as defined in 3GPP TS 36.211. For details, see 'Resources in time and frequency domain'. \n
			:return: nrb_view_filter: (integer or boolean) Number of allocated resource blocks
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:NVFilter?')
		return Conversions.str_to_int_or_bool(response)

	def set_nvfilter(self, nrb_view_filter: int or bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:NVFilter \n
		Snippet: driver.configure.lteMeas.multiEval.set_nvfilter(nrb_view_filter = 1) \n
		Specifies, enables or disables the number of resource blocks (NRB) view filter. If the filter is active, only slots with
		a matching number of allocated resource blocks are measured. Within the indicated input range, only specific numbers are
		allowed as defined in 3GPP TS 36.211. For details, see 'Resources in time and frequency domain'. \n
			:param nrb_view_filter: (integer or boolean) Number of allocated resource blocks
		"""
		param = Conversions.decimal_or_bool_value_to_str(nrb_view_filter)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:NVFilter {param}')

	def get_orv_filter(self) -> int or bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:ORVFilter \n
		Snippet: value: int or bool = driver.configure.lteMeas.multiEval.get_orv_filter() \n
		Specifies, enables or disables the RB offset view filter. If the filter is active, only slots with a matching number of
		RB offset are measured. The indicated input range applies to a 20-MHz channel bandwidth. The maximum value depends on the
		bandwidth (maximum number of RBs minus one) . \n
			:return: offset_rb: (integer or boolean) Offset of the first allocated RB
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:ORVFilter?')
		return Conversions.str_to_int_or_bool(response)

	def set_orv_filter(self, offset_rb: int or bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:ORVFilter \n
		Snippet: driver.configure.lteMeas.multiEval.set_orv_filter(offset_rb = 1) \n
		Specifies, enables or disables the RB offset view filter. If the filter is active, only slots with a matching number of
		RB offset are measured. The indicated input range applies to a 20-MHz channel bandwidth. The maximum value depends on the
		bandwidth (maximum number of RBs minus one) . \n
			:param offset_rb: (integer or boolean) Offset of the first allocated RB
		"""
		param = Conversions.decimal_or_bool_value_to_str(offset_rb)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:ORVFilter {param}')

	# noinspection PyTypeChecker
	def get_ctv_filter(self) -> enums.ChannelTypeVewFilter:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:CTVFilter \n
		Snippet: value: enums.ChannelTypeVewFilter = driver.configure.lteMeas.multiEval.get_ctv_filter() \n
		Specifies, enables or disables the channel type view filter. If the filter is active, only slots with detected channel
		type PUSCH or PUCCH are measured. \n
			:return: channel_type: PUSCh: measure only PUSCH PUCCh: measure only PUCCH ON: enable the filter OFF: disable the filter
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:CTVFilter?')
		return Conversions.str_to_scalar_enum(response, enums.ChannelTypeVewFilter)

	def set_ctv_filter(self, channel_type: enums.ChannelTypeVewFilter) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:CTVFilter \n
		Snippet: driver.configure.lteMeas.multiEval.set_ctv_filter(channel_type = enums.ChannelTypeVewFilter.OFF) \n
		Specifies, enables or disables the channel type view filter. If the filter is active, only slots with detected channel
		type PUSCH or PUCCH are measured. \n
			:param channel_type: PUSCh: measure only PUSCH PUCCh: measure only PUCCH ON: enable the filter OFF: disable the filter
		"""
		param = Conversions.enum_scalar_to_str(channel_type, enums.ChannelTypeVewFilter)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:CTVFilter {param}')

	def get_dss_pusch(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:DSSPusch \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.get_dss_pusch() \n
		Specifies the delta sequence shift value (Δss) used to calculate the sequence shift pattern for PUSCH. \n
			:return: delta_seq_sh_pusch: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:DSSPusch?')
		return Conversions.str_to_int(response)

	def set_dss_pusch(self, delta_seq_sh_pusch: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:DSSPusch \n
		Snippet: driver.configure.lteMeas.multiEval.set_dss_pusch(delta_seq_sh_pusch = 1) \n
		Specifies the delta sequence shift value (Δss) used to calculate the sequence shift pattern for PUSCH. \n
			:param delta_seq_sh_pusch: No help available
		"""
		param = Conversions.decimal_value_to_str(delta_seq_sh_pusch)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:DSSPusch {param}')

	def get_ghopping(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:GHOPping \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.get_ghopping() \n
		Specifies whether group hopping is used. For Signal Path = Network, the setting is not configurable. \n
			:return: value: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:GHOPping?')
		return Conversions.str_to_bool(response)

	def set_ghopping(self, value: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:GHOPping \n
		Snippet: driver.configure.lteMeas.multiEval.set_ghopping(value = False) \n
		Specifies whether group hopping is used. For Signal Path = Network, the setting is not configurable. \n
			:param value: No help available
		"""
		param = Conversions.bool_to_str(value)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:GHOPping {param}')

	# noinspection PyTypeChecker
	def get_mslot(self) -> enums.MeasureSlot:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:MSLot \n
		Snippet: value: enums.MeasureSlot = driver.configure.lteMeas.multiEval.get_mslot() \n
		Selects which slots of the Measure Subframe are measured. \n
			:return: measure_slot: MS0: slot number 0 only MS1: slot number 1 only ALL: both slots
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:MSLot?')
		return Conversions.str_to_scalar_enum(response, enums.MeasureSlot)

	def set_mslot(self, measure_slot: enums.MeasureSlot) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:MSLot \n
		Snippet: driver.configure.lteMeas.multiEval.set_mslot(measure_slot = enums.MeasureSlot.ALL) \n
		Selects which slots of the Measure Subframe are measured. \n
			:param measure_slot: MS0: slot number 0 only MS1: slot number 1 only ALL: both slots
		"""
		param = Conversions.enum_scalar_to_str(measure_slot, enums.MeasureSlot)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:MSLot {param}')

	# noinspection PyTypeChecker
	def get_view(self) -> enums.ViewMev:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:VIEW \n
		Snippet: value: enums.ViewMev = driver.configure.lteMeas.multiEval.get_view() \n
		No command help available \n
			:return: view: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:VIEW?')
		return Conversions.str_to_scalar_enum(response, enums.ViewMev)

	def set_view(self, view: enums.ViewMev) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:VIEW \n
		Snippet: driver.configure.lteMeas.multiEval.set_view(view = enums.ViewMev.ACLR) \n
		No command help available \n
			:param view: No help available
		"""
		param = Conversions.enum_scalar_to_str(view, enums.ViewMev)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:VIEW {param}')

	def clone(self) -> 'MultiEvalCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = MultiEvalCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
