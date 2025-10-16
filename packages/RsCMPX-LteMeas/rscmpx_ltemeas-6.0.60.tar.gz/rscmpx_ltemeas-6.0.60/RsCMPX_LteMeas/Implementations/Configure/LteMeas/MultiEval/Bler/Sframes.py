from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal.Types import DataType
from ......Internal.StructBase import StructBase
from ......Internal.ArgStruct import ArgStruct
from ......Internal.ArgSingleList import ArgSingleList
from ......Internal.ArgSingle import ArgSingle


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SframesCls:
	"""Sframes commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("sframes", core, parent)

	def set(self, sub_frames: int, sched_subfr_per_fr: int=None) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:BLER:SFRames \n
		Snippet: driver.configure.lteMeas.multiEval.bler.sframes.set(sub_frames = 1, sched_subfr_per_fr = 1) \n
		No command help available \n
			:param sub_frames: No help available
			:param sched_subfr_per_fr: No help available
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('sub_frames', sub_frames, DataType.Integer), ArgSingle('sched_subfr_per_fr', sched_subfr_per_fr, DataType.Integer, None, is_optional=True))
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:BLER:SFRames {param}'.rstrip())

	# noinspection PyTypeChecker
	class SframesStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Sub_Frames: int: No parameter help available
			- 2 Sched_Subfr_Per_Fr: int: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_int('Sub_Frames'),
			ArgStruct.scalar_int('Sched_Subfr_Per_Fr')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Sub_Frames: int = None
			self.Sched_Subfr_Per_Fr: int = None

	def get(self) -> SframesStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:BLER:SFRames \n
		Snippet: value: SframesStruct = driver.configure.lteMeas.multiEval.bler.sframes.get() \n
		No command help available \n
			:return: structure: for return value, see the help for SframesStruct structure arguments."""
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:BLER:SFRames?', self.__class__.SframesStruct())
