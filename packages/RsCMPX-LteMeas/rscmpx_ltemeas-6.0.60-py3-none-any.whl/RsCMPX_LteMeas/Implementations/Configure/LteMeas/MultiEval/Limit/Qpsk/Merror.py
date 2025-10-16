from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.Types import DataType
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct
from .......Internal.ArgSingleList import ArgSingleList
from .......Internal.ArgSingle import ArgSingle


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class MerrorCls:
	"""Merror commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("merror", core, parent)

	def set(self, rms: float or bool, peak: float or bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QPSK:MERRor \n
		Snippet: driver.configure.lteMeas.multiEval.limit.qpsk.merror.set(rms = 1.0, peak = 1.0) \n
		Defines upper limits for the RMS and peak values of the magnitude error for QPSK. \n
			:param rms: (float or boolean) No help available
			:param peak: (float or boolean) No help available
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('rms', rms, DataType.FloatExt), ArgSingle('peak', peak, DataType.FloatExt))
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QPSK:MERRor {param}'.rstrip())

	# noinspection PyTypeChecker
	class MerrorStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Rms: float or bool: No parameter help available
			- 2 Peak: float or bool: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_float_ext('Rms'),
			ArgStruct.scalar_float_ext('Peak')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Rms: float or bool = None
			self.Peak: float or bool = None

	def get(self) -> MerrorStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QPSK:MERRor \n
		Snippet: value: MerrorStruct = driver.configure.lteMeas.multiEval.limit.qpsk.merror.get() \n
		Defines upper limits for the RMS and peak values of the magnitude error for QPSK. \n
			:return: structure: for return value, see the help for MerrorStruct structure arguments."""
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QPSK:MERRor?', self.__class__.MerrorStruct())
