from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal.StructBase import StructBase
from .....Internal.ArgStruct import ArgStruct


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ExtremeCls:
	"""Extreme commands group definition. 3 total commands, 0 Subgroups, 3 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("extreme", core, parent)

	# noinspection PyTypeChecker
	class ResultData(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Out_Of_Tolerance: int: Out of tolerance result, i.e. the percentage of measurement intervals of the statistic count for modulation measurements exceeding the specified modulation limits.
			- 3 Evm_Rms_Low: float: EVM RMS value, low EVM window position
			- 4 Evm_Rms_High: float: EVM RMS value, high EVM window position
			- 5 Evm_Peak_Low: float: EVM peak value, low EVM window position
			- 6 Evm_Peak_High: float: EVM peak value, high EVM window position
			- 7 Mag_Error_Rms_Low: float: Magnitude error RMS value, low EVM window position
			- 8 Mag_Error_Rms_High: float: Magnitude error RMS value, low EVM window position
			- 9 Mag_Error_Peak_Low: float: Magnitude error peak value, low EVM window position
			- 10 Mag_Err_Peak_High: float: Magnitude error peak value, high EVM window position
			- 11 Ph_Error_Rms_Low: float: Phase error RMS value, low EVM window position
			- 12 Ph_Error_Rms_High: float: Phase error RMS value, high EVM window position
			- 13 Ph_Error_Peak_Low: float: Phase error peak value, low EVM window position
			- 14 Ph_Error_Peak_High: float: Phase error peak value, high EVM window position
			- 15 Iq_Offset: float: I/Q origin offset
			- 16 Frequency_Error: float: Carrier frequency error
			- 17 Timing_Error: float: Time error
			- 18 Tx_Power_Minimum: float: Minimum user equipment power
			- 19 Tx_Power_Maximum: float: Maximum user equipment power
			- 20 Peak_Power_Min: float: Minimum user equipment peak power
			- 21 Peak_Power_Max: float: Maximum user equipment peak power
			- 22 Psd_Minimum: float: No parameter help available
			- 23 Psd_Maximum: float: No parameter help available
			- 24 Evm_Dmrs_Low: float: EVM DMRS value, low EVM window position
			- 25 Evm_Dmrs_High: float: EVM DMRS value, high EVM window position
			- 26 Mag_Err_Dmrs_Low: float: Magnitude error DMRS value, low EVM window position
			- 27 Mag_Err_Dmrs_High: float: Magnitude error DMRS value, high EVM window position
			- 28 Ph_Error_Dmrs_Low: float: Phase error DMRS value, low EVM window position
			- 29 Ph_Error_Dmrs_High: float: Phase error DMRS value, high EVM window position
			- 30 Iq_Gain_Imbalance: float: Gain imbalance
			- 31 Iq_Quadrature_Err: float: Quadrature error
			- 32 Evm_Srs: float: No parameter help available
			- 33 Evm_Srs_2: float: EVM value, second SRS symbol
			- 34 Power_Srs_1_Min: float: No parameter help available
			- 35 Power_Srs_1_Max: float: No parameter help available
			- 36 Power_Srs_2_Min: float: No parameter help available
			- 37 Power_Srs_2_Max: float: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct.scalar_float('Evm_Rms_Low'),
			ArgStruct.scalar_float('Evm_Rms_High'),
			ArgStruct.scalar_float('Evm_Peak_Low'),
			ArgStruct.scalar_float('Evm_Peak_High'),
			ArgStruct.scalar_float('Mag_Error_Rms_Low'),
			ArgStruct.scalar_float('Mag_Error_Rms_High'),
			ArgStruct.scalar_float('Mag_Error_Peak_Low'),
			ArgStruct.scalar_float('Mag_Err_Peak_High'),
			ArgStruct.scalar_float('Ph_Error_Rms_Low'),
			ArgStruct.scalar_float('Ph_Error_Rms_High'),
			ArgStruct.scalar_float('Ph_Error_Peak_Low'),
			ArgStruct.scalar_float('Ph_Error_Peak_High'),
			ArgStruct.scalar_float('Iq_Offset'),
			ArgStruct.scalar_float('Frequency_Error'),
			ArgStruct.scalar_float('Timing_Error'),
			ArgStruct.scalar_float('Tx_Power_Minimum'),
			ArgStruct.scalar_float('Tx_Power_Maximum'),
			ArgStruct.scalar_float('Peak_Power_Min'),
			ArgStruct.scalar_float('Peak_Power_Max'),
			ArgStruct.scalar_float('Psd_Minimum'),
			ArgStruct.scalar_float('Psd_Maximum'),
			ArgStruct.scalar_float('Evm_Dmrs_Low'),
			ArgStruct.scalar_float('Evm_Dmrs_High'),
			ArgStruct.scalar_float('Mag_Err_Dmrs_Low'),
			ArgStruct.scalar_float('Mag_Err_Dmrs_High'),
			ArgStruct.scalar_float('Ph_Error_Dmrs_Low'),
			ArgStruct.scalar_float('Ph_Error_Dmrs_High'),
			ArgStruct.scalar_float('Iq_Gain_Imbalance'),
			ArgStruct.scalar_float('Iq_Quadrature_Err'),
			ArgStruct.scalar_float('Evm_Srs'),
			ArgStruct.scalar_float('Evm_Srs_2'),
			ArgStruct.scalar_float('Power_Srs_1_Min'),
			ArgStruct.scalar_float('Power_Srs_1_Max'),
			ArgStruct.scalar_float('Power_Srs_2_Min'),
			ArgStruct.scalar_float('Power_Srs_2_Max')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Out_Of_Tolerance: int = None
			self.Evm_Rms_Low: float = None
			self.Evm_Rms_High: float = None
			self.Evm_Peak_Low: float = None
			self.Evm_Peak_High: float = None
			self.Mag_Error_Rms_Low: float = None
			self.Mag_Error_Rms_High: float = None
			self.Mag_Error_Peak_Low: float = None
			self.Mag_Err_Peak_High: float = None
			self.Ph_Error_Rms_Low: float = None
			self.Ph_Error_Rms_High: float = None
			self.Ph_Error_Peak_Low: float = None
			self.Ph_Error_Peak_High: float = None
			self.Iq_Offset: float = None
			self.Frequency_Error: float = None
			self.Timing_Error: float = None
			self.Tx_Power_Minimum: float = None
			self.Tx_Power_Maximum: float = None
			self.Peak_Power_Min: float = None
			self.Peak_Power_Max: float = None
			self.Psd_Minimum: float = None
			self.Psd_Maximum: float = None
			self.Evm_Dmrs_Low: float = None
			self.Evm_Dmrs_High: float = None
			self.Mag_Err_Dmrs_Low: float = None
			self.Mag_Err_Dmrs_High: float = None
			self.Ph_Error_Dmrs_Low: float = None
			self.Ph_Error_Dmrs_High: float = None
			self.Iq_Gain_Imbalance: float = None
			self.Iq_Quadrature_Err: float = None
			self.Evm_Srs: float = None
			self.Evm_Srs_2: float = None
			self.Power_Srs_1_Min: float = None
			self.Power_Srs_1_Max: float = None
			self.Power_Srs_2_Min: float = None
			self.Power_Srs_2_Max: float = None

	def read(self) -> ResultData:
		"""READ:LTE:MEASurement<Instance>:MEValuation:MODulation:EXTReme \n
		Snippet: value: ResultData = driver.lteMeas.multiEval.modulation.extreme.read() \n
		Return the extreme single value results. The values described below are returned by FETCh and READ commands. A CALCulate
		command returns limit check results instead, one value for each result listed below. \n
			:return: structure: for return value, see the help for ResultData structure arguments."""
		return self._core.io.query_struct(f'READ:LTE:MEASurement<Instance>:MEValuation:MODulation:EXTReme?', self.__class__.ResultData())

	def fetch(self) -> ResultData:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:MODulation:EXTReme \n
		Snippet: value: ResultData = driver.lteMeas.multiEval.modulation.extreme.fetch() \n
		Return the extreme single value results. The values described below are returned by FETCh and READ commands. A CALCulate
		command returns limit check results instead, one value for each result listed below. \n
			:return: structure: for return value, see the help for ResultData structure arguments."""
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:MODulation:EXTReme?', self.__class__.ResultData())

	# noinspection PyTypeChecker
	class CalculateStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Out_Of_Tolerance: int: Out of tolerance result, i.e. the percentage of measurement intervals of the statistic count for modulation measurements exceeding the specified modulation limits.
			- 3 Evm_Rms_Low: float or bool: EVM RMS value, low EVM window position
			- 4 Evm_Rms_High: float or bool: EVM RMS value, high EVM window position
			- 5 Evm_Peak_Low: float or bool: EVM peak value, low EVM window position
			- 6 Evm_Peak_High: float or bool: EVM peak value, high EVM window position
			- 7 Mag_Error_Rms_Low: float or bool: Magnitude error RMS value, low EVM window position
			- 8 Mag_Error_Rms_High: float or bool: Magnitude error RMS value, low EVM window position
			- 9 Mag_Error_Peak_Low: float or bool: Magnitude error peak value, low EVM window position
			- 10 Mag_Err_Peak_High: float or bool: Magnitude error peak value, high EVM window position
			- 11 Ph_Error_Rms_Low: float or bool: Phase error RMS value, low EVM window position
			- 12 Ph_Error_Rms_High: float or bool: Phase error RMS value, high EVM window position
			- 13 Ph_Error_Peak_Low: float or bool: Phase error peak value, low EVM window position
			- 14 Ph_Error_Peak_High: float or bool: Phase error peak value, high EVM window position
			- 15 Iq_Offset: float or bool: I/Q origin offset
			- 16 Frequency_Error: float or bool: Carrier frequency error
			- 17 Timing_Error: float or bool: Time error
			- 18 Tx_Power_Minimum: float or bool: Minimum user equipment power
			- 19 Tx_Power_Maximum: float or bool: Maximum user equipment power
			- 20 Peak_Power_Min: float or bool: Minimum user equipment peak power
			- 21 Peak_Power_Max: float or bool: Maximum user equipment peak power
			- 22 Psd_Minimum: float or bool: No parameter help available
			- 23 Psd_Maximum: float or bool: No parameter help available
			- 24 Evm_Dmrs_Low: float or bool: EVM DMRS value, low EVM window position
			- 25 Evm_Dmrs_High: float or bool: EVM DMRS value, high EVM window position
			- 26 Mag_Err_Dmrs_Low: float or bool: Magnitude error DMRS value, low EVM window position
			- 27 Mag_Err_Dmrs_High: float or bool: Magnitude error DMRS value, high EVM window position
			- 28 Ph_Error_Dmrs_Low: float or bool: Phase error DMRS value, low EVM window position
			- 29 Ph_Error_Dmrs_High: float or bool: Phase error DMRS value, high EVM window position
			- 30 Iq_Gain_Imbalance: float or bool: Gain imbalance
			- 31 Iq_Quadrature_Err: float or bool: Quadrature error
			- 32 Evm_Srs: float: No parameter help available
			- 33 Evm_Srs_2: float: EVM value, second SRS symbol
			- 34 Power_Srs_1_Min: float or bool: No parameter help available
			- 35 Power_Srs_1_Max: float or bool: No parameter help available
			- 36 Power_Srs_2_Min: float or bool: No parameter help available
			- 37 Power_Srs_2_Max: float or bool: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct.scalar_float_ext('Evm_Rms_Low'),
			ArgStruct.scalar_float_ext('Evm_Rms_High'),
			ArgStruct.scalar_float_ext('Evm_Peak_Low'),
			ArgStruct.scalar_float_ext('Evm_Peak_High'),
			ArgStruct.scalar_float_ext('Mag_Error_Rms_Low'),
			ArgStruct.scalar_float_ext('Mag_Error_Rms_High'),
			ArgStruct.scalar_float_ext('Mag_Error_Peak_Low'),
			ArgStruct.scalar_float_ext('Mag_Err_Peak_High'),
			ArgStruct.scalar_float_ext('Ph_Error_Rms_Low'),
			ArgStruct.scalar_float_ext('Ph_Error_Rms_High'),
			ArgStruct.scalar_float_ext('Ph_Error_Peak_Low'),
			ArgStruct.scalar_float_ext('Ph_Error_Peak_High'),
			ArgStruct.scalar_float_ext('Iq_Offset'),
			ArgStruct.scalar_float_ext('Frequency_Error'),
			ArgStruct.scalar_float_ext('Timing_Error'),
			ArgStruct.scalar_float_ext('Tx_Power_Minimum'),
			ArgStruct.scalar_float_ext('Tx_Power_Maximum'),
			ArgStruct.scalar_float_ext('Peak_Power_Min'),
			ArgStruct.scalar_float_ext('Peak_Power_Max'),
			ArgStruct.scalar_float_ext('Psd_Minimum'),
			ArgStruct.scalar_float_ext('Psd_Maximum'),
			ArgStruct.scalar_float_ext('Evm_Dmrs_Low'),
			ArgStruct.scalar_float_ext('Evm_Dmrs_High'),
			ArgStruct.scalar_float_ext('Mag_Err_Dmrs_Low'),
			ArgStruct.scalar_float_ext('Mag_Err_Dmrs_High'),
			ArgStruct.scalar_float_ext('Ph_Error_Dmrs_Low'),
			ArgStruct.scalar_float_ext('Ph_Error_Dmrs_High'),
			ArgStruct.scalar_float_ext('Iq_Gain_Imbalance'),
			ArgStruct.scalar_float_ext('Iq_Quadrature_Err'),
			ArgStruct.scalar_float('Evm_Srs'),
			ArgStruct.scalar_float('Evm_Srs_2'),
			ArgStruct.scalar_float_ext('Power_Srs_1_Min'),
			ArgStruct.scalar_float_ext('Power_Srs_1_Max'),
			ArgStruct.scalar_float_ext('Power_Srs_2_Min'),
			ArgStruct.scalar_float_ext('Power_Srs_2_Max')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Out_Of_Tolerance: int = None
			self.Evm_Rms_Low: float or bool = None
			self.Evm_Rms_High: float or bool = None
			self.Evm_Peak_Low: float or bool = None
			self.Evm_Peak_High: float or bool = None
			self.Mag_Error_Rms_Low: float or bool = None
			self.Mag_Error_Rms_High: float or bool = None
			self.Mag_Error_Peak_Low: float or bool = None
			self.Mag_Err_Peak_High: float or bool = None
			self.Ph_Error_Rms_Low: float or bool = None
			self.Ph_Error_Rms_High: float or bool = None
			self.Ph_Error_Peak_Low: float or bool = None
			self.Ph_Error_Peak_High: float or bool = None
			self.Iq_Offset: float or bool = None
			self.Frequency_Error: float or bool = None
			self.Timing_Error: float or bool = None
			self.Tx_Power_Minimum: float or bool = None
			self.Tx_Power_Maximum: float or bool = None
			self.Peak_Power_Min: float or bool = None
			self.Peak_Power_Max: float or bool = None
			self.Psd_Minimum: float or bool = None
			self.Psd_Maximum: float or bool = None
			self.Evm_Dmrs_Low: float or bool = None
			self.Evm_Dmrs_High: float or bool = None
			self.Mag_Err_Dmrs_Low: float or bool = None
			self.Mag_Err_Dmrs_High: float or bool = None
			self.Ph_Error_Dmrs_Low: float or bool = None
			self.Ph_Error_Dmrs_High: float or bool = None
			self.Iq_Gain_Imbalance: float or bool = None
			self.Iq_Quadrature_Err: float or bool = None
			self.Evm_Srs: float = None
			self.Evm_Srs_2: float = None
			self.Power_Srs_1_Min: float or bool = None
			self.Power_Srs_1_Max: float or bool = None
			self.Power_Srs_2_Min: float or bool = None
			self.Power_Srs_2_Max: float or bool = None

	def calculate(self) -> CalculateStruct:
		"""CALCulate:LTE:MEASurement<Instance>:MEValuation:MODulation:EXTReme \n
		Snippet: value: CalculateStruct = driver.lteMeas.multiEval.modulation.extreme.calculate() \n
		Return the extreme single value results. The values described below are returned by FETCh and READ commands. A CALCulate
		command returns limit check results instead, one value for each result listed below. \n
			:return: structure: for return value, see the help for CalculateStruct structure arguments."""
		return self._core.io.query_struct(f'CALCulate:LTE:MEASurement<Instance>:MEValuation:MODulation:EXTReme?', self.__class__.CalculateStruct())
