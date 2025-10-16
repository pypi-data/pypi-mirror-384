from typing import List

from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class IemissionsCls:
	"""Iemissions commands group definition. 4 total commands, 1 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("iemissions", core, parent)

	@property
	def ulca(self):
		"""ulca commands group. 1 Sub-classes, 1 commands."""
		if not hasattr(self, '_ulca'):
			from .Ulca import UlcaCls
			self._ulca = UlcaCls(self._core, self._cmd_group)
		return self._ulca

	def get_scc(self) -> List[float]:
		"""SENSe:LTE:MEASurement<Instance>:MEValuation:LIMit:IEMissions:SCC \n
		Snippet: value: List[float] = driver.sense.lteMeas.multiEval.limit.iemissions.get_scc() \n
		No command help available \n
			:return: power: No help available
		"""
		response = self._core.io.query_bin_or_ascii_float_list('SENSe:LTE:MEASurement<Instance>:MEValuation:LIMit:IEMissions:SCC?')
		return response

	def get_pcc(self) -> List[float]:
		"""SENSe:LTE:MEASurement<Instance>:MEValuation:LIMit:IEMissions[:PCC] \n
		Snippet: value: List[float] = driver.sense.lteMeas.multiEval.limit.iemissions.get_pcc() \n
		No command help available \n
			:return: power: No help available
		"""
		response = self._core.io.query_bin_or_ascii_float_list('SENSe:LTE:MEASurement<Instance>:MEValuation:LIMit:IEMissions:PCC?')
		return response

	def clone(self) -> 'IemissionsCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = IemissionsCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
