from ...........Internal.Core import Core
from ...........Internal.CommandsGroup import CommandsGroup
from ...........Internal import Conversions
from ...........Internal.RepeatedCapability import RepeatedCapability
from ........... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ChannelBw2ndCls:
	"""ChannelBw2nd commands group definition. 2 total commands, 1 Subgroups, 1 group commands
	Repeated Capability: SecondChannelBw, default value after init: SecondChannelBw.Bw50"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("channelBw2nd", core, parent)
		self._cmd_group.rep_cap = RepeatedCapability(self._cmd_group.group_name, 'repcap_secondChannelBw_get', 'repcap_secondChannelBw_set', repcap.SecondChannelBw.Bw50)

	def repcap_secondChannelBw_set(self, secondChannelBw: repcap.SecondChannelBw) -> None:
		"""Repeated Capability default value numeric suffix.
		This value is used, if you do not explicitely set it in the child set/get methods, or if you leave it to SecondChannelBw.Default.
		Default value after init: SecondChannelBw.Bw50"""
		self._cmd_group.set_repcap_enum_value(secondChannelBw)

	def repcap_secondChannelBw_get(self) -> repcap.SecondChannelBw:
		"""Returns the current default repeated capability for the child set/get methods"""
		# noinspection PyTypeChecker
		return self._cmd_group.get_repcap_enum_value()

	@property
	def channelBw3rd(self):
		"""channelBw3rd commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_channelBw3rd'):
			from .ChannelBw3rd import ChannelBw3rdCls
			self._channelBw3rd = ChannelBw3rdCls(self._core, self._cmd_group)
		return self._channelBw3rd

	def set(self, obw_limit: float or bool, firstChannelBw=repcap.FirstChannelBw.Default, secondChannelBw=repcap.SecondChannelBw.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:OBWLimit:CAGGregation:CBANdwidth<Band1>:CBANdwidth<Band2> \n
		Snippet: driver.configure.lteMeas.multiEval.limit.seMask.obwLimit.carrierAggregation.channelBw1st.channelBw2nd.set(obw_limit = 1.0, firstChannelBw = repcap.FirstChannelBw.Default, secondChannelBw = repcap.SecondChannelBw.Default) \n
		Defines an upper limit for the occupied bandwidth. The setting is defined separately for each channel bandwidth
		combination, for two aggregated carriers.
			Table Header:  \n
			- <Band1> / 50 / 100 / 150 / 100 / 150 / 200 / 200 / 150 / 200 / 200
			- <Band2> / 50 / 50 / 50 / 100 / 100 / 50 / 100 / 150 / 150 / 200 \n
			:param obw_limit: (float or boolean) No help available
			:param firstChannelBw: optional repeated capability selector. Default value: Bw50 (settable in the interface 'ChannelBw1st')
			:param secondChannelBw: optional repeated capability selector. Default value: Bw50 (settable in the interface 'ChannelBw2nd')
		"""
		param = Conversions.decimal_or_bool_value_to_str(obw_limit)
		firstChannelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(firstChannelBw, repcap.FirstChannelBw)
		secondChannelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(secondChannelBw, repcap.SecondChannelBw)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:OBWLimit:CAGGregation:CBANdwidth{firstChannelBw_cmd_val}:CBANdwidth{secondChannelBw_cmd_val} {param}')

	def get(self, firstChannelBw=repcap.FirstChannelBw.Default, secondChannelBw=repcap.SecondChannelBw.Default) -> float or bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:OBWLimit:CAGGregation:CBANdwidth<Band1>:CBANdwidth<Band2> \n
		Snippet: value: float or bool = driver.configure.lteMeas.multiEval.limit.seMask.obwLimit.carrierAggregation.channelBw1st.channelBw2nd.get(firstChannelBw = repcap.FirstChannelBw.Default, secondChannelBw = repcap.SecondChannelBw.Default) \n
		Defines an upper limit for the occupied bandwidth. The setting is defined separately for each channel bandwidth
		combination, for two aggregated carriers.
			Table Header:  \n
			- <Band1> / 50 / 100 / 150 / 100 / 150 / 200 / 200 / 150 / 200 / 200
			- <Band2> / 50 / 50 / 50 / 100 / 100 / 50 / 100 / 150 / 150 / 200 \n
			:param firstChannelBw: optional repeated capability selector. Default value: Bw50 (settable in the interface 'ChannelBw1st')
			:param secondChannelBw: optional repeated capability selector. Default value: Bw50 (settable in the interface 'ChannelBw2nd')
			:return: obw_limit: (float or boolean) No help available"""
		firstChannelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(firstChannelBw, repcap.FirstChannelBw)
		secondChannelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(secondChannelBw, repcap.SecondChannelBw)
		response = self._core.io.query_str(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:OBWLimit:CAGGregation:CBANdwidth{firstChannelBw_cmd_val}:CBANdwidth{secondChannelBw_cmd_val}?')
		return Conversions.str_to_float_or_bool(response)

	def clone(self) -> 'ChannelBw2ndCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = ChannelBw2ndCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
