from ........Internal.Core import Core
from ........Internal.CommandsGroup import CommandsGroup
from ........Internal.StructBase import StructBase
from ........Internal.ArgStruct import ArgStruct
from ........ import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class CurrentCls:
	"""Current commands group definition. 3 total commands, 1 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("current", core, parent)

	@property
	def scIndex(self):
		"""scIndex commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_scIndex'):
			from .ScIndex import ScIndexCls
			self._scIndex = ScIndexCls(self._core, self._cmd_group)
		return self._scIndex

	# noinspection PyTypeChecker
	class FetchStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Seg_Reliability: int: Reliability indicator for the segment
			- 3 Statist_Expired: int: Reached statistical length in slots
			- 4 Out_Of_Tolerance: int: Percentage of measured subframes with failed limit check
			- 5 Ripple_1: float: Max (range 1) - min (range 1)
			- 6 Ripple_2: float: Max (range 2) - min (range 2)
			- 7 Max_R_1_Min_R_2: float: Max (range 1) - min (range 2)
			- 8 Max_R_2_Min_R_1: float: Max (range 2) - min (range 1)
			- 9 Min_R_1: float: Min (range 1)
			- 10 Max_R_1: float: Max (range 1)
			- 11 Min_R_2: float: Min (range 2)
			- 12 Max_R_2: float: Max (range 2)"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Seg_Reliability'),
			ArgStruct.scalar_int('Statist_Expired'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct.scalar_float('Ripple_1'),
			ArgStruct.scalar_float('Ripple_2'),
			ArgStruct.scalar_float('Max_R_1_Min_R_2'),
			ArgStruct.scalar_float('Max_R_2_Min_R_1'),
			ArgStruct.scalar_float('Min_R_1'),
			ArgStruct.scalar_float('Max_R_1'),
			ArgStruct.scalar_float('Min_R_2'),
			ArgStruct.scalar_float('Max_R_2')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Seg_Reliability: int = None
			self.Statist_Expired: int = None
			self.Out_Of_Tolerance: int = None
			self.Ripple_1: float = None
			self.Ripple_2: float = None
			self.Max_R_1_Min_R_2: float = None
			self.Max_R_2_Min_R_1: float = None
			self.Min_R_1: float = None
			self.Max_R_1: float = None
			self.Min_R_2: float = None
			self.Max_R_2: float = None

	def fetch(self, segment=repcap.Segment.Default) -> FetchStruct:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:ESFLatness:CURRent \n
		Snippet: value: FetchStruct = driver.lteMeas.multiEval.listPy.segment.esFlatness.current.fetch(segment = repcap.Segment.Default) \n
		Return equalizer spectrum flatness single value results for segment <no> in list mode. \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:return: structure: for return value, see the help for FetchStruct structure arguments."""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:ESFLatness:CURRent?', self.__class__.FetchStruct())

	# noinspection PyTypeChecker
	class CalculateStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Seg_Reliability: int: Reliability indicator for the segment
			- 3 Statist_Expired: int: Reached statistical length in slots
			- 4 Out_Of_Tolerance: int: Percentage of measured subframes with failed limit check
			- 5 Ripple_1: float or bool: Limit check result for max (range 1) - min (range 1) .
			- 6 Ripple_2: float or bool: Limit check result for max (range 2) - min (range 2) .
			- 7 Max_R_1_Min_R_2: float or bool: Limit check result for max (range 1) - min (range 2) .
			- 8 Max_R_2_Min_R_1: float or bool: Limit check result for max (range 2) - min (range 1) ."""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Seg_Reliability'),
			ArgStruct.scalar_int('Statist_Expired'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct.scalar_float_ext('Ripple_1'),
			ArgStruct.scalar_float_ext('Ripple_2'),
			ArgStruct.scalar_float_ext('Max_R_1_Min_R_2'),
			ArgStruct.scalar_float_ext('Max_R_2_Min_R_1')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Seg_Reliability: int = None
			self.Statist_Expired: int = None
			self.Out_Of_Tolerance: int = None
			self.Ripple_1: float or bool = None
			self.Ripple_2: float or bool = None
			self.Max_R_1_Min_R_2: float or bool = None
			self.Max_R_2_Min_R_1: float or bool = None

	def calculate(self, segment=repcap.Segment.Default) -> CalculateStruct:
		"""CALCulate:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:ESFLatness:CURRent \n
		Snippet: value: CalculateStruct = driver.lteMeas.multiEval.listPy.segment.esFlatness.current.calculate(segment = repcap.Segment.Default) \n
		Return equalizer spectrum flatness single value results for segment <no> in list mode. \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:return: structure: for return value, see the help for CalculateStruct structure arguments."""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		return self._core.io.query_struct(f'CALCulate:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:ESFLatness:CURRent?', self.__class__.CalculateStruct())

	def clone(self) -> 'CurrentCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = CurrentCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
