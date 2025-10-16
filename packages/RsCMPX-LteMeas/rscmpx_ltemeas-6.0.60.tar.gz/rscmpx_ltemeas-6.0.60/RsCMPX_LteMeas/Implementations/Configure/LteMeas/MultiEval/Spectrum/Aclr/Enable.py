from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.Types import DataType
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct
from .......Internal.ArgSingleList import ArgSingleList
from .......Internal.ArgSingle import ArgSingle


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class EnableCls:
	"""Enable commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("enable", core, parent)

	def set(self, utra_1: bool, utra_2: bool, eutra: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SPECtrum:ACLR:ENABle \n
		Snippet: driver.configure.lteMeas.multiEval.spectrum.aclr.enable.set(utra_1 = False, utra_2 = False, eutra = False) \n
		Enables or disables the evaluation of the first adjacent UTRA channels, second adjacent UTRA channels and first adjacent
		E-UTRA channels. \n
			:param utra_1: No help available
			:param utra_2: No help available
			:param eutra: No help available
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('utra_1', utra_1, DataType.Boolean), ArgSingle('utra_2', utra_2, DataType.Boolean), ArgSingle('eutra', eutra, DataType.Boolean))
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:SPECtrum:ACLR:ENABle {param}'.rstrip())

	# noinspection PyTypeChecker
	class EnableStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Utra_1: bool: No parameter help available
			- 2 Utra_2: bool: No parameter help available
			- 3 Eutra: bool: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_bool('Utra_1'),
			ArgStruct.scalar_bool('Utra_2'),
			ArgStruct.scalar_bool('Eutra')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Utra_1: bool = None
			self.Utra_2: bool = None
			self.Eutra: bool = None

	def get(self) -> EnableStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SPECtrum:ACLR:ENABle \n
		Snippet: value: EnableStruct = driver.configure.lteMeas.multiEval.spectrum.aclr.enable.get() \n
		Enables or disables the evaluation of the first adjacent UTRA channels, second adjacent UTRA channels and first adjacent
		E-UTRA channels. \n
			:return: structure: for return value, see the help for EnableStruct structure arguments."""
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:SPECtrum:ACLR:ENABle?', self.__class__.EnableStruct())
