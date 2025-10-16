from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.Types import DataType
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct
from .......Internal.ArgSingleList import ArgSingleList
from .......Internal.ArgSingle import ArgSingle
from ....... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class EvmSymbolCls:
	"""EvmSymbol commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("evmSymbol", core, parent)

	def set(self, enable: bool, symbol: int, low_high: enums.LowHigh) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:EVMagnitude:EVMSymbol \n
		Snippet: driver.configure.lteMeas.multiEval.result.evMagnitude.evmSymbol.set(enable = False, symbol = 1, low_high = enums.LowHigh.HIGH) \n
		Enables or disables the measurement of EVM vs modulation symbol results and configures the scope of the measurement. \n
			:param enable: OFF: Do not measure the results. ON: Measure the results.
			:param symbol: SC-FDMA symbol to be evaluated.
			:param low_high: Low or high EVM window position.
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('enable', enable, DataType.Boolean), ArgSingle('symbol', symbol, DataType.Integer), ArgSingle('low_high', low_high, DataType.Enum, enums.LowHigh))
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:EVMagnitude:EVMSymbol {param}'.rstrip())

	# noinspection PyTypeChecker
	class EvmSymbolStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Enable: bool: OFF: Do not measure the results. ON: Measure the results.
			- 2 Symbol: int: SC-FDMA symbol to be evaluated.
			- 3 Low_High: enums.LowHigh: Low or high EVM window position."""
		__meta_args_list = [
			ArgStruct.scalar_bool('Enable'),
			ArgStruct.scalar_int('Symbol'),
			ArgStruct.scalar_enum('Low_High', enums.LowHigh)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Enable: bool = None
			self.Symbol: int = None
			self.Low_High: enums.LowHigh = None

	def get(self) -> EvmSymbolStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:EVMagnitude:EVMSymbol \n
		Snippet: value: EvmSymbolStruct = driver.configure.lteMeas.multiEval.result.evMagnitude.evmSymbol.get() \n
		Enables or disables the measurement of EVM vs modulation symbol results and configures the scope of the measurement. \n
			:return: structure: for return value, see the help for EvmSymbolStruct structure arguments."""
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RESult:EVMagnitude:EVMSymbol?', self.__class__.EvmSymbolStruct())
