from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal.Types import DataType
from ......Internal.StructBase import StructBase
from ......Internal.ArgStruct import ArgStruct
from ......Internal.ArgSingleList import ArgSingleList
from ......Internal.ArgSingle import ArgSingle


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class PdynamicsCls:
	"""Pdynamics commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("pdynamics", core, parent)

	def set(self, enable: bool, on_power_upper: float, on_power_lower: float, off_power_upper: float) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:SRS:LIMit:PDYNamics \n
		Snippet: driver.configure.lteMeas.srs.limit.pdynamics.set(enable = False, on_power_upper = 1.0, on_power_lower = 1.0, off_power_upper = 1.0) \n
		Defines limits for the ON power and OFF power determined with the power dynamics measurement. \n
			:param enable: OFF: disables the limit check ON: enables the limit check
			:param on_power_upper: Upper limit for the ON power
			:param on_power_lower: Lower limit for the ON power
			:param off_power_upper: Upper limit for the OFF power
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('enable', enable, DataType.Boolean), ArgSingle('on_power_upper', on_power_upper, DataType.Float), ArgSingle('on_power_lower', on_power_lower, DataType.Float), ArgSingle('off_power_upper', off_power_upper, DataType.Float))
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:SRS:LIMit:PDYNamics {param}'.rstrip())

	# noinspection PyTypeChecker
	class PdynamicsStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Enable: bool: OFF: disables the limit check ON: enables the limit check
			- 2 On_Power_Upper: float: Upper limit for the ON power
			- 3 On_Power_Lower: float: Lower limit for the ON power
			- 4 Off_Power_Upper: float: Upper limit for the OFF power"""
		__meta_args_list = [
			ArgStruct.scalar_bool('Enable'),
			ArgStruct.scalar_float('On_Power_Upper'),
			ArgStruct.scalar_float('On_Power_Lower'),
			ArgStruct.scalar_float('Off_Power_Upper')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Enable: bool = None
			self.On_Power_Upper: float = None
			self.On_Power_Lower: float = None
			self.Off_Power_Upper: float = None

	def get(self) -> PdynamicsStruct:
		"""CONFigure:LTE:MEASurement<Instance>:SRS:LIMit:PDYNamics \n
		Snippet: value: PdynamicsStruct = driver.configure.lteMeas.srs.limit.pdynamics.get() \n
		Defines limits for the ON power and OFF power determined with the power dynamics measurement. \n
			:return: structure: for return value, see the help for PdynamicsStruct structure arguments."""
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:SRS:LIMit:PDYNamics?', self.__class__.PdynamicsStruct())
