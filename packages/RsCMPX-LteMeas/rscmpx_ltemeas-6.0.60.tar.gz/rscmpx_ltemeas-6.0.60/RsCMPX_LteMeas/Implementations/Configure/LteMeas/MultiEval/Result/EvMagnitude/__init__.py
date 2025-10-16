from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class EvMagnitudeCls:
	"""EvMagnitude commands group definition. 2 total commands, 1 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("evMagnitude", core, parent)

	@property
	def evmSymbol(self):
		"""evmSymbol commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_evmSymbol'):
			from .EvmSymbol import EvmSymbolCls
			self._evmSymbol = EvmSymbolCls(self._core, self._cmd_group)
		return self._evmSymbol

	def get_value(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:EVMagnitude \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.result.evMagnitude.get_value() \n
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
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:EVMagnitude?')
		return Conversions.str_to_bool(response)

	def set_value(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:EVMagnitude \n
		Snippet: driver.configure.lteMeas.multiEval.result.evMagnitude.set_value(enable = False) \n
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
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:EVMagnitude {param}')

	def clone(self) -> 'EvMagnitudeCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = EvMagnitudeCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
