from typing import List

from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.Types import DataType
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct
from .......Internal.ArgSingleList import ArgSingleList
from .......Internal.ArgSingle import ArgSingle


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class EwLengthCls:
	"""EwLength commands group definition. 2 total commands, 1 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("ewLength", core, parent)

	@property
	def channelBw(self):
		"""channelBw commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_channelBw'):
			from .ChannelBw import ChannelBwCls
			self._channelBw = ChannelBwCls(self._core, self._cmd_group)
		return self._channelBw

	def set(self, length_cp_normal: List[int], length_cp_extended: List[int]) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:MODulation:EWLength \n
		Snippet: driver.configure.lteMeas.multiEval.modulation.ewLength.set(length_cp_normal = [1, 2, 3], length_cp_extended = [1, 2, 3]) \n
		Specifies the EVM window length in samples for all channel bandwidths, depending on the cyclic prefix (CP) type. \n
			:param length_cp_normal: No help available
			:param length_cp_extended: No help available
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('length_cp_normal', length_cp_normal, DataType.IntegerList, None, False, False, 6), ArgSingle('length_cp_extended', length_cp_extended, DataType.IntegerList, None, False, False, 6))
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:MODulation:EWLength {param}'.rstrip())

	# noinspection PyTypeChecker
	class EwLengthStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Length_Cp_Normal: List[int]: No parameter help available
			- 2 Length_Cp_Extended: List[int]: No parameter help available"""
		__meta_args_list = [
			ArgStruct('Length_Cp_Normal', DataType.IntegerList, None, False, False, 6),
			ArgStruct('Length_Cp_Extended', DataType.IntegerList, None, False, False, 6)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Length_Cp_Normal: List[int] = None
			self.Length_Cp_Extended: List[int] = None

	def get(self) -> EwLengthStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:MODulation:EWLength \n
		Snippet: value: EwLengthStruct = driver.configure.lteMeas.multiEval.modulation.ewLength.get() \n
		Specifies the EVM window length in samples for all channel bandwidths, depending on the cyclic prefix (CP) type. \n
			:return: structure: for return value, see the help for EwLengthStruct structure arguments."""
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:MODulation:EWLength?', self.__class__.EwLengthStruct())

	def clone(self) -> 'EwLengthCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = EwLengthCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
