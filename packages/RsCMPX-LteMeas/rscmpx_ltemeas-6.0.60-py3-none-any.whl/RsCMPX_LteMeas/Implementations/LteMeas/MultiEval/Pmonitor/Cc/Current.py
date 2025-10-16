from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal.StructBase import StructBase
from ......Internal.ArgStruct import ArgStruct
from ...... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class CurrentCls:
	"""Current commands group definition. 2 total commands, 0 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("current", core, parent)

	# noinspection PyTypeChecker
	class ResultData(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Out_Of_Tolerance: int: Out of tolerance result, i.e. the percentage of measurement intervals of the statistic count for power measurements exceeding the specified power limits.
			- 3 Tx_Power: float: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct.scalar_float('Tx_Power')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Out_Of_Tolerance: int = None
			self.Tx_Power: float = None

	def read(self, carrierComponent=repcap.CarrierComponent.Default) -> ResultData:
		"""READ:LTE:MEASurement<Instance>:MEValuation:PMONitor:CC<Nr>:CURRent \n
		Snippet: value: ResultData = driver.lteMeas.multiEval.pmonitor.cc.current.read(carrierComponent = repcap.CarrierComponent.Default) \n
		Returns the TX power of carrier CC<no>. \n
			:param carrierComponent: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Cc')
			:return: structure: for return value, see the help for ResultData structure arguments."""
		carrierComponent_cmd_val = self._cmd_group.get_repcap_cmd_value(carrierComponent, repcap.CarrierComponent)
		return self._core.io.query_struct(f'READ:LTE:MEASurement<Instance>:MEValuation:PMONitor:CC{carrierComponent_cmd_val}:CURRent?', self.__class__.ResultData())

	def fetch(self, carrierComponent=repcap.CarrierComponent.Default) -> ResultData:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:PMONitor:CC<Nr>:CURRent \n
		Snippet: value: ResultData = driver.lteMeas.multiEval.pmonitor.cc.current.fetch(carrierComponent = repcap.CarrierComponent.Default) \n
		Returns the TX power of carrier CC<no>. \n
			:param carrierComponent: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Cc')
			:return: structure: for return value, see the help for ResultData structure arguments."""
		carrierComponent_cmd_val = self._cmd_group.get_repcap_cmd_value(carrierComponent, repcap.CarrierComponent)
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:PMONitor:CC{carrierComponent_cmd_val}:CURRent?', self.__class__.ResultData())
