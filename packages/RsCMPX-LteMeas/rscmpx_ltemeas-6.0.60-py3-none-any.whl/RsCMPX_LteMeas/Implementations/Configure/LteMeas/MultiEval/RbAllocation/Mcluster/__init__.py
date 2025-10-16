from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class MclusterCls:
	"""Mcluster commands group definition. 3 total commands, 2 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("mcluster", core, parent)

	@property
	def nrb(self):
		"""nrb commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_nrb'):
			from .Nrb import NrbCls
			self._nrb = NrbCls(self._core, self._cmd_group)
		return self._nrb

	@property
	def orb(self):
		"""orb commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_orb'):
			from .Orb import OrbCls
			self._orb = OrbCls(self._core, self._cmd_group)
		return self._orb

	def get_value(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:MCLuster \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.rbAllocation.mcluster.get_value() \n
		Specifies whether the UL signal uses multi-cluster allocation or not. \n
			:return: enable: OFF: contiguous allocation, resource allocation type 0 ON: multi-cluster allocation, resource allocation type 1
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:MCLuster?')
		return Conversions.str_to_bool(response)

	def set_value(self, enable: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:MCLuster \n
		Snippet: driver.configure.lteMeas.multiEval.rbAllocation.mcluster.set_value(enable = False) \n
		Specifies whether the UL signal uses multi-cluster allocation or not. \n
			:param enable: OFF: contiguous allocation, resource allocation type 0 ON: multi-cluster allocation, resource allocation type 1
		"""
		param = Conversions.bool_to_str(enable)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:MCLuster {param}')

	def clone(self) -> 'MclusterCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = MclusterCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
