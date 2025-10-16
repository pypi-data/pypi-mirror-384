from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal import Conversions
from ......Internal.StructBase import StructBase
from ......Internal.ArgStruct import ArgStruct


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ResultCls:
	"""Result commands group definition. 16 total commands, 1 Subgroups, 14 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("result", core, parent)

	@property
	def evMagnitude(self):
		"""evMagnitude commands group. 1 Sub-classes, 1 commands."""
		if not hasattr(self, '_evMagnitude'):
			from .EvMagnitude import EvMagnitudeCls
			self._evMagnitude = EvMagnitudeCls(self._core, self._cmd_group)
		return self._evMagnitude

	# noinspection PyTypeChecker
	class AllStruct(StructBase):  # From WriteStructDefinition CmdPropertyTemplate.xml
		"""Structure for setting input parameters. Contains optional set arguments. Fields: \n
			- Evm: bool: Error vector magnitude OFF: Do not evaluate the results. ON: Evaluate the results.
			- Magnitude_Error: bool: No parameter help available
			- Phase_Error: bool: No parameter help available
			- Inband_Emissions: bool: No parameter help available
			- Evm_Versus_C: bool: EVM vs subcarrier
			- Iq: bool: I/Q constellation diagram
			- Equ_Spec_Flatness: bool: Equalizer spectrum flatness
			- Tx_Measurement: bool: TX measurement statistical overview
			- Spec_Em_Mask: bool: Spectrum emission mask
			- Aclr: bool: Adjacent channel leakage power ratio
			- Rb_Alloc_Table: bool: Optional setting parameter. Resource block allocation table
			- Power_Monitor: bool: No parameter help available
			- Bler: bool: Optional setting parameter. Not supported
			- Power_Dynamics: bool: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_bool('Evm'),
			ArgStruct.scalar_bool('Magnitude_Error'),
			ArgStruct.scalar_bool('Phase_Error'),
			ArgStruct.scalar_bool('Inband_Emissions'),
			ArgStruct.scalar_bool('Evm_Versus_C'),
			ArgStruct.scalar_bool('Iq'),
			ArgStruct.scalar_bool('Equ_Spec_Flatness'),
			ArgStruct.scalar_bool('Tx_Measurement'),
			ArgStruct.scalar_bool('Spec_Em_Mask'),
			ArgStruct.scalar_bool('Aclr'),
			ArgStruct.scalar_bool_optional('Rb_Alloc_Table'),
			ArgStruct.scalar_bool_optional('Power_Monitor'),
			ArgStruct.scalar_bool_optional('Bler'),
			ArgStruct.scalar_bool_optional('Power_Dynamics')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Evm: bool=None
			self.Magnitude_Error: bool=None
			self.Phase_Error: bool=None
			self.Inband_Emissions: bool=None
			self.Evm_Versus_C: bool=None
			self.Iq: bool=None
			self.Equ_Spec_Flatness: bool=None
			self.Tx_Measurement: bool=None
			self.Spec_Em_Mask: bool=None
			self.Aclr: bool=None
			self.Rb_Alloc_Table: bool=None
			self.Power_Monitor: bool=None
			self.Bler: bool=None
			self.Power_Dynamics: bool=None

	def get_all(self) -> AllStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult[:ALL] \n
		Snippet: value: AllStruct = driver.configure.lteMeas.multiEval.result.get_all() \n
		Enables or disables the evaluation of results in the multi-evaluation measurement. This command combines most other
		CONFigure:LTE:MEAS<i>:MEValuation:RESult... commands. \n
			:return: structure: for return value, see the help for AllStruct structure arguments.
		"""
		return self._core.io.query_struct('CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:ALL?', self.__class__.AllStruct())

	def set_all(self, value: AllStruct) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult[:ALL] \n
		Snippet with structure: \n
		structure = driver.configure.lteMeas.multiEval.result.AllStruct() \n
		structure.Evm: bool = False \n
		structure.Magnitude_Error: bool = False \n
		structure.Phase_Error: bool = False \n
		structure.Inband_Emissions: bool = False \n
		structure.Evm_Versus_C: bool = False \n
		structure.Iq: bool = False \n
		structure.Equ_Spec_Flatness: bool = False \n
		structure.Tx_Measurement: bool = False \n
		structure.Spec_Em_Mask: bool = False \n
		structure.Aclr: bool = False \n
		structure.Rb_Alloc_Table: bool = False \n
		structure.Power_Monitor: bool = False \n
		structure.Bler: bool = False \n
		structure.Power_Dynamics: bool = False \n
		driver.configure.lteMeas.multiEval.result.set_all(value = structure) \n
		Enables or disables the evaluation of results in the multi-evaluation measurement. This command combines most other
		CONFigure:LTE:MEAS<i>:MEValuation:RESult... commands. \n
			:param value: see the help for AllStruct structure arguments.
		"""
		self._core.io.write_struct('CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:ALL', value)

	def get_merror(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:MERRor \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.result.get_merror() \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:return: enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:MERRor?')
		return Conversions.str_to_bool(response)

	def set_merror(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:MERRor \n
		Snippet: driver.configure.lteMeas.multiEval.result.set_merror(enable = False) \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:param enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:MERRor {param}')

	def get_perror(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:PERRor \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.result.get_perror() \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:return: enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:PERRor?')
		return Conversions.str_to_bool(response)

	def set_perror(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:PERRor \n
		Snippet: driver.configure.lteMeas.multiEval.result.set_perror(enable = False) \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:param enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:PERRor {param}')

	def get_iemissions(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:IEMissions \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.result.get_iemissions() \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:return: enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:IEMissions?')
		return Conversions.str_to_bool(response)

	def set_iemissions(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:IEMissions \n
		Snippet: driver.configure.lteMeas.multiEval.result.set_iemissions(enable = False) \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:param enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:IEMissions {param}')

	def get_evmc(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:EVMC \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.result.get_evmc() \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:return: enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:EVMC?')
		return Conversions.str_to_bool(response)

	def set_evmc(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:EVMC \n
		Snippet: driver.configure.lteMeas.multiEval.result.set_evmc(enable = False) \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:param enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:EVMC {param}')

	def get_es_flatness(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:ESFLatness \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.result.get_es_flatness() \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:return: enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:ESFLatness?')
		return Conversions.str_to_bool(response)

	def set_es_flatness(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:ESFLatness \n
		Snippet: driver.configure.lteMeas.multiEval.result.set_es_flatness(enable = False) \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:param enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:ESFLatness {param}')

	def get_txm(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:TXM \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.result.get_txm() \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:return: enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:TXM?')
		return Conversions.str_to_bool(response)

	def set_txm(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:TXM \n
		Snippet: driver.configure.lteMeas.multiEval.result.set_txm(enable = False) \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:param enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:TXM {param}')

	def get_iq(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:IQ \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.result.get_iq() \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:return: enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:IQ?')
		return Conversions.str_to_bool(response)

	def set_iq(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:IQ \n
		Snippet: driver.configure.lteMeas.multiEval.result.set_iq(enable = False) \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:param enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:IQ {param}')

	def get_se_mask(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:SEMask \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.result.get_se_mask() \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:return: enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:SEMask?')
		return Conversions.str_to_bool(response)

	def set_se_mask(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:SEMask \n
		Snippet: driver.configure.lteMeas.multiEval.result.set_se_mask(enable = False) \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:param enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:SEMask {param}')

	def get_aclr(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:ACLR \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.result.get_aclr() \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:return: enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:ACLR?')
		return Conversions.str_to_bool(response)

	def set_aclr(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:ACLR \n
		Snippet: driver.configure.lteMeas.multiEval.result.set_aclr(enable = False) \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:param enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:ACLR {param}')

	def get_rba_table(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:RBATable \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.result.get_rba_table() \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:return: enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:RBATable?')
		return Conversions.str_to_bool(response)

	def set_rba_table(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:RBATable \n
		Snippet: driver.configure.lteMeas.multiEval.result.set_rba_table(enable = False) \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:param enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:RBATable {param}')

	def get_pmonitor(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:PMONitor \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.result.get_pmonitor() \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:return: enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:PMONitor?')
		return Conversions.str_to_bool(response)

	def set_pmonitor(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:PMONitor \n
		Snippet: driver.configure.lteMeas.multiEval.result.set_pmonitor(enable = False) \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:param enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:PMONitor {param}')

	def get_pdynamics(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:PDYNamics \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.result.get_pdynamics() \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:return: enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:PDYNamics?')
		return Conversions.str_to_bool(response)

	def set_pdynamics(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:PDYNamics \n
		Snippet: driver.configure.lteMeas.multiEval.result.set_pdynamics(enable = False) \n
		Enables or disables the evaluation of results in the multi-evaluation measurement.
			Table Header: Mnemonic / Description \n
			- EVMagnitude / Error vector magnitude
			- MERRor / Magnitude error
			- IEMissions / In-band emissions
			- ESFLatness / Equalizer spectrum flatness
			- SEMask / Spectrum emission mask
			- RBATable / Resource block allocation table
			-
			- EVMC / EVM vs subcarrier
			- PERRor / Phase error
			- IQ / I/Q constellation diagram
			- TXM / TX meas. statistical overview
			- ACLR / Adj. channel leakage power ratio
			- PMONitor / Power monitor
			- PDYNamics / Power dynamics
		For reset values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Result.all. \n
			:param enable: OFF: Do not evaluate the results. ON: Evaluate the results.
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:PDYNamics {param}')

	def get_bler(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:BLER \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.result.get_bler() \n
		No command help available \n
			:return: enable: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:BLER?')
		return Conversions.str_to_bool(response)

	def set_bler(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:BLER \n
		Snippet: driver.configure.lteMeas.multiEval.result.set_bler(enable = False) \n
		No command help available \n
			:param enable: No help available
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:BLER {param}')

	def clone(self) -> 'ResultCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = ResultCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
