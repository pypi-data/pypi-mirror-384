from ....Internal.Core import Core
from ....Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class PrachCls:
	"""Prach commands group definition. 85 total commands, 5 Subgroups, 3 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("prach", core, parent)

	@property
	def state(self):
		"""state commands group. 1 Sub-classes, 1 commands."""
		if not hasattr(self, '_state'):
			from .State import StateCls
			self._state = StateCls(self._core, self._cmd_group)
		return self._state

	@property
	def trace(self):
		"""trace commands group. 7 Sub-classes, 0 commands."""
		if not hasattr(self, '_trace'):
			from .Trace import TraceCls
			self._trace = TraceCls(self._core, self._cmd_group)
		return self._trace

	@property
	def modulation(self):
		"""modulation commands group. 9 Sub-classes, 0 commands."""
		if not hasattr(self, '_modulation'):
			from .Modulation import ModulationCls
			self._modulation = ModulationCls(self._core, self._cmd_group)
		return self._modulation

	@property
	def evmSymbol(self):
		"""evmSymbol commands group. 4 Sub-classes, 0 commands."""
		if not hasattr(self, '_evmSymbol'):
			from .EvmSymbol import EvmSymbolCls
			self._evmSymbol = EvmSymbolCls(self._core, self._cmd_group)
		return self._evmSymbol

	@property
	def pdynamics(self):
		"""pdynamics commands group. 5 Sub-classes, 0 commands."""
		if not hasattr(self, '_pdynamics'):
			from .Pdynamics import PdynamicsCls
			self._pdynamics = PdynamicsCls(self._core, self._cmd_group)
		return self._pdynamics

	def initiate(self, opc_timeout_ms: int = -1) -> None:
		"""INITiate:LTE:MEASurement<Instance>:PRACh \n
		Snippet: driver.lteMeas.prach.initiate() \n
			INTRO_CMD_HELP: Starts, stops or aborts the measurement: \n
			- The INITiate:... command starts or restarts the measurement. The measurement enters the RUN state.
			- The STOP:... command halts the measurement immediately. The measurement enters the RDY state. Measurement results are kept. The resources remain allocated to the measurement.
			- The ABORt:... command halts the measurement immediately. The measurement enters the OFF state. All measurement values are set to NAV. Allocated resources are released.
		To query the current measurement state, use FETCh...STATe?. \n
			:param opc_timeout_ms: Maximum time to wait in milliseconds, valid only for this call."""
		self._core.io.write_with_opc(f'INITiate:LTE:MEASurement<Instance>:PRACh', opc_timeout_ms)
		# OpcSyncAllowed = true

	def stop(self) -> None:
		"""STOP:LTE:MEASurement<Instance>:PRACh \n
		Snippet: driver.lteMeas.prach.stop() \n
			INTRO_CMD_HELP: Starts, stops or aborts the measurement: \n
			- The INITiate:... command starts or restarts the measurement. The measurement enters the RUN state.
			- The STOP:... command halts the measurement immediately. The measurement enters the RDY state. Measurement results are kept. The resources remain allocated to the measurement.
			- The ABORt:... command halts the measurement immediately. The measurement enters the OFF state. All measurement values are set to NAV. Allocated resources are released.
		To query the current measurement state, use FETCh...STATe?. \n
		"""
		self._core.io.write(f'STOP:LTE:MEASurement<Instance>:PRACh')

	def stop_with_opc(self, opc_timeout_ms: int = -1) -> None:
		"""STOP:LTE:MEASurement<Instance>:PRACh \n
		Snippet: driver.lteMeas.prach.stop_with_opc() \n
			INTRO_CMD_HELP: Starts, stops or aborts the measurement: \n
			- The INITiate:... command starts or restarts the measurement. The measurement enters the RUN state.
			- The STOP:... command halts the measurement immediately. The measurement enters the RDY state. Measurement results are kept. The resources remain allocated to the measurement.
			- The ABORt:... command halts the measurement immediately. The measurement enters the OFF state. All measurement values are set to NAV. Allocated resources are released.
		To query the current measurement state, use FETCh...STATe?. \n
		Same as stop, but waits for the operation to complete before continuing further. Use the RsCMPX_LteMeas.utilities.opc_timeout_set() to set the timeout value. \n
			:param opc_timeout_ms: Maximum time to wait in milliseconds, valid only for this call."""
		self._core.io.write_with_opc(f'STOP:LTE:MEASurement<Instance>:PRACh', opc_timeout_ms)

	def abort(self, opc_timeout_ms: int = -1) -> None:
		"""ABORt:LTE:MEASurement<Instance>:PRACh \n
		Snippet: driver.lteMeas.prach.abort() \n
			INTRO_CMD_HELP: Starts, stops or aborts the measurement: \n
			- The INITiate:... command starts or restarts the measurement. The measurement enters the RUN state.
			- The STOP:... command halts the measurement immediately. The measurement enters the RDY state. Measurement results are kept. The resources remain allocated to the measurement.
			- The ABORt:... command halts the measurement immediately. The measurement enters the OFF state. All measurement values are set to NAV. Allocated resources are released.
		To query the current measurement state, use FETCh...STATe?. \n
			:param opc_timeout_ms: Maximum time to wait in milliseconds, valid only for this call."""
		self._core.io.write_with_opc(f'ABORt:LTE:MEASurement<Instance>:PRACh', opc_timeout_ms)
		# OpcSyncAllowed = true

	def clone(self) -> 'PrachCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = PrachCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
