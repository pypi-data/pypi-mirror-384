from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal.Types import DataType
from ......Internal.StructBase import StructBase
from ......Internal.ArgStruct import ArgStruct
from ......Internal.ArgSingleList import ArgSingleList
from ......Internal.ArgSingle import ArgSingle


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class LrangeCls:
	"""Lrange commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("lrange", core, parent)

	def set(self, start_index: int, nr_segments: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:LRANge \n
		Snippet: driver.configure.lteMeas.multiEval.listPy.lrange.set(start_index = 1, nr_segments = 1) \n
		Selects a range of measured segments. Configure the segments via method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.ListPy.
		Segment.Setup.set. \n
			:param start_index: First measured segment in the range of configured segments
			:param nr_segments: Number of measured segments
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('start_index', start_index, DataType.Integer), ArgSingle('nr_segments', nr_segments, DataType.Integer))
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:LRANge {param}'.rstrip())

	# noinspection PyTypeChecker
	class LrangeStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Start_Index: int: First measured segment in the range of configured segments
			- 2 Nr_Segments: int: Number of measured segments"""
		__meta_args_list = [
			ArgStruct.scalar_int('Start_Index'),
			ArgStruct.scalar_int('Nr_Segments')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Start_Index: int = None
			self.Nr_Segments: int = None

	def get(self) -> LrangeStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:LRANge \n
		Snippet: value: LrangeStruct = driver.configure.lteMeas.multiEval.listPy.lrange.get() \n
		Selects a range of measured segments. Configure the segments via method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.ListPy.
		Segment.Setup.set. \n
			:return: structure: for return value, see the help for LrangeStruct structure arguments."""
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:LRANge?', self.__class__.LrangeStruct())
