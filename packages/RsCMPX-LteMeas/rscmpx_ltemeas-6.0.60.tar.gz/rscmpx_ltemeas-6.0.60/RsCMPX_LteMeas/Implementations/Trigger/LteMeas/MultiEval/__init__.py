from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions
from ..... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class MultiEvalCls:
	"""MultiEval commands group definition. 9 total commands, 1 Subgroups, 7 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("multiEval", core, parent)

	@property
	def listPy(self):
		"""listPy commands group. 0 Sub-classes, 2 commands."""
		if not hasattr(self, '_listPy'):
			from .ListPy import ListPyCls
			self._listPy = ListPyCls(self._core, self._cmd_group)
		return self._listPy

	def get_threshold(self) -> float or bool:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:THReshold \n
		Snippet: value: float or bool = driver.trigger.lteMeas.multiEval.get_threshold() \n
		Defines the trigger threshold for power trigger sources. \n
			:return: trig_threshold: (float or boolean) No help available
		"""
		response = self._core.io.query_str('TRIGger:LTE:MEASurement<Instance>:MEValuation:THReshold?')
		return Conversions.str_to_float_or_bool(response)

	def set_threshold(self, trig_threshold: float or bool) -> None:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:THReshold \n
		Snippet: driver.trigger.lteMeas.multiEval.set_threshold(trig_threshold = 1.0) \n
		Defines the trigger threshold for power trigger sources. \n
			:param trig_threshold: (float or boolean) No help available
		"""
		param = Conversions.decimal_or_bool_value_to_str(trig_threshold)
		self._core.io.write(f'TRIGger:LTE:MEASurement<Instance>:MEValuation:THReshold {param}')

	# noinspection PyTypeChecker
	def get_slope(self) -> enums.SignalSlope:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:SLOPe \n
		Snippet: value: enums.SignalSlope = driver.trigger.lteMeas.multiEval.get_slope() \n
		Qualifies whether the trigger event is generated at the rising or at the falling edge of the trigger pulse (valid for
		external and power trigger sources) . \n
			:return: slope: REDGe: Rising edge FEDGe: Falling edge
		"""
		response = self._core.io.query_str('TRIGger:LTE:MEASurement<Instance>:MEValuation:SLOPe?')
		return Conversions.str_to_scalar_enum(response, enums.SignalSlope)

	def set_slope(self, slope: enums.SignalSlope) -> None:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:SLOPe \n
		Snippet: driver.trigger.lteMeas.multiEval.set_slope(slope = enums.SignalSlope.FEDGe) \n
		Qualifies whether the trigger event is generated at the rising or at the falling edge of the trigger pulse (valid for
		external and power trigger sources) . \n
			:param slope: REDGe: Rising edge FEDGe: Falling edge
		"""
		param = Conversions.enum_scalar_to_str(slope, enums.SignalSlope)
		self._core.io.write(f'TRIGger:LTE:MEASurement<Instance>:MEValuation:SLOPe {param}')

	def get_delay(self) -> float:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:DELay \n
		Snippet: value: float = driver.trigger.lteMeas.multiEval.get_delay() \n
		Defines a time delaying the start of the measurement relative to the trigger event. This setting has no influence on free
		run measurements. \n
			:return: delay: No help available
		"""
		response = self._core.io.query_str('TRIGger:LTE:MEASurement<Instance>:MEValuation:DELay?')
		return Conversions.str_to_float(response)

	def set_delay(self, delay: float) -> None:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:DELay \n
		Snippet: driver.trigger.lteMeas.multiEval.set_delay(delay = 1.0) \n
		Defines a time delaying the start of the measurement relative to the trigger event. This setting has no influence on free
		run measurements. \n
			:param delay: No help available
		"""
		param = Conversions.decimal_value_to_str(delay)
		self._core.io.write(f'TRIGger:LTE:MEASurement<Instance>:MEValuation:DELay {param}')

	def get_timeout(self) -> float or bool:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:TOUT \n
		Snippet: value: float or bool = driver.trigger.lteMeas.multiEval.get_timeout() \n
		Selects the maximum time that the measurement waits for a trigger event before it stops in remote control mode or
		indicates a trigger timeout in manual operation mode. This setting has no influence on Free Run measurements. \n
			:return: trigger_timeout: (float or boolean) No help available
		"""
		response = self._core.io.query_str('TRIGger:LTE:MEASurement<Instance>:MEValuation:TOUT?')
		return Conversions.str_to_float_or_bool(response)

	def set_timeout(self, trigger_timeout: float or bool) -> None:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:TOUT \n
		Snippet: driver.trigger.lteMeas.multiEval.set_timeout(trigger_timeout = 1.0) \n
		Selects the maximum time that the measurement waits for a trigger event before it stops in remote control mode or
		indicates a trigger timeout in manual operation mode. This setting has no influence on Free Run measurements. \n
			:param trigger_timeout: (float or boolean) No help available
		"""
		param = Conversions.decimal_or_bool_value_to_str(trigger_timeout)
		self._core.io.write(f'TRIGger:LTE:MEASurement<Instance>:MEValuation:TOUT {param}')

	def get_mgap(self) -> int:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:MGAP \n
		Snippet: value: int = driver.trigger.lteMeas.multiEval.get_mgap() \n
		Sets a minimum time during which the IF signal must be below the trigger threshold before the trigger is armed so that an
		IF power trigger event can be generated. \n
			:return: min_trig_gap: No help available
		"""
		response = self._core.io.query_str('TRIGger:LTE:MEASurement<Instance>:MEValuation:MGAP?')
		return Conversions.str_to_int(response)

	def set_mgap(self, min_trig_gap: int) -> None:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:MGAP \n
		Snippet: driver.trigger.lteMeas.multiEval.set_mgap(min_trig_gap = 1) \n
		Sets a minimum time during which the IF signal must be below the trigger threshold before the trigger is armed so that an
		IF power trigger event can be generated. \n
			:param min_trig_gap: No help available
		"""
		param = Conversions.decimal_value_to_str(min_trig_gap)
		self._core.io.write(f'TRIGger:LTE:MEASurement<Instance>:MEValuation:MGAP {param}')

	# noinspection PyTypeChecker
	def get_smode(self) -> enums.SyncMode:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:SMODe \n
		Snippet: value: enums.SyncMode = driver.trigger.lteMeas.multiEval.get_smode() \n
		Selects the size of the search window for synchronization - normal or enhanced. \n
			:return: sync_mode: No help available
		"""
		response = self._core.io.query_str('TRIGger:LTE:MEASurement<Instance>:MEValuation:SMODe?')
		return Conversions.str_to_scalar_enum(response, enums.SyncMode)

	def set_smode(self, sync_mode: enums.SyncMode) -> None:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:SMODe \n
		Snippet: driver.trigger.lteMeas.multiEval.set_smode(sync_mode = enums.SyncMode.ENHanced) \n
		Selects the size of the search window for synchronization - normal or enhanced. \n
			:param sync_mode: No help available
		"""
		param = Conversions.enum_scalar_to_str(sync_mode, enums.SyncMode)
		self._core.io.write(f'TRIGger:LTE:MEASurement<Instance>:MEValuation:SMODe {param}')

	# noinspection PyTypeChecker
	def get_amode(self) -> enums.MevAcquisitionMode:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:AMODe \n
		Snippet: value: enums.MevAcquisitionMode = driver.trigger.lteMeas.multiEval.get_amode() \n
		Selects whether the measurement synchronizes to a slot boundary or to a subframe boundary. The parameter is relevant for
		Free Run (Fast Sync) and for list mode measurements with Synchronization Mode = Enhanced. \n
			:return: acquisition_mode: No help available
		"""
		response = self._core.io.query_str('TRIGger:LTE:MEASurement<Instance>:MEValuation:AMODe?')
		return Conversions.str_to_scalar_enum(response, enums.MevAcquisitionMode)

	def set_amode(self, acquisition_mode: enums.MevAcquisitionMode) -> None:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:AMODe \n
		Snippet: driver.trigger.lteMeas.multiEval.set_amode(acquisition_mode = enums.MevAcquisitionMode.SLOT) \n
		Selects whether the measurement synchronizes to a slot boundary or to a subframe boundary. The parameter is relevant for
		Free Run (Fast Sync) and for list mode measurements with Synchronization Mode = Enhanced. \n
			:param acquisition_mode: No help available
		"""
		param = Conversions.enum_scalar_to_str(acquisition_mode, enums.MevAcquisitionMode)
		self._core.io.write(f'TRIGger:LTE:MEASurement<Instance>:MEValuation:AMODe {param}')

	def clone(self) -> 'MultiEvalCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = MultiEvalCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
