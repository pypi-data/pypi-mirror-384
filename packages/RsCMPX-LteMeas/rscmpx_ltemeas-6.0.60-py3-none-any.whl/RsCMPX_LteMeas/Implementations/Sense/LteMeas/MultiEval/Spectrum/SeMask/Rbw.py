from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class RbwCls:
	"""Rbw commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("rbw", core, parent)

	# noinspection PyTypeChecker
	class UsedStruct(StructBase):  # From ReadStructDefinition CmdPropertyTemplate.xml
		"""Structure for reading output parameters. Fields: \n
			- Trace_1: int: RBW for trace 1 (smallest RBW)
			- Trace_2: int: RBW for trace 2 (intermediate RBW)
			- Trace_3: int: RBW for trace 3 (largest RBW)"""
		__meta_args_list = [
			ArgStruct.scalar_int('Trace_1'),
			ArgStruct.scalar_int('Trace_2'),
			ArgStruct.scalar_int('Trace_3')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Trace_1: int=None
			self.Trace_2: int=None
			self.Trace_3: int=None

	def get_used(self) -> UsedStruct:
		"""SENSe:LTE:MEASurement<Instance>:MEValuation:SPECtrum:SEMask:RBW:USED \n
		Snippet: value: UsedStruct = driver.sense.lteMeas.multiEval.spectrum.seMask.rbw.get_used() \n
		Queries the resolution bandwidths (RBW) allowed for spectrum emission measurements. The RBWs depend on the channel
		bandwidth and on the 'network signaled value'. \n
			:return: structure: for return value, see the help for UsedStruct structure arguments.
		"""
		return self._core.io.query_struct('SENSe:LTE:MEASurement<Instance>:MEValuation:SPECtrum:SEMask:RBW:USED?', self.__class__.UsedStruct())
