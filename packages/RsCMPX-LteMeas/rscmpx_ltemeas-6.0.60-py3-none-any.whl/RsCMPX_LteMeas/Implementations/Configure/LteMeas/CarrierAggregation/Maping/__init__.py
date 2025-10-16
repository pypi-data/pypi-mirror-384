from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal.Utilities import trim_str_response
from ......Internal.StructBase import StructBase
from ......Internal.ArgStruct import ArgStruct
from ...... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class MapingCls:
	"""Maping commands group definition. 3 total commands, 1 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("maping", core, parent)

	@property
	def scc(self):
		"""scc commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_scc'):
			from .Scc import SccCls
			self._scc = SccCls(self._core, self._cmd_group)
		return self._scc

	def get_pcc(self) -> str:
		"""CONFigure:LTE:MEASurement<Instance>:CAGGregation:MAPing:PCC \n
		Snippet: value: str = driver.configure.lteMeas.carrierAggregation.maping.get_pcc() \n
		No command help available \n
			:return: cc: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:CAGGregation:MAPing:PCC?')
		return trim_str_response(response)

	# noinspection PyTypeChecker
	class ValueStruct(StructBase):  # From ReadStructDefinition CmdPropertyTemplate.xml
		"""Structure for reading output parameters. Fields: \n
			- Cc_1: enums.CarrAggrMaping: No parameter help available
			- Cc_2: enums.CarrAggrMaping: No parameter help available
			- Cc_3: enums.CarrAggrMaping: No parameter help available
			- Cc_4: enums.CarrAggrMaping: No parameter help available"""
		__meta_args_list = [
			ArgStruct.scalar_enum('Cc_1', enums.CarrAggrMaping),
			ArgStruct.scalar_enum('Cc_2', enums.CarrAggrMaping),
			ArgStruct.scalar_enum('Cc_3', enums.CarrAggrMaping),
			ArgStruct.scalar_enum('Cc_4', enums.CarrAggrMaping)]

		def __init__(self):
			StructBase.__init__(self, self)
			self.Cc_1: enums.CarrAggrMaping=None
			self.Cc_2: enums.CarrAggrMaping=None
			self.Cc_3: enums.CarrAggrMaping=None
			self.Cc_4: enums.CarrAggrMaping=None

	def get_value(self) -> ValueStruct:
		"""CONFigure:LTE:MEASurement<Instance>:CAGGregation:MAPing \n
		Snippet: value: ValueStruct = driver.configure.lteMeas.carrierAggregation.maping.get_value() \n
		No command help available \n
			:return: structure: for return value, see the help for ValueStruct structure arguments.
		"""
		return self._core.io.query_struct('CONFigure:LTE:MEASurement<Instance>:CAGGregation:MAPing?', self.__class__.ValueStruct())

	def clone(self) -> 'MapingCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = MapingCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
