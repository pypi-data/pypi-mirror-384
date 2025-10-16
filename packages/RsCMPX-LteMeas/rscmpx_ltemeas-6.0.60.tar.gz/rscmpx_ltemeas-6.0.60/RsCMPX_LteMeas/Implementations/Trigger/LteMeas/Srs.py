from ....Internal.Core import Core
from ....Internal.CommandsGroup import CommandsGroup
from ....Internal import Conversions
from .... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SrsCls:
	"""Srs commands group definition. 4 total commands, 0 Subgroups, 4 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("srs", core, parent)

	def get_threshold(self) -> float or bool:
		"""TRIGger:LTE:MEASurement<Instance>:SRS:THReshold \n
		Snippet: value: float or bool = driver.trigger.lteMeas.srs.get_threshold() \n
		Defines the trigger threshold for power trigger sources. \n
			:return: trig_threshold: (float or boolean) No help available
		"""
		response = self._core.io.query_str('TRIGger:LTE:MEASurement<Instance>:SRS:THReshold?')
		return Conversions.str_to_float_or_bool(response)

	def set_threshold(self, trig_threshold: float or bool) -> None:
		"""TRIGger:LTE:MEASurement<Instance>:SRS:THReshold \n
		Snippet: driver.trigger.lteMeas.srs.set_threshold(trig_threshold = 1.0) \n
		Defines the trigger threshold for power trigger sources. \n
			:param trig_threshold: (float or boolean) No help available
		"""
		param = Conversions.decimal_or_bool_value_to_str(trig_threshold)
		self._core.io.write(f'TRIGger:LTE:MEASurement<Instance>:SRS:THReshold {param}')

	# noinspection PyTypeChecker
	def get_slope(self) -> enums.SignalSlope:
		"""TRIGger:LTE:MEASurement<Instance>:SRS:SLOPe \n
		Snippet: value: enums.SignalSlope = driver.trigger.lteMeas.srs.get_slope() \n
		Qualifies whether the trigger event is generated at the rising or at the falling edge of the trigger pulse (valid for
		external and power trigger sources) . \n
			:return: slope: REDGe: Rising edge FEDGe: Falling edge
		"""
		response = self._core.io.query_str('TRIGger:LTE:MEASurement<Instance>:SRS:SLOPe?')
		return Conversions.str_to_scalar_enum(response, enums.SignalSlope)

	def set_slope(self, slope: enums.SignalSlope) -> None:
		"""TRIGger:LTE:MEASurement<Instance>:SRS:SLOPe \n
		Snippet: driver.trigger.lteMeas.srs.set_slope(slope = enums.SignalSlope.FEDGe) \n
		Qualifies whether the trigger event is generated at the rising or at the falling edge of the trigger pulse (valid for
		external and power trigger sources) . \n
			:param slope: REDGe: Rising edge FEDGe: Falling edge
		"""
		param = Conversions.enum_scalar_to_str(slope, enums.SignalSlope)
		self._core.io.write(f'TRIGger:LTE:MEASurement<Instance>:SRS:SLOPe {param}')

	def get_timeout(self) -> float or bool:
		"""TRIGger:LTE:MEASurement<Instance>:SRS:TOUT \n
		Snippet: value: float or bool = driver.trigger.lteMeas.srs.get_timeout() \n
		Selects the maximum time that the measurement waits for a trigger event before it stops in remote control mode or
		indicates a trigger timeout in manual operation mode. This setting has no influence on Free Run measurements. \n
			:return: trigger_timeout: (float or boolean) No help available
		"""
		response = self._core.io.query_str('TRIGger:LTE:MEASurement<Instance>:SRS:TOUT?')
		return Conversions.str_to_float_or_bool(response)

	def set_timeout(self, trigger_timeout: float or bool) -> None:
		"""TRIGger:LTE:MEASurement<Instance>:SRS:TOUT \n
		Snippet: driver.trigger.lteMeas.srs.set_timeout(trigger_timeout = 1.0) \n
		Selects the maximum time that the measurement waits for a trigger event before it stops in remote control mode or
		indicates a trigger timeout in manual operation mode. This setting has no influence on Free Run measurements. \n
			:param trigger_timeout: (float or boolean) No help available
		"""
		param = Conversions.decimal_or_bool_value_to_str(trigger_timeout)
		self._core.io.write(f'TRIGger:LTE:MEASurement<Instance>:SRS:TOUT {param}')

	def get_mgap(self) -> float:
		"""TRIGger:LTE:MEASurement<Instance>:SRS:MGAP \n
		Snippet: value: float = driver.trigger.lteMeas.srs.get_mgap() \n
		Sets a minimum time during which the IF signal must be below the trigger threshold before the trigger is armed so that an
		IF power trigger event can be generated. \n
			:return: min_trig_gap: No help available
		"""
		response = self._core.io.query_str('TRIGger:LTE:MEASurement<Instance>:SRS:MGAP?')
		return Conversions.str_to_float(response)

	def set_mgap(self, min_trig_gap: float) -> None:
		"""TRIGger:LTE:MEASurement<Instance>:SRS:MGAP \n
		Snippet: driver.trigger.lteMeas.srs.set_mgap(min_trig_gap = 1.0) \n
		Sets a minimum time during which the IF signal must be below the trigger threshold before the trigger is armed so that an
		IF power trigger event can be generated. \n
			:param min_trig_gap: No help available
		"""
		param = Conversions.decimal_value_to_str(min_trig_gap)
		self._core.io.write(f'TRIGger:LTE:MEASurement<Instance>:SRS:MGAP {param}')
