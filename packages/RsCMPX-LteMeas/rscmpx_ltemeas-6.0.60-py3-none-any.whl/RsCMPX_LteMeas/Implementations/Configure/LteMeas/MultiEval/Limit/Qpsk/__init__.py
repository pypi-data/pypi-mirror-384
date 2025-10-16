from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal import Conversions
from .......Internal.StructBase import StructBase
from .......Internal.ArgStruct import ArgStruct


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class QpskCls:
	"""Qpsk commands group definition. 9 total commands, 5 Subgroups, 3 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("qpsk", core, parent)

	@property
	def evMagnitude(self):
		"""evMagnitude commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_evMagnitude'):
			from .EvMagnitude import EvMagnitudeCls
			self._evMagnitude = EvMagnitudeCls(self._core, self._cmd_group)
		return self._evMagnitude

	@property
	def merror(self):
		"""merror commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_merror'):
			from .Merror import MerrorCls
			self._merror = MerrorCls(self._core, self._cmd_group)
		return self._merror

	@property
	def perror(self):
		"""perror commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_perror'):
			from .Perror import PerrorCls
			self._perror = PerrorCls(self._core, self._cmd_group)
		return self._perror

	@property
	def iqOffset(self):
		"""iqOffset commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_iqOffset'):
			from .IqOffset import IqOffsetCls
			self._iqOffset = IqOffsetCls(self._core, self._cmd_group)
		return self._iqOffset

	@property
	def ibe(self):
		"""ibe commands group. 1 Sub-classes, 1 commands."""
		if not hasattr(self, '_ibe'):
			from .Ibe import IbeCls
			self._ibe = IbeCls(self._core, self._cmd_group)
		return self._ibe

	def get_freq_error(self) -> float or bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QPSK:FERRor \n
		Snippet: value: float or bool = driver.configure.lteMeas.multiEval.limit.qpsk.get_freq_error() \n
		Defines an upper limit for the carrier frequency error (QPSK modulation) . \n
			:return: frequency_error: (float or boolean) No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QPSK:FERRor?')
		return Conversions.str_to_float_or_bool(response)

	def set_freq_error(self, frequency_error: float or bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QPSK:FERRor \n
		Snippet: driver.configure.lteMeas.multiEval.limit.qpsk.set_freq_error(frequency_error = 1.0) \n
		Defines an upper limit for the carrier frequency error (QPSK modulation) . \n
			:param frequency_error: (float or boolean) No help available
		"""
		param = Conversions.decimal_or_bool_value_to_str(frequency_error)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QPSK:FERRor {param}')

	# noinspection PyTypeChecker
	class SflatnessStruct(StructBase):  # From WriteStructDefinition CmdPropertyTemplate.xml
		"""Structure for setting input parameters. Fields: \n
			- Enable: bool: No parameter help available
			- Lower: float: No parameter help available
			- Upper: float: No parameter help available
			- Edge_Lower: float: No parameter help available
			- Edge_Upper: float: No parameter help available
			- Edge_Frequency: float: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_bool('Enable'),
			ArgStruct.scalar_float('Lower'),
			ArgStruct.scalar_float('Upper'),
			ArgStruct.scalar_float('Edge_Lower'),
			ArgStruct.scalar_float('Edge_Upper'),
			ArgStruct.scalar_float('Edge_Frequency')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Enable: bool=None
			self.Lower: float=None
			self.Upper: float=None
			self.Edge_Lower: float=None
			self.Edge_Upper: float=None
			self.Edge_Frequency: float=None

	def get_sflatness(self) -> SflatnessStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QPSK:SFLatness \n
		Snippet: value: SflatnessStruct = driver.configure.lteMeas.multiEval.limit.qpsk.get_sflatness() \n
		No command help available \n
			:return: structure: for return value, see the help for SflatnessStruct structure arguments.
		"""
		return self._core.io.query_struct('CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QPSK:SFLatness?', self.__class__.SflatnessStruct())

	def set_sflatness(self, value: SflatnessStruct) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QPSK:SFLatness \n
		Snippet with structure: \n
		structure = driver.configure.lteMeas.multiEval.limit.qpsk.SflatnessStruct() \n
		structure.Enable: bool = False \n
		structure.Lower: float = 1.0 \n
		structure.Upper: float = 1.0 \n
		structure.Edge_Lower: float = 1.0 \n
		structure.Edge_Upper: float = 1.0 \n
		structure.Edge_Frequency: float = 1.0 \n
		driver.configure.lteMeas.multiEval.limit.qpsk.set_sflatness(value = structure) \n
		No command help available \n
			:param value: see the help for SflatnessStruct structure arguments.
		"""
		self._core.io.write_struct('CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QPSK:SFLatness', value)

	# noinspection PyTypeChecker
	class EsFlatnessStruct(StructBase):  # From WriteStructDefinition CmdPropertyTemplate.xml
		"""Structure for setting input parameters. Fields: \n
			- Enable: bool: OFF: disables the limit check ON: enables the limit check
			- Range_1: float: Upper limit for max(range 1) - min(range 1)
			- Range_2: float: Upper limit for max(range 2) - min(range 2)
			- Max_1_Min_2: float: Upper limit for max(range 1) - min(range 2)
			- Max_2_Min_1: float: Upper limit for max(range 2) - min(range 1)
			- Edge_Frequency: float: Frequency band edge distance of border between range 1 and range 2"""
		__meta_args_list = [
			ArgStruct.scalar_bool('Enable'),
			ArgStruct.scalar_float('Range_1'),
			ArgStruct.scalar_float('Range_2'),
			ArgStruct.scalar_float('Max_1_Min_2'),
			ArgStruct.scalar_float('Max_2_Min_1'),
			ArgStruct.scalar_float('Edge_Frequency')]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Enable: bool=None
			self.Range_1: float=None
			self.Range_2: float=None
			self.Max_1_Min_2: float=None
			self.Max_2_Min_1: float=None
			self.Edge_Frequency: float=None

	def get_es_flatness(self) -> EsFlatnessStruct:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QPSK:ESFLatness \n
		Snippet: value: EsFlatnessStruct = driver.configure.lteMeas.multiEval.limit.qpsk.get_es_flatness() \n
		Defines limits for the equalizer spectrum flatness (QPSK modulation) . \n
			:return: structure: for return value, see the help for EsFlatnessStruct structure arguments.
		"""
		return self._core.io.query_struct('CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QPSK:ESFLatness?', self.__class__.EsFlatnessStruct())

	def set_es_flatness(self, value: EsFlatnessStruct) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QPSK:ESFLatness \n
		Snippet with structure: \n
		structure = driver.configure.lteMeas.multiEval.limit.qpsk.EsFlatnessStruct() \n
		structure.Enable: bool = False \n
		structure.Range_1: float = 1.0 \n
		structure.Range_2: float = 1.0 \n
		structure.Max_1_Min_2: float = 1.0 \n
		structure.Max_2_Min_1: float = 1.0 \n
		structure.Edge_Frequency: float = 1.0 \n
		driver.configure.lteMeas.multiEval.limit.qpsk.set_es_flatness(value = structure) \n
		Defines limits for the equalizer spectrum flatness (QPSK modulation) . \n
			:param value: see the help for EsFlatnessStruct structure arguments.
		"""
		self._core.io.write_struct('CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:QPSK:ESFLatness', value)

	def clone(self) -> 'QpskCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = QpskCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
