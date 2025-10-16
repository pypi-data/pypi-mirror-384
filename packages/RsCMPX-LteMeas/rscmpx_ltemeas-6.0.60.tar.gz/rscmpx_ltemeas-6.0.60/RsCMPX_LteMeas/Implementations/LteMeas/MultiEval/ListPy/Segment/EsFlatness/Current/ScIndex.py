from ........Internal.Core import Core
from ........Internal.CommandsGroup import CommandsGroup
from ........Internal.StructBase import StructBase
from ........Internal.ArgStruct import ArgStruct
from ........ import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ScIndexCls:
	"""ScIndex commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("scIndex", core, parent)

	# noinspection PyTypeChecker
	class FetchStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Seg_Reliability: int: Reliability indicator for the segment
			- 3 Statist_Expired: int: Reached statistical length in slots
			- 4 Out_Of_Tolerance: int: Percentage of measured subframes with failed limit check
			- 5 Maximum_1: int: SC index of max (range 1)
			- 6 Minimum_1: int: SC index of min (range 1)
			- 7 Maximum_2: int: SC index of max (range 2)
			- 8 Minimum_2: int: SC index of min (range 2)"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Seg_Reliability'),
			ArgStruct.scalar_int('Statist_Expired'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct.scalar_int('Maximum_1'),
			ArgStruct.scalar_int('Minimum_1'),
			ArgStruct.scalar_int('Maximum_2'),
			ArgStruct.scalar_int('Minimum_2')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Seg_Reliability: int = None
			self.Statist_Expired: int = None
			self.Out_Of_Tolerance: int = None
			self.Maximum_1: int = None
			self.Minimum_1: int = None
			self.Maximum_2: int = None
			self.Minimum_2: int = None

	def fetch(self, segment=repcap.Segment.Default) -> FetchStruct:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:ESFLatness:CURRent:SCINdex \n
		Snippet: value: FetchStruct = driver.lteMeas.multiEval.listPy.segment.esFlatness.current.scIndex.fetch(segment = repcap.Segment.Default) \n
		Return subcarrier indices of the equalizer spectrum flatness measurement for segment <no> in list mode. At these SC
		indices, the current minimum and maximum power of the equalizer coefficients have been detected within range 1 and range
		2. \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:return: structure: for return value, see the help for FetchStruct structure arguments."""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:ESFLatness:CURRent:SCINdex?', self.__class__.FetchStruct())
