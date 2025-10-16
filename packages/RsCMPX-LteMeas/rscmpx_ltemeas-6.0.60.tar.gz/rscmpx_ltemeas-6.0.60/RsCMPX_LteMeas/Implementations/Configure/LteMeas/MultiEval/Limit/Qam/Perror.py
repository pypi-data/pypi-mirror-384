from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.Types import DataType
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct
from .......Internal.ArgSingleList import ArgSingleList
from .......Internal.ArgSingle import ArgSingle
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class PerrorCls:
	"""Perror commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("perror", core, parent)

	def set(self, rms: float or bool, peak: float or bool, qAMmodOrder=repcap.QAMmodOrder.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM<ModOrder>:PERRor \n
		Snippet: driver.configure.lteMeas.multiEval.limit.qam.perror.set(rms = 1.0, peak = 1.0, qAMmodOrder = repcap.QAMmodOrder.Default) \n
		Defines symmetric limits for the RMS and peak values of the phase error, for QAM modulations. The limit check fails if
		the absolute value of the measured phase error exceeds the specified limit. \n
			:param rms: (float or boolean) No help available
			:param peak: (float or boolean) No help available
			:param qAMmodOrder: optional repeated capability selector. Default value: Qam16 (settable in the interface 'Qam')
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('rms', rms, DataType.FloatExt), ArgSingle('peak', peak, DataType.FloatExt))
		qAMmodOrder_cmd_val = self._cmd_group.get_repcap_cmd_value(qAMmodOrder, repcap.QAMmodOrder)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM{qAMmodOrder_cmd_val}:PERRor {param}'.rstrip())

	# noinspection PyTypeChecker
	class PerrorStruct(StructBase):
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

	def get(self, qAMmodOrder=repcap.QAMmodOrder.Default) -> PerrorStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM<ModOrder>:PERRor \n
		Snippet: value: PerrorStruct = driver.configure.lteMeas.multiEval.limit.qam.perror.get(qAMmodOrder = repcap.QAMmodOrder.Default) \n
		Defines symmetric limits for the RMS and peak values of the phase error, for QAM modulations. The limit check fails if
		the absolute value of the measured phase error exceeds the specified limit. \n
			:param qAMmodOrder: optional repeated capability selector. Default value: Qam16 (settable in the interface 'Qam')
			:return: structure: for return value, see the help for PerrorStruct structure arguments."""
		qAMmodOrder_cmd_val = self._cmd_group.get_repcap_cmd_value(qAMmodOrder, repcap.QAMmodOrder)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM{qAMmodOrder_cmd_val}:PERRor?', self.__class__.PerrorStruct())
