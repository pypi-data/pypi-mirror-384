from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions
from ..... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ListPyCls:
	"""ListPy commands group definition. 2 total commands, 0 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("listPy", core, parent)

	# noinspection PyTypeChecker
	def get_mode(self) -> enums.ListMode:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:LIST:MODE \n
		Snippet: value: enums.ListMode = driver.trigger.lteMeas.multiEval.listPy.get_mode() \n
		Specifies the trigger mode for list mode measurements. For configuration of retrigger flags, see method RsCMPX_LteMeas.
		Configure.LteMeas.MultiEval.ListPy.Segment.Setup.set. For configuration of the global trigger source,
		see TRIGger:LTE:MEAS<i>:MEValuation:SOURce. \n
			:return: mode:
				- ONCE: A trigger event is only required to start the measurement. The entire range of segments to be measured is captured without additional trigger event. The global trigger source is used.
				- SEGMent: The retrigger flag of each segment is evaluated. It defines whether a trigger event is required and which trigger source is used."""
		response = self._core.io.query_str('TRIGger:LTE:MEASurement<Instance>:MEValuation:LIST:MODE?')
		return Conversions.str_to_scalar_enum(response, enums.ListMode)

	def set_mode(self, mode: enums.ListMode) -> None:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:LIST:MODE \n
		Snippet: driver.trigger.lteMeas.multiEval.listPy.set_mode(mode = enums.ListMode.ONCE) \n
		Specifies the trigger mode for list mode measurements. For configuration of retrigger flags, see method RsCMPX_LteMeas.
		Configure.LteMeas.MultiEval.ListPy.Segment.Setup.set. For configuration of the global trigger source,
		see TRIGger:LTE:MEAS<i>:MEValuation:SOURce. \n
			:param mode:
				- ONCE: A trigger event is only required to start the measurement. The entire range of segments to be measured is captured without additional trigger event. The global trigger source is used.
				- SEGMent: The retrigger flag of each segment is evaluated. It defines whether a trigger event is required and which trigger source is used."""
		param = Conversions.enum_scalar_to_str(mode, enums.ListMode)
		self._core.io.write(f'TRIGger:LTE:MEASurement<Instance>:MEValuation:LIST:MODE {param}')

	# noinspection PyTypeChecker
	def get_nbandwidth(self) -> enums.BandwidthNarrow:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:LIST:NBANdwidth \n
		Snippet: value: enums.BandwidthNarrow = driver.trigger.lteMeas.multiEval.listPy.get_nbandwidth() \n
		Selects the trigger evaluation bandwidth for the retrigger source IFPNarrowband. Select the retrigger source via method
		RsCMPX_LteMeas.Configure.LteMeas.MultiEval.ListPy.Segment.Setup.set. \n
			:return: bandwidth: Evaluation bandwidth 10 MHz to 80 MHz
		"""
		response = self._core.io.query_str('TRIGger:LTE:MEASurement<Instance>:MEValuation:LIST:NBANdwidth?')
		return Conversions.str_to_scalar_enum(response, enums.BandwidthNarrow)

	def set_nbandwidth(self, bandwidth: enums.BandwidthNarrow) -> None:
		"""TRIGger:LTE:MEASurement<Instance>:MEValuation:LIST:NBANdwidth \n
		Snippet: driver.trigger.lteMeas.multiEval.listPy.set_nbandwidth(bandwidth = enums.BandwidthNarrow.M010) \n
		Selects the trigger evaluation bandwidth for the retrigger source IFPNarrowband. Select the retrigger source via method
		RsCMPX_LteMeas.Configure.LteMeas.MultiEval.ListPy.Segment.Setup.set. \n
			:param bandwidth: Evaluation bandwidth 10 MHz to 80 MHz
		"""
		param = Conversions.enum_scalar_to_str(bandwidth, enums.BandwidthNarrow)
		self._core.io.write(f'TRIGger:LTE:MEASurement<Instance>:MEValuation:LIST:NBANdwidth {param}')
