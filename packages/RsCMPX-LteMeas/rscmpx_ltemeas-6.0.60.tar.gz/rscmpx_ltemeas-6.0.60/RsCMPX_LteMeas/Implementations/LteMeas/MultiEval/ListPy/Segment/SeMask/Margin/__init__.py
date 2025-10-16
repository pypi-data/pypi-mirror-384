from typing import List

from ........Internal.Core import Core
from ........Internal.CommandsGroup import CommandsGroup
from ........Internal.Types import DataType
from ........Internal.StructBase import StructBase
from ........Internal.ArgStruct import ArgStruct
from ........ import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class MarginCls:
	"""Margin commands group definition. 8 total commands, 4 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("margin", core, parent)

	@property
	def all(self):
		"""all commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_all'):
			from .All import AllCls
			self._all = AllCls(self._core, self._cmd_group)
		return self._all

	@property
	def current(self):
		"""current commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_current'):
			from .Current import CurrentCls
			self._current = CurrentCls(self._core, self._cmd_group)
		return self._current

	@property
	def average(self):
		"""average commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_average'):
			from .Average import AverageCls
			self._average = AverageCls(self._core, self._cmd_group)
		return self._average

	@property
	def minimum(self):
		"""minimum commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_minimum'):
			from .Minimum import MinimumCls
			self._minimum = MinimumCls(self._core, self._cmd_group)
		return self._minimum

	# noinspection PyTypeChecker
	class FetchStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: No parameter help available
			- 2 Seg_Reliability: int: No parameter help available
			- 3 Statist_Expired: int: No parameter help available
			- 4 Out_Of_Tolerance: int: No parameter help available
			- 5 Margin_Curr_Neg: List[float]: No parameter help available
			- 6 Margin_Curr_Pos: List[float]: No parameter help available
			- 7 Margin_Avg_Neg: List[float]: No parameter help available
			- 8 Margin_Avg_Pos: List[float]: No parameter help available
			- 9 Margin_Min_Neg: List[float]: No parameter help available
			- 10 Margin_Min_Pos: List[float]: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Seg_Reliability'),
			ArgStruct.scalar_int('Statist_Expired'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct('Margin_Curr_Neg', DataType.FloatList, None, False, False, 10),
			ArgStruct('Margin_Curr_Pos', DataType.FloatList, None, False, False, 10),
			ArgStruct('Margin_Avg_Neg', DataType.FloatList, None, False, False, 10),
			ArgStruct('Margin_Avg_Pos', DataType.FloatList, None, False, False, 10),
			ArgStruct('Margin_Min_Neg', DataType.FloatList, None, False, False, 10),
			ArgStruct('Margin_Min_Pos', DataType.FloatList, None, False, False, 10)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Seg_Reliability: int = None
			self.Statist_Expired: int = None
			self.Out_Of_Tolerance: int = None
			self.Margin_Curr_Neg: List[float] = None
			self.Margin_Curr_Pos: List[float] = None
			self.Margin_Avg_Neg: List[float] = None
			self.Margin_Avg_Pos: List[float] = None
			self.Margin_Min_Neg: List[float] = None
			self.Margin_Min_Pos: List[float] = None

	def fetch(self, segment=repcap.Segment.Default) -> FetchStruct:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:SEMask:MARGin \n
		Snippet: value: FetchStruct = driver.lteMeas.multiEval.listPy.segment.seMask.margin.fetch(segment = repcap.Segment.Default) \n
		No command help available \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:return: structure: for return value, see the help for FetchStruct structure arguments."""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:SEMask:MARGin?', self.__class__.FetchStruct())

	def clone(self) -> 'MarginCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = MarginCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
