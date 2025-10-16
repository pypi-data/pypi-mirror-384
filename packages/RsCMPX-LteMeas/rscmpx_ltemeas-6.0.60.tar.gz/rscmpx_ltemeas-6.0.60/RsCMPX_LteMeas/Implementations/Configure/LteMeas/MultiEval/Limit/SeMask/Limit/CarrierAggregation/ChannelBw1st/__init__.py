from ..........Internal.Core import Core
from ..........Internal.CommandsGroup import CommandsGroup
from ..........Internal.RepeatedCapability import RepeatedCapability
from .......... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ChannelBw1stCls:
	"""ChannelBw1st commands group definition. 2 total commands, 1 Subgroups, 0 group commands
	Repeated Capability: FirstChannelBw, default value after init: FirstChannelBw.Bw50"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("channelBw1st", core, parent)
		self._cmd_group.rep_cap = RepeatedCapability(self._cmd_group.group_name, 'repcap_firstChannelBw_get', 'repcap_firstChannelBw_set', repcap.FirstChannelBw.Bw50)

	def repcap_firstChannelBw_set(self, firstChannelBw: repcap.FirstChannelBw) -> None:
		"""Repeated Capability default value numeric suffix.
		This value is used, if you do not explicitely set it in the child set/get methods, or if you leave it to FirstChannelBw.Default.
		Default value after init: FirstChannelBw.Bw50"""
		self._cmd_group.set_repcap_enum_value(firstChannelBw)

	def repcap_firstChannelBw_get(self) -> repcap.FirstChannelBw:
		"""Returns the current default repeated capability for the child set/get methods"""
		# noinspection PyTypeChecker
		return self._cmd_group.get_repcap_enum_value()

	@property
	def channelBw2nd(self):
		"""channelBw2nd commands group. 1 Sub-classes, 1 commands."""
		if not hasattr(self, '_channelBw2nd'):
			from .ChannelBw2nd import ChannelBw2ndCls
			self._channelBw2nd = ChannelBw2ndCls(self._core, self._cmd_group)
		return self._channelBw2nd

	def clone(self) -> 'ChannelBw1stCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = ChannelBw1stCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
