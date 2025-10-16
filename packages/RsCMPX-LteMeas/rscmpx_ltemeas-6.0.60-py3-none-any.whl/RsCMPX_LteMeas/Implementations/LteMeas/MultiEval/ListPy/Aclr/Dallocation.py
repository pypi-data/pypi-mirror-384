from typing import List

from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal.Types import DataType
from ......Internal.StructBase import StructBase
from ......Internal.ArgStruct import ArgStruct


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class DallocationCls:
	"""Dallocation commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("dallocation", core, parent)

	# noinspection PyTypeChecker
	class FetchStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Reliability: int: 'Reliability indicator'
			- 2 Nr_Res_Blocks: List[int]: Number of allocated resource blocks
			- 3 Offset_Res_Blocks: List[int]: Offset of the first allocated resource block from the edge of the allocated UL transmission bandwidth"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct('Nr_Res_Blocks', DataType.IntegerList, None, False, True, 1),
			ArgStruct('Offset_Res_Blocks', DataType.IntegerList, None, False, True, 1)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Nr_Res_Blocks: List[int] = None
			self.Offset_Res_Blocks: List[int] = None

	def fetch(self) -> FetchStruct:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:ACLR:DALLocation \n
		Snippet: value: FetchStruct = driver.lteMeas.multiEval.listPy.aclr.dallocation.fetch() \n
		Return the detected allocation for all measured list mode segments. The result is determined from the last measured slot
		of the statistical length of a segment. The individual measurements provide the same result when measuring the same slot.
		However different statistical lengths can be defined for the measurements so that the measured slots and returned results
		can differ. The results are returned as pairs per segment: <Reliability>, {<NrResBlocks>, <OffsetResBlocks>}Seg 1,
		{<NrResBlocks>, <OffsetResBlocks>}Seg 2, ... \n
			:return: structure: for return value, see the help for FetchStruct structure arguments."""
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:LIST:ACLR:DALLocation?', self.__class__.FetchStruct())
