from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions
from ..... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SrsCls:
	"""Srs commands group definition. 8 total commands, 2 Subgroups, 6 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("srs", core, parent)

	@property
	def scount(self):
		"""scount commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_scount'):
			from .Scount import ScountCls
			self._scount = ScountCls(self._core, self._cmd_group)
		return self._scount

	@property
	def limit(self):
		"""limit commands group. 1 Sub-classes, 0 commands."""
		if not hasattr(self, '_limit'):
			from .Limit import LimitCls
			self._limit = LimitCls(self._core, self._cmd_group)
		return self._limit

	# noinspection PyTypeChecker
	def get_view(self) -> enums.ViewSrs:
		"""CONFigure:LTE:MEASurement<Instance>:SRS:VIEW \n
		Snippet: value: enums.ViewSrs = driver.configure.lteMeas.srs.get_view() \n
		No command help available \n
			:return: view: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:SRS:VIEW?')
		return Conversions.str_to_scalar_enum(response, enums.ViewSrs)

	def set_view(self, view: enums.ViewSrs) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:SRS:VIEW \n
		Snippet: driver.configure.lteMeas.srs.set_view(view = enums.ViewSrs.PDYNamics) \n
		No command help available \n
			:param view: No help available
		"""
		param = Conversions.enum_scalar_to_str(view, enums.ViewSrs)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:SRS:VIEW {param}')

	def get_timeout(self) -> float:
		"""CONFigure:LTE:MEASurement<Instance>:SRS:TOUT \n
		Snippet: value: float = driver.configure.lteMeas.srs.get_timeout() \n
		Defines a timeout for the measurement. The timer is started when the measurement is initiated via a READ or INIT command.
		It is not started if the measurement is initiated manually. When the measurement has completed the first measurement
		cycle (first single shot) , the statistical depth is reached and the timer is reset. If the first measurement cycle has
		not been completed when the timer expires, the measurement is stopped. The measurement state changes to RDY.
		The reliability indicator is set to 1, indicating that a measurement timeout occurred. Still running READ, FETCh or
		CALCulate commands are completed, returning the available results. At least for some results, there are no values at all
		or the statistical depth has not been reached. A timeout of 0 s corresponds to an infinite measurement timeout. \n
			:return: timeout: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:SRS:TOUT?')
		return Conversions.str_to_float(response)

	def set_timeout(self, timeout: float) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:SRS:TOUT \n
		Snippet: driver.configure.lteMeas.srs.set_timeout(timeout = 1.0) \n
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
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:SRS:TOUT {param}')

	# noinspection PyTypeChecker
	def get_repetition(self) -> enums.Repeat:
		"""CONFigure:LTE:MEASurement<Instance>:SRS:REPetition \n
		Snippet: value: enums.Repeat = driver.configure.lteMeas.srs.get_repetition() \n
		Specifies the repetition mode of the measurement. The repetition mode specifies whether the measurement is stopped after
		a single shot or repeated continuously. Use the CONFigure:...:MEAS<i>:...:SCOunt commands to specify the number of
		measurement intervals per single shot. \n
			:return: repetition: SINGleshot: Single-shot measurement CONTinuous: Continuous measurement
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:SRS:REPetition?')
		return Conversions.str_to_scalar_enum(response, enums.Repeat)

	def set_repetition(self, repetition: enums.Repeat) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:SRS:REPetition \n
		Snippet: driver.configure.lteMeas.srs.set_repetition(repetition = enums.Repeat.CONTinuous) \n
		Specifies the repetition mode of the measurement. The repetition mode specifies whether the measurement is stopped after
		a single shot or repeated continuously. Use the CONFigure:...:MEAS<i>:...:SCOunt commands to specify the number of
		measurement intervals per single shot. \n
			:param repetition: SINGleshot: Single-shot measurement CONTinuous: Continuous measurement
		"""
		param = Conversions.enum_scalar_to_str(repetition, enums.Repeat)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:SRS:REPetition {param}')

	# noinspection PyTypeChecker
	def get_scondition(self) -> enums.StopCondition:
		"""CONFigure:LTE:MEASurement<Instance>:SRS:SCONdition \n
		Snippet: value: enums.StopCondition = driver.configure.lteMeas.srs.get_scondition() \n
		Qualifies whether the measurement is stopped after a failed limit check or continued. With SLFail, the measurement is
		stopped and reaches the RDY state when one of the results exceeds the limits. \n
			:return: stop_condition: NONE: Continue measurement irrespective of the limit check. SLFail: Stop measurement on limit failure.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:SRS:SCONdition?')
		return Conversions.str_to_scalar_enum(response, enums.StopCondition)

	def set_scondition(self, stop_condition: enums.StopCondition) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:SRS:SCONdition \n
		Snippet: driver.configure.lteMeas.srs.set_scondition(stop_condition = enums.StopCondition.NONE) \n
		Qualifies whether the measurement is stopped after a failed limit check or continued. With SLFail, the measurement is
		stopped and reaches the RDY state when one of the results exceeds the limits. \n
			:param stop_condition: NONE: Continue measurement irrespective of the limit check. SLFail: Stop measurement on limit failure.
		"""
		param = Conversions.enum_scalar_to_str(stop_condition, enums.StopCondition)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:SRS:SCONdition {param}')

	def get_mo_exception(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:SRS:MOEXception \n
		Snippet: value: bool = driver.configure.lteMeas.srs.get_mo_exception() \n
		Specifies whether measurement results that the CMX500 identifies as faulty or inaccurate are rejected. \n
			:return: meas_on_exception: OFF: Faulty results are rejected. ON: Results are never rejected.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:SRS:MOEXception?')
		return Conversions.str_to_bool(response)

	def set_mo_exception(self, meas_on_exception: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:SRS:MOEXception \n
		Snippet: driver.configure.lteMeas.srs.set_mo_exception(meas_on_exception = False) \n
		Specifies whether measurement results that the CMX500 identifies as faulty or inaccurate are rejected. \n
			:param meas_on_exception: OFF: Faulty results are rejected. ON: Results are never rejected.
		"""
		param = Conversions.bool_to_str(meas_on_exception)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:SRS:MOEXception {param}')

	def get_hdmode(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:SRS:HDMode \n
		Snippet: value: bool = driver.configure.lteMeas.srs.get_hdmode() \n
		Enables or disables the high dynamic mode for power dynamics measurements. With RF path sharing, this command is not
		applicable. \n
			:return: high_dynamic_mode: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:SRS:HDMode?')
		return Conversions.str_to_bool(response)

	def set_hdmode(self, high_dynamic_mode: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:SRS:HDMode \n
		Snippet: driver.configure.lteMeas.srs.set_hdmode(high_dynamic_mode = False) \n
		Enables or disables the high dynamic mode for power dynamics measurements. With RF path sharing, this command is not
		applicable. \n
			:param high_dynamic_mode: No help available
		"""
		param = Conversions.bool_to_str(high_dynamic_mode)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:SRS:HDMode {param}')

	def clone(self) -> 'SrsCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = SrsCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
