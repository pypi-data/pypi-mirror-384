from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class CarrierAggregationCls:
	"""CarrierAggregation commands group definition. 12 total commands, 6 Subgroups, 0 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("carrierAggregation", core, parent)

	@property
	def mode(self):
		"""mode commands group. 0 Sub-classes, 2 commands."""
		if not hasattr(self, '_mode'):
			from .Mode import ModeCls
			self._mode = ModeCls(self._core, self._cmd_group)
		return self._mode

	@property
	def mcarrier(self):
		"""mcarrier commands group. 0 Sub-classes, 2 commands."""
		if not hasattr(self, '_mcarrier'):
			from .Mcarrier import McarrierCls
			self._mcarrier = McarrierCls(self._core, self._cmd_group)
		return self._mcarrier

	@property
	def frequency(self):
		"""frequency commands group. 1 Sub-classes, 0 commands."""
		if not hasattr(self, '_frequency'):
			from .Frequency import FrequencyCls
			self._frequency = FrequencyCls(self._core, self._cmd_group)
		return self._frequency

	@property
	def channelBw(self):
		"""channelBw commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_channelBw'):
			from .ChannelBw import ChannelBwCls
			self._channelBw = ChannelBwCls(self._core, self._cmd_group)
		return self._channelBw

	@property
	def scc(self):
		"""scc commands group. 1 Sub-classes, 0 commands."""
		if not hasattr(self, '_scc'):
			from .Scc import SccCls
			self._scc = SccCls(self._core, self._cmd_group)
		return self._scc

	@property
	def maping(self):
		"""maping commands group. 1 Sub-classes, 2 commands."""
		if not hasattr(self, '_maping'):
			from .Maping import MapingCls
			self._maping = MapingCls(self._core, self._cmd_group)
		return self._maping

	def clone(self) -> 'CarrierAggregationCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = CarrierAggregationCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
