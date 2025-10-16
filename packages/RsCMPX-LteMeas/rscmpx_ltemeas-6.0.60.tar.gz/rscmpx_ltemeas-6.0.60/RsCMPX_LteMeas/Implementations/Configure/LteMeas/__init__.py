from ....Internal.Core import Core
from ....Internal.CommandsGroup import CommandsGroup
from ....Internal import Conversions
from .... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class LteMeasCls:
	"""LteMeas commands group definition. 221 total commands, 10 Subgroups, 5 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("lteMeas", core, parent)

	@property
	def network(self):
		"""network commands group. 0 Sub-classes, 3 commands."""
		if not hasattr(self, '_network'):
			from .Network import NetworkCls
			self._network = NetworkCls(self._core, self._cmd_group)
		return self._network

	@property
	def rfSettings(self):
		"""rfSettings commands group. 4 Sub-classes, 6 commands."""
		if not hasattr(self, '_rfSettings'):
			from .RfSettings import RfSettingsCls
			self._rfSettings = RfSettingsCls(self._core, self._cmd_group)
		return self._rfSettings

	@property
	def carrierAggregation(self):
		"""carrierAggregation commands group. 6 Sub-classes, 0 commands."""
		if not hasattr(self, '_carrierAggregation'):
			from .CarrierAggregation import CarrierAggregationCls
			self._carrierAggregation = CarrierAggregationCls(self._core, self._cmd_group)
		return self._carrierAggregation

	@property
	def emtc(self):
		"""emtc commands group. 0 Sub-classes, 3 commands."""
		if not hasattr(self, '_emtc'):
			from .Emtc import EmtcCls
			self._emtc = EmtcCls(self._core, self._cmd_group)
		return self._emtc

	@property
	def multiEval(self):
		"""multiEval commands group. 17 Sub-classes, 19 commands."""
		if not hasattr(self, '_multiEval'):
			from .MultiEval import MultiEvalCls
			self._multiEval = MultiEvalCls(self._core, self._cmd_group)
		return self._multiEval

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
	def prach(self):
		"""prach commands group. 6 Sub-classes, 10 commands."""
		if not hasattr(self, '_prach'):
			from .Prach import PrachCls
			self._prach = PrachCls(self._core, self._cmd_group)
		return self._prach

	@property
	def srs(self):
		"""srs commands group. 2 Sub-classes, 6 commands."""
		if not hasattr(self, '_srs'):
			from .Srs import SrsCls
			self._srs = SrsCls(self._core, self._cmd_group)
		return self._srs

	# noinspection PyTypeChecker
	def get_band(self) -> enums.Band:
		"""CONFigure:LTE:MEASurement<Instance>:BAND \n
		Snippet: value: enums.Band = driver.configure.lteMeas.get_band() \n
		Selects the operating band (OB) .
			INTRO_CMD_HELP: The allowed input range has dependencies: \n
			- FDD UL: OB1 | ... | OB28 | OB30 | OB31 | OB65 | OB66 | OB68 | OB70 | ... | OB74 | OB85 | OB87 | OB88
			- TDD UL: OB33 | ... | OB45 | OB48 | OB50 | ... | OB53 | OB250
			- Sidelink: OB47
		For Signal Path = Network, use [CONFigure:]SIGNaling:LTE:CELL:RFSettings:FBINdicator. \n
			:return: band: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:BAND?')
		return Conversions.str_to_scalar_enum(response, enums.Band)

	def set_band(self, band: enums.Band) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:BAND \n
		Snippet: driver.configure.lteMeas.set_band(band = enums.Band.OB1) \n
		Selects the operating band (OB) .
			INTRO_CMD_HELP: The allowed input range has dependencies: \n
			- FDD UL: OB1 | ... | OB28 | OB30 | OB31 | OB65 | OB66 | OB68 | OB70 | ... | OB74 | OB85 | OB87 | OB88
			- TDD UL: OB33 | ... | OB45 | OB48 | OB50 | ... | OB53 | OB250
			- Sidelink: OB47
		For Signal Path = Network, use [CONFigure:]SIGNaling:LTE:CELL:RFSettings:FBINdicator. \n
			:param band: No help available
		"""
		param = Conversions.enum_scalar_to_str(band, enums.Band)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:BAND {param}')

	# noinspection PyTypeChecker
	def get_spath(self) -> enums.Path:
		"""CONFigure:LTE:MEASurement<Instance>:SPATh \n
		Snippet: value: enums.Path = driver.configure.lteMeas.get_spath() \n
		Selects between a standalone measurement and a measurement with coupling to signaling settings (cell settings of the
		network configuration) . \n
			:return: path: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:SPATh?')
		return Conversions.str_to_scalar_enum(response, enums.Path)

	def set_spath(self, path: enums.Path) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:SPATh \n
		Snippet: driver.configure.lteMeas.set_spath(path = enums.Path.NETWork) \n
		Selects between a standalone measurement and a measurement with coupling to signaling settings (cell settings of the
		network configuration) . \n
			:param path: No help available
		"""
		param = Conversions.enum_scalar_to_str(path, enums.Path)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:SPATh {param}')

	# noinspection PyTypeChecker
	def get_stype(self) -> enums.SignalType:
		"""CONFigure:LTE:MEASurement<Instance>:STYPe \n
		Snippet: value: enums.SignalType = driver.configure.lteMeas.get_stype() \n
		Selects the type of the measured signal. \n
			:return: signal_type: UL: LTE uplink signal SL: V2X sidelink signal
		"""
		response = self._core.io.query_str_with_opc('CONFigure:LTE:MEASurement<Instance>:STYPe?')
		return Conversions.str_to_scalar_enum(response, enums.SignalType)

	def set_stype(self, signal_type: enums.SignalType) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:STYPe \n
		Snippet: driver.configure.lteMeas.set_stype(signal_type = enums.SignalType.SL) \n
		Selects the type of the measured signal. \n
			:param signal_type: UL: LTE uplink signal SL: V2X sidelink signal
		"""
		param = Conversions.enum_scalar_to_str(signal_type, enums.SignalType)
		self._core.io.write_with_opc(f'CONFigure:LTE:MEASurement<Instance>:STYPe {param}')

	# noinspection PyTypeChecker
	def get_dmode(self) -> enums.Mode:
		"""CONFigure:LTE:MEASurement<Instance>:DMODe \n
		Snippet: value: enums.Mode = driver.configure.lteMeas.get_dmode() \n
		Selects the duplex mode of the LTE signal: FDD or TDD.
		For Signal Path = Network, use [CONFigure:]SIGNaling:LTE:CELL:RFSettings:DMODe. \n
			:return: mode: No help available
		"""
		response = self._core.io.query_str_with_opc('CONFigure:LTE:MEASurement<Instance>:DMODe?')
		return Conversions.str_to_scalar_enum(response, enums.Mode)

	def set_dmode(self, mode: enums.Mode) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:DMODe \n
		Snippet: driver.configure.lteMeas.set_dmode(mode = enums.Mode.FDD) \n
		Selects the duplex mode of the LTE signal: FDD or TDD.
		For Signal Path = Network, use [CONFigure:]SIGNaling:LTE:CELL:RFSettings:DMODe. \n
			:param mode: No help available
		"""
		param = Conversions.enum_scalar_to_str(mode, enums.Mode)
		self._core.io.write_with_opc(f'CONFigure:LTE:MEASurement<Instance>:DMODe {param}')

	# noinspection PyTypeChecker
	def get_fstructure(self) -> enums.FrameStructure:
		"""CONFigure:LTE:MEASurement<Instance>:FSTRucture \n
		Snippet: value: enums.FrameStructure = driver.configure.lteMeas.get_fstructure() \n
		Queries the frame structure type of the LTE signal. The value depends on the duplex mode (method RsCMPX_LteMeas.Configure.
		LteMeas.dmode) . \n
			:return: frame_structure: T1: Type 1, FDD signal T2: Type 2, TDD signal
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:FSTRucture?')
		return Conversions.str_to_scalar_enum(response, enums.FrameStructure)

	def clone(self) -> 'LteMeasCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = LteMeasCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
