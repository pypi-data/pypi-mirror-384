from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.RepeatedCapability import RepeatedCapability
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class UtraCls:
	"""Utra commands group definition. 8 total commands, 2 Subgroups, 0 group commands
	Repeated Capability: UtraAdjChannel, default value after init: UtraAdjChannel.Ch1"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("utra", core, parent)
		self._cmd_group.rep_cap = RepeatedCapability(self._cmd_group.group_name, 'repcap_utraAdjChannel_get', 'repcap_utraAdjChannel_set', repcap.UtraAdjChannel.Ch1)

	def repcap_utraAdjChannel_set(self, utraAdjChannel: repcap.UtraAdjChannel) -> None:
		"""Repeated Capability default value numeric suffix.
		This value is used, if you do not explicitely set it in the child set/get methods, or if you leave it to UtraAdjChannel.Default.
		Default value after init: UtraAdjChannel.Ch1"""
		self._cmd_group.set_repcap_enum_value(utraAdjChannel)

	def repcap_utraAdjChannel_get(self) -> repcap.UtraAdjChannel:
		"""Returns the current default repeated capability for the child set/get methods"""
		# noinspection PyTypeChecker
		return self._cmd_group.get_repcap_enum_value()

	@property
	def negativ(self):
		"""negativ commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_negativ'):
			from .Negativ import NegativCls
			self._negativ = NegativCls(self._core, self._cmd_group)
		return self._negativ

	@property
	def positiv(self):
		"""positiv commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_positiv'):
			from .Positiv import PositivCls
			self._positiv = PositivCls(self._core, self._cmd_group)
		return self._positiv

	def clone(self) -> 'UtraCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = UtraCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
