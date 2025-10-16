from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.Types import DataType
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct
from .......Internal.ArgSingleList import ArgSingleList
from .......Internal.ArgSingle import ArgSingle
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class MerrorCls:
	"""Merror commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("merror", core, parent)

	def set(self, rms: float or bool, peak: float or bool, qAMmodOrder=repcap.QAMmodOrder.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM<ModOrder>:MERRor \n
		Snippet: driver.configure.lteMeas.multiEval.limit.qam.merror.set(rms = 1.0, peak = 1.0, qAMmodOrder = repcap.QAMmodOrder.Default) \n
		Defines upper limits for the RMS and peak values of the magnitude error, for QAM modulations. \n
			:param rms: (float or boolean) No help available
			:param peak: (float or boolean) No help available
			:param qAMmodOrder: optional repeated capability selector. Default value: Qam16 (settable in the interface 'Qam')
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('rms', rms, DataType.FloatExt), ArgSingle('peak', peak, DataType.FloatExt))
		qAMmodOrder_cmd_val = self._cmd_group.get_repcap_cmd_value(qAMmodOrder, repcap.QAMmodOrder)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM{qAMmodOrder_cmd_val}:MERRor {param}'.rstrip())

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

	def get(self, qAMmodOrder=repcap.QAMmodOrder.Default) -> MerrorStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM<ModOrder>:MERRor \n
		Snippet: value: MerrorStruct = driver.configure.lteMeas.multiEval.limit.qam.merror.get(qAMmodOrder = repcap.QAMmodOrder.Default) \n
		Defines upper limits for the RMS and peak values of the magnitude error, for QAM modulations. \n
			:param qAMmodOrder: optional repeated capability selector. Default value: Qam16 (settable in the interface 'Qam')
			:return: structure: for return value, see the help for MerrorStruct structure arguments."""
		qAMmodOrder_cmd_val = self._cmd_group.get_repcap_cmd_value(qAMmodOrder, repcap.QAMmodOrder)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM{qAMmodOrder_cmd_val}:MERRor?', self.__class__.MerrorStruct())
