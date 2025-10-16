from ........Internal.Core import Core
from ........Internal.CommandsGroup import CommandsGroup
from ........Internal.StructBase import StructBase
from ........Internal.ArgStruct import ArgStruct
from ........ import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class StandardDevCls:
	"""StandardDev commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("standardDev", core, parent)

	# noinspection PyTypeChecker
	class FetchStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Seg_Reliability: int: Reliability indicator for the segment
			- 3 Statist_Expired: int: Reached statistical length in subframes
			- 4 Out_Of_Tolerance: int: Percentage of measured subframes with failed limit check
			- 5 Tx_Power: float: TX power of the component carrier"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Seg_Reliability'),
			ArgStruct.scalar_int('Statist_Expired'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct.scalar_float('Tx_Power')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Seg_Reliability: int = None
			self.Statist_Expired: int = None
			self.Out_Of_Tolerance: int = None
			self.Tx_Power: float = None

	def fetch(self, segment=repcap.Segment.Default, carrierComponentB=repcap.CarrierComponentB.Default) -> FetchStruct:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:POWer:CC<no>:SDEViation \n
		Snippet: value: FetchStruct = driver.lteMeas.multiEval.listPy.segment.power.cc.standardDev.fetch(segment = repcap.Segment.Default, carrierComponentB = repcap.CarrierComponentB.Default) \n
		Return TX power results for component carrier CC<no> and a single segment in list mode. \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:param carrierComponentB: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Cc')
			:return: structure: for return value, see the help for FetchStruct structure arguments."""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		carrierComponentB_cmd_val = self._cmd_group.get_repcap_cmd_value(carrierComponentB, repcap.CarrierComponentB)
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:POWer:CC{carrierComponentB_cmd_val}:SDEViation?', self.__class__.FetchStruct())
