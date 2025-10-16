from .........Internal.Core import Core
from .........Internal.CommandsGroup import CommandsGroup
from .........Internal.Types import DataType
from .........Internal.StructBase import StructBase
from .........Internal.ArgStruct import ArgStruct
from .........Internal.ArgSingleList import ArgSingleList
from .........Internal.ArgSingle import ArgSingle
from ......... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class OcombinationCls:
	"""Ocombination commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("ocombination", core, parent)

	def set(self, relative_level: float or bool, absolute_level: float or bool, utraAdjChannel=repcap.UtraAdjChannel.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:ACLR:UTRA<nr>:CAGGregation:OCOMbination \n
		Snippet: driver.configure.lteMeas.multiEval.limit.aclr.utra.carrierAggregation.ocombination.set(relative_level = 1.0, absolute_level = 1.0, utraAdjChannel = repcap.UtraAdjChannel.Default) \n
		Defines relative and absolute limits for the ACLR measured in the first or second adjacent UTRA channel, depending on
		<no>. The settings apply to all 'other' channel bandwidth combinations, not covered by other commands in this section. \n
			:param relative_level: (float or boolean) No help available
			:param absolute_level: (float or boolean) No help available
			:param utraAdjChannel: optional repeated capability selector. Default value: Ch1 (settable in the interface 'Utra')
		"""
		param = ArgSingleList().compose_cmd_string(ArgSingle('relative_level', relative_level, DataType.FloatExt), ArgSingle('absolute_level', absolute_level, DataType.FloatExt))
		utraAdjChannel_cmd_val = self._cmd_group.get_repcap_cmd_value(utraAdjChannel, repcap.UtraAdjChannel)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:ACLR:UTRA{utraAdjChannel_cmd_val}:CAGGregation:OCOMbination {param}'.rstrip())

	# noinspection PyTypeChecker
	class OcombinationStruct(StructBase):
		"""Response structure. Fields: \n
			- 1 Relative_Level: float or bool: No parameter help available
			- 2 Absolute_Level: float or bool: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_float_ext('Relative_Level'),
			ArgStruct.scalar_float_ext('Absolute_Level')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Relative_Level: float or bool = None
			self.Absolute_Level: float or bool = None

	def get(self, utraAdjChannel=repcap.UtraAdjChannel.Default) -> OcombinationStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:ACLR:UTRA<nr>:CAGGregation:OCOMbination \n
		Snippet: value: OcombinationStruct = driver.configure.lteMeas.multiEval.limit.aclr.utra.carrierAggregation.ocombination.get(utraAdjChannel = repcap.UtraAdjChannel.Default) \n
		Defines relative and absolute limits for the ACLR measured in the first or second adjacent UTRA channel, depending on
		<no>. The settings apply to all 'other' channel bandwidth combinations, not covered by other commands in this section. \n
			:param utraAdjChannel: optional repeated capability selector. Default value: Ch1 (settable in the interface 'Utra')
			:return: structure: for return value, see the help for OcombinationStruct structure arguments."""
		utraAdjChannel_cmd_val = self._cmd_group.get_repcap_cmd_value(utraAdjChannel, repcap.UtraAdjChannel)
		return self._core.io.query_struct(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:ACLR:UTRA{utraAdjChannel_cmd_val}:CAGGregation:OCOMbination?', self.__class__.OcombinationStruct())
