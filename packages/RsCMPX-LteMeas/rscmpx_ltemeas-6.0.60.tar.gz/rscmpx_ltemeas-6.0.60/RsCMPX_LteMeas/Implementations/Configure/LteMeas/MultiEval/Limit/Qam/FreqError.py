from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal import Conversions
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class FreqErrorCls:
	"""FreqError commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("freqError", core, parent)

	def set(self, frequency_error: float or bool, qAMmodOrder=repcap.QAMmodOrder.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM<ModOrder>:FERRor \n
		Snippet: driver.configure.lteMeas.multiEval.limit.qam.freqError.set(frequency_error = 1.0, qAMmodOrder = repcap.QAMmodOrder.Default) \n
		Defines an upper limit for the carrier frequency error for QAM modulations. \n
			:param frequency_error: (float or boolean) No help available
			:param qAMmodOrder: optional repeated capability selector. Default value: Qam16 (settable in the interface 'Qam')
		"""
		param = Conversions.decimal_or_bool_value_to_str(frequency_error)
		qAMmodOrder_cmd_val = self._cmd_group.get_repcap_cmd_value(qAMmodOrder, repcap.QAMmodOrder)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM{qAMmodOrder_cmd_val}:FERRor {param}')

	def get(self, qAMmodOrder=repcap.QAMmodOrder.Default) -> float or bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM<ModOrder>:FERRor \n
		Snippet: value: float or bool = driver.configure.lteMeas.multiEval.limit.qam.freqError.get(qAMmodOrder = repcap.QAMmodOrder.Default) \n
		Defines an upper limit for the carrier frequency error for QAM modulations. \n
			:param qAMmodOrder: optional repeated capability selector. Default value: Qam16 (settable in the interface 'Qam')
			:return: frequency_error: (float or boolean) No help available"""
		qAMmodOrder_cmd_val = self._cmd_group.get_repcap_cmd_value(qAMmodOrder, repcap.QAMmodOrder)
		response = self._core.io.query_str(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QAM{qAMmodOrder_cmd_val}:FERRor?')
		return Conversions.str_to_float_or_bool(response)
