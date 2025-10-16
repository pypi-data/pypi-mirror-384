from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal import Conversions
from .......Internal.RepeatedCapability import RepeatedCapability
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class NrbCls:
	"""Nrb commands group definition. 1 total commands, 0 Subgroups, 1 group commands
	Repeated Capability: RBcount, default value after init: RBcount.Nr1"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("nrb", core, parent)
		self._cmd_group.rep_cap = RepeatedCapability(self._cmd_group.group_name, 'repcap_rBcount_get', 'repcap_rBcount_set', repcap.RBcount.Nr1)

	def repcap_rBcount_set(self, rBcount: repcap.RBcount) -> None:
		"""Repeated Capability default value numeric suffix.
		This value is used, if you do not explicitely set it in the child set/get methods, or if you leave it to RBcount.Default.
		Default value after init: RBcount.Nr1"""
		self._cmd_group.set_repcap_enum_value(rBcount)

	def repcap_rBcount_get(self) -> repcap.RBcount:
		"""Returns the current default repeated capability for the child set/get methods"""
		# noinspection PyTypeChecker
		return self._cmd_group.get_repcap_enum_value()

	def set(self, no_rb: int, rBcount=repcap.RBcount.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:MCLuster:NRB<Number> \n
		Snippet: driver.configure.lteMeas.multiEval.rbAllocation.mcluster.nrb.set(no_rb = 1, rBcount = repcap.RBcount.Default) \n
		Specifies the number of allocated RBs in the measured slot, for multi-cluster allocation. \n
			:param no_rb: For the allowed input ranges, see 'Uplink resource block allocation'.
			:param rBcount: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Nrb')
		"""
		param = Conversions.decimal_value_to_str(no_rb)
		rBcount_cmd_val = self._cmd_group.get_repcap_cmd_value(rBcount, repcap.RBcount)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:MCLuster:NRB{rBcount_cmd_val} {param}')

	def get(self, rBcount=repcap.RBcount.Default) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:MCLuster:NRB<Number> \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.rbAllocation.mcluster.nrb.get(rBcount = repcap.RBcount.Default) \n
		Specifies the number of allocated RBs in the measured slot, for multi-cluster allocation. \n
			:param rBcount: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Nrb')
			:return: no_rb: For the allowed input ranges, see 'Uplink resource block allocation'."""
		rBcount_cmd_val = self._cmd_group.get_repcap_cmd_value(rBcount, repcap.RBcount)
		response = self._core.io.query_str(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:MCLuster:NRB{rBcount_cmd_val}?')
		return Conversions.str_to_int(response)

	def clone(self) -> 'NrbCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = NrbCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
