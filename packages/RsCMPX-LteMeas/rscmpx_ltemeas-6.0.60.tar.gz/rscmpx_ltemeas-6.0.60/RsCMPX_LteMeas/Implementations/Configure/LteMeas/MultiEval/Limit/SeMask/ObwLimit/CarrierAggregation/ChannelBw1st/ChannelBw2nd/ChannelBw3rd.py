from ...........Internal.Core import Core
from ...........Internal.CommandsGroup import CommandsGroup
from ...........Internal import Conversions
from ...........Internal.RepeatedCapability import RepeatedCapability
from ........... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ChannelBw3rdCls:
	"""ChannelBw3rd commands group definition. 1 total commands, 0 Subgroups, 1 group commands
	Repeated Capability: ThirdChannelBw, default value after init: ThirdChannelBw.Bw100"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("channelBw3rd", core, parent)
		self._cmd_group.rep_cap = RepeatedCapability(self._cmd_group.group_name, 'repcap_thirdChannelBw_get', 'repcap_thirdChannelBw_set', repcap.ThirdChannelBw.Bw100)

	def repcap_thirdChannelBw_set(self, thirdChannelBw: repcap.ThirdChannelBw) -> None:
		"""Repeated Capability default value numeric suffix.
		This value is used, if you do not explicitely set it in the child set/get methods, or if you leave it to ThirdChannelBw.Default.
		Default value after init: ThirdChannelBw.Bw100"""
		self._cmd_group.set_repcap_enum_value(thirdChannelBw)

	def repcap_thirdChannelBw_get(self) -> repcap.ThirdChannelBw:
		"""Returns the current default repeated capability for the child set/get methods"""
		# noinspection PyTypeChecker
		return self._cmd_group.get_repcap_enum_value()

	def set(self, obw_limit: float or bool, firstChannelBw=repcap.FirstChannelBw.Default, secondChannelBw=repcap.SecondChannelBw.Default, thirdChannelBw=repcap.ThirdChannelBw.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:OBWLimit:CAGGregation:CBANdwidth<Band1>:CBANdwidth<Band2>:CBANdwidth<Band3> \n
		Snippet: driver.configure.lteMeas.multiEval.limit.seMask.obwLimit.carrierAggregation.channelBw1st.channelBw2nd.channelBw3rd.set(obw_limit = 1.0, firstChannelBw = repcap.FirstChannelBw.Default, secondChannelBw = repcap.SecondChannelBw.Default, thirdChannelBw = repcap.ThirdChannelBw.Default) \n
		Defines an upper limit for the occupied bandwidth. The settings are defined separately for each channel bandwidth
		combination, for three aggregated carriers. The following bandwidth combinations are supported: Example: For the first
		line in the figure, use ...:CBANdwidth200:CBANdwidth150:CBANdwidth100. \n
			:param obw_limit: (float or boolean) No help available
			:param firstChannelBw: optional repeated capability selector. Default value: Bw50 (settable in the interface 'ChannelBw1st')
			:param secondChannelBw: optional repeated capability selector. Default value: Bw50 (settable in the interface 'ChannelBw2nd')
			:param thirdChannelBw: optional repeated capability selector. Default value: Bw100 (settable in the interface 'ChannelBw3rd')
		"""
		param = Conversions.decimal_or_bool_value_to_str(obw_limit)
		firstChannelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(firstChannelBw, repcap.FirstChannelBw)
		secondChannelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(secondChannelBw, repcap.SecondChannelBw)
		thirdChannelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(thirdChannelBw, repcap.ThirdChannelBw)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:OBWLimit:CAGGregation:CBANdwidth{firstChannelBw_cmd_val}:CBANdwidth{secondChannelBw_cmd_val}:CBANdwidth{thirdChannelBw_cmd_val} {param}')

	def get(self, firstChannelBw=repcap.FirstChannelBw.Default, secondChannelBw=repcap.SecondChannelBw.Default, thirdChannelBw=repcap.ThirdChannelBw.Default) -> float or bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:OBWLimit:CAGGregation:CBANdwidth<Band1>:CBANdwidth<Band2>:CBANdwidth<Band3> \n
		Snippet: value: float or bool = driver.configure.lteMeas.multiEval.limit.seMask.obwLimit.carrierAggregation.channelBw1st.channelBw2nd.channelBw3rd.get(firstChannelBw = repcap.FirstChannelBw.Default, secondChannelBw = repcap.SecondChannelBw.Default, thirdChannelBw = repcap.ThirdChannelBw.Default) \n
		Defines an upper limit for the occupied bandwidth. The settings are defined separately for each channel bandwidth
		combination, for three aggregated carriers. The following bandwidth combinations are supported: Example: For the first
		line in the figure, use ...:CBANdwidth200:CBANdwidth150:CBANdwidth100. \n
			:param firstChannelBw: optional repeated capability selector. Default value: Bw50 (settable in the interface 'ChannelBw1st')
			:param secondChannelBw: optional repeated capability selector. Default value: Bw50 (settable in the interface 'ChannelBw2nd')
			:param thirdChannelBw: optional repeated capability selector. Default value: Bw100 (settable in the interface 'ChannelBw3rd')
			:return: obw_limit: (float or boolean) No help available"""
		firstChannelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(firstChannelBw, repcap.FirstChannelBw)
		secondChannelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(secondChannelBw, repcap.SecondChannelBw)
		thirdChannelBw_cmd_val = self._cmd_group.get_repcap_cmd_value(thirdChannelBw, repcap.ThirdChannelBw)
		response = self._core.io.query_str(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:OBWLimit:CAGGregation:CBANdwidth{firstChannelBw_cmd_val}:CBANdwidth{secondChannelBw_cmd_val}:CBANdwidth{thirdChannelBw_cmd_val}?')
		return Conversions.str_to_float_or_bool(response)

	def clone(self) -> 'ChannelBw3rdCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = ChannelBw3rdCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
