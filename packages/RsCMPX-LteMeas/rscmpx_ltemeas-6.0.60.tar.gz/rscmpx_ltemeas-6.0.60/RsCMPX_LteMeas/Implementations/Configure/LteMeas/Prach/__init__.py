from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions
from ..... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class PrachCls:
	"""Prach commands group definition. 36 total commands, 6 Subgroups, 10 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("prach", core, parent)

	@property
	def pfOffset(self):
		"""pfOffset commands group. 0 Sub-classes, 2 commands."""
		if not hasattr(self, '_pfOffset'):
			from .PfOffset import PfOffsetCls
			self._pfOffset = PfOffsetCls(self._core, self._cmd_group)
		return self._pfOffset

	@property
	def modulation(self):
		"""modulation commands group. 2 Sub-classes, 3 commands."""
		if not hasattr(self, '_modulation'):
			from .Modulation import ModulationCls
			self._modulation = ModulationCls(self._core, self._cmd_group)
		return self._modulation

	@property
	def power(self):
		"""power commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_power'):
			from .Power import PowerCls
			self._power = PowerCls(self._core, self._cmd_group)
		return self._power

	@property
	def scount(self):
		"""scount commands group. 0 Sub-classes, 2 commands."""
		if not hasattr(self, '_scount'):
			from .Scount import ScountCls
			self._scount = ScountCls(self._core, self._cmd_group)
		return self._scount

	@property
	def result(self):
		"""result commands group. 0 Sub-classes, 9 commands."""
		if not hasattr(self, '_result'):
			from .Result import ResultCls
			self._result = ResultCls(self._core, self._cmd_group)
		return self._result

	@property
	def limit(self):
		"""limit commands group. 4 Sub-classes, 1 commands."""
		if not hasattr(self, '_limit'):
			from .Limit import LimitCls
			self._limit = LimitCls(self._core, self._cmd_group)
		return self._limit

	# noinspection PyTypeChecker
	def get_view(self) -> enums.ViewPrach:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:VIEW \n
		Snippet: value: enums.ViewPrach = driver.configure.lteMeas.prach.get_view() \n
		No command help available \n
			:return: view: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:PRACh:VIEW?')
		return Conversions.str_to_scalar_enum(response, enums.ViewPrach)

	def set_view(self, view: enums.ViewPrach) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:VIEW \n
		Snippet: driver.configure.lteMeas.prach.set_view(view = enums.ViewPrach.EVMagnitude) \n
		No command help available \n
			:param view: No help available
		"""
		param = Conversions.enum_scalar_to_str(view, enums.ViewPrach)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:PRACh:VIEW {param}')

	def get_timeout(self) -> float:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:TOUT \n
		Snippet: value: float = driver.configure.lteMeas.prach.get_timeout() \n
		Defines a timeout for the measurement. The timer is started when the measurement is initiated via a READ or INIT command.
		It is not started if the measurement is initiated manually. When the measurement has completed the first measurement
		cycle (first single shot) , the statistical depth is reached and the timer is reset. If the first measurement cycle has
		not been completed when the timer expires, the measurement is stopped. The measurement state changes to RDY.
		The reliability indicator is set to 1, indicating that a measurement timeout occurred. Still running READ, FETCh or
		CALCulate commands are completed, returning the available results. At least for some results, there are no values at all
		or the statistical depth has not been reached. A timeout of 0 s corresponds to an infinite measurement timeout. \n
			:return: timeout: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:PRACh:TOUT?')
		return Conversions.str_to_float(response)

	def set_timeout(self, timeout: float) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:TOUT \n
		Snippet: driver.configure.lteMeas.prach.set_timeout(timeout = 1.0) \n
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
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:PRACh:TOUT {param}')

	# noinspection PyTypeChecker
	def get_repetition(self) -> enums.Repeat:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:REPetition \n
		Snippet: value: enums.Repeat = driver.configure.lteMeas.prach.get_repetition() \n
		Specifies the repetition mode of the measurement. The repetition mode specifies whether the measurement is stopped after
		a single shot or repeated continuously. Use the CONFigure:...:MEAS<i>:...:SCOunt commands to specify the number of
		measurement intervals per single shot. \n
			:return: repetition: SINGleshot: Single-shot measurement CONTinuous: Continuous measurement
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:PRACh:REPetition?')
		return Conversions.str_to_scalar_enum(response, enums.Repeat)

	def set_repetition(self, repetition: enums.Repeat) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:REPetition \n
		Snippet: driver.configure.lteMeas.prach.set_repetition(repetition = enums.Repeat.CONTinuous) \n
		Specifies the repetition mode of the measurement. The repetition mode specifies whether the measurement is stopped after
		a single shot or repeated continuously. Use the CONFigure:...:MEAS<i>:...:SCOunt commands to specify the number of
		measurement intervals per single shot. \n
			:param repetition: SINGleshot: Single-shot measurement CONTinuous: Continuous measurement
		"""
		param = Conversions.enum_scalar_to_str(repetition, enums.Repeat)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:PRACh:REPetition {param}')

	# noinspection PyTypeChecker
	def get_scondition(self) -> enums.StopCondition:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:SCONdition \n
		Snippet: value: enums.StopCondition = driver.configure.lteMeas.prach.get_scondition() \n
		Qualifies whether the measurement is stopped after a failed limit check or continued. With SLFail, the measurement is
		stopped and reaches the RDY state when one of the results exceeds the limits. \n
			:return: stop_condition: NONE: Continue measurement irrespective of the limit check. SLFail: Stop measurement on limit failure.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:PRACh:SCONdition?')
		return Conversions.str_to_scalar_enum(response, enums.StopCondition)

	def set_scondition(self, stop_condition: enums.StopCondition) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:SCONdition \n
		Snippet: driver.configure.lteMeas.prach.set_scondition(stop_condition = enums.StopCondition.NONE) \n
		Qualifies whether the measurement is stopped after a failed limit check or continued. With SLFail, the measurement is
		stopped and reaches the RDY state when one of the results exceeds the limits. \n
			:param stop_condition: NONE: Continue measurement irrespective of the limit check. SLFail: Stop measurement on limit failure.
		"""
		param = Conversions.enum_scalar_to_str(stop_condition, enums.StopCondition)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:PRACh:SCONdition {param}')

	def get_mo_exception(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:MOEXception \n
		Snippet: value: bool = driver.configure.lteMeas.prach.get_mo_exception() \n
		Specifies whether measurement results that the CMX500 identifies as faulty or inaccurate are rejected. \n
			:return: meas_on_exception: OFF: Faulty results are rejected. ON: Results are never rejected.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:PRACh:MOEXception?')
		return Conversions.str_to_bool(response)

	def set_mo_exception(self, meas_on_exception: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:MOEXception \n
		Snippet: driver.configure.lteMeas.prach.set_mo_exception(meas_on_exception = False) \n
		Specifies whether measurement results that the CMX500 identifies as faulty or inaccurate are rejected. \n
			:param meas_on_exception: OFF: Faulty results are rejected. ON: Results are never rejected.
		"""
		param = Conversions.bool_to_str(meas_on_exception)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:PRACh:MOEXception {param}')

	def get_pc_index(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:PCINdex \n
		Snippet: value: int = driver.configure.lteMeas.prach.get_pc_index() \n
		The PRACH configuration index identifies the PRACH configuration used by the UE (preamble format, which resources in the
		time domain are allowed for transmission of preambles etc.) .
		For Signal Path = Network, use[CONFigure:]SIGNaling:LTE:CELL:POWer:UL:CINDex. \n
			:return: prach_conf_index: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:PRACh:PCINdex?')
		return Conversions.str_to_int(response)

	def set_pc_index(self, prach_conf_index: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:PCINdex \n
		Snippet: driver.configure.lteMeas.prach.set_pc_index(prach_conf_index = 1) \n
		The PRACH configuration index identifies the PRACH configuration used by the UE (preamble format, which resources in the
		time domain are allowed for transmission of preambles etc.) .
		For Signal Path = Network, use[CONFigure:]SIGNaling:LTE:CELL:POWer:UL:CINDex. \n
			:param prach_conf_index: No help available
		"""
		param = Conversions.decimal_value_to_str(prach_conf_index)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:PRACh:PCINdex {param}')

	def get_ssymbol(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:SSYMbol \n
		Snippet: value: int = driver.configure.lteMeas.prach.get_ssymbol() \n
		Selects the OFDM symbol to be evaluated for single-symbol modulation result diagrams. The number of OFDM symbols in the
		preamble (<no of symbols>) depends on the preamble format, see Table 'Preambles in the time domain'. \n
			:return: selected_symbol: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:PRACh:SSYMbol?')
		return Conversions.str_to_int(response)

	def set_ssymbol(self, selected_symbol: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:SSYMbol \n
		Snippet: driver.configure.lteMeas.prach.set_ssymbol(selected_symbol = 1) \n
		Selects the OFDM symbol to be evaluated for single-symbol modulation result diagrams. The number of OFDM symbols in the
		preamble (<no of symbols>) depends on the preamble format, see Table 'Preambles in the time domain'. \n
			:param selected_symbol: No help available
		"""
		param = Conversions.decimal_value_to_str(selected_symbol)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:PRACh:SSYMbol {param}')

	def get_pformat(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:PFORmat \n
		Snippet: value: int = driver.configure.lteMeas.prach.get_pformat() \n
		No command help available \n
			:return: preamble_format: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:PRACh:PFORmat?')
		return Conversions.str_to_int(response)

	def get_no_preambles(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:NOPReambles \n
		Snippet: value: int = driver.configure.lteMeas.prach.get_no_preambles() \n
		Specifies the number of preambles to be captured per measurement interval. \n
			:return: number_preamble: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:PRACh:NOPReambles?')
		return Conversions.str_to_int(response)

	def set_no_preambles(self, number_preamble: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:NOPReambles \n
		Snippet: driver.configure.lteMeas.prach.set_no_preambles(number_preamble = 1) \n
		Specifies the number of preambles to be captured per measurement interval. \n
			:param number_preamble: No help available
		"""
		param = Conversions.decimal_value_to_str(number_preamble)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:PRACh:NOPReambles {param}')

	# noinspection PyTypeChecker
	def get_po_preambles(self) -> enums.PeriodPreamble:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:POPReambles \n
		Snippet: value: enums.PeriodPreamble = driver.configure.lteMeas.prach.get_po_preambles() \n
		Specifies the periodicity of preambles to be captured for multi-preamble result views. \n
			:return: period_preamble: MS05: 5 ms MS10: 10 ms MS20: 20 ms
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:PRACh:POPReambles?')
		return Conversions.str_to_scalar_enum(response, enums.PeriodPreamble)

	def set_po_preambles(self, period_preamble: enums.PeriodPreamble) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:POPReambles \n
		Snippet: driver.configure.lteMeas.prach.set_po_preambles(period_preamble = enums.PeriodPreamble.MS05) \n
		Specifies the periodicity of preambles to be captured for multi-preamble result views. \n
			:param period_preamble: MS05: 5 ms MS10: 10 ms MS20: 20 ms
		"""
		param = Conversions.enum_scalar_to_str(period_preamble, enums.PeriodPreamble)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:PRACh:POPReambles {param}')

	def clone(self) -> 'PrachCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = PrachCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
