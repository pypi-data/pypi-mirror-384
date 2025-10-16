from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal.StructBase import StructBase
from ......Internal.ArgStruct import ArgStruct


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
			- 2 Out_Of_Tolerance: int: Out of tolerance result, i.e. the percentage of measurement intervals of the statistic count for modulation measurements exceeding the specified modulation limits.
			- 3 Maximum_1: int: SC index of Max (Range 1)
			- 4 Minimum_1: int: SC index of Min (Range 1)
			- 5 Maximum_2: int: SC index of Max (Range 2)
			- 6 Minimum_2: int: SC index of Min (Range 2)"""
		__meta_args_list = [
			ArgStruct.scalar_int('Reliability', 'Reliability'),
			ArgStruct.scalar_int('Out_Of_Tolerance'),
			ArgStruct.scalar_int('Maximum_1'),
			ArgStruct.scalar_int('Minimum_1'),
			ArgStruct.scalar_int('Maximum_2'),
			ArgStruct.scalar_int('Minimum_2')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Reliability: int = None
			self.Out_Of_Tolerance: int = None
			self.Maximum_1: int = None
			self.Minimum_1: int = None
			self.Maximum_2: int = None
			self.Minimum_2: int = None

	def fetch(self) -> FetchStruct:
		"""FETCh:LTE:MEASurement<Instance>:MEValuation:ESFLatness:CURRent:SCINdex \n
		Snippet: value: FetchStruct = driver.lteMeas.multiEval.esFlatness.current.scIndex.fetch() \n
		Returns subcarrier indices of the equalizer spectrum flatness measurement. At these SC indices, the current minimum and
		maximum power of the equalizer coefficients have been detected within range 1 and range 2. \n
			:return: structure: for return value, see the help for FetchStruct structure arguments."""
		return self._core.io.query_struct(f'FETCh:LTE:MEASurement<Instance>:MEValuation:ESFLatness:CURRent:SCINdex?', self.__class__.FetchStruct())
