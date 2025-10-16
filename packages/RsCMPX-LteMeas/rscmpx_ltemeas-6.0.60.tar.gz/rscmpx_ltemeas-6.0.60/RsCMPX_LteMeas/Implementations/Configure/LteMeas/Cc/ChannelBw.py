from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions
from ..... import enums
from ..... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ChannelBwCls:
	"""ChannelBw commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("channelBw", core, parent)

	def set(self, channel_bw: enums.ChannelBandwidth, carrierComponent=repcap.CarrierComponent.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:CC<Nr>:CBANdwidth \n
		Snippet: driver.configure.lteMeas.cc.channelBw.set(channel_bw = enums.ChannelBandwidth.B014, carrierComponent = repcap.CarrierComponent.Default) \n
		Selects the channel bandwidth of component carrier CC<no>. Without carrier aggregation, you can omit <no>. For Signal
		Path = Network, use [CONFigure:]SIGNaling:LTE:CELL:RFSettings:UL:BWIDth. \n
			:param channel_bw: B014: 1.4 MHz B030: 3 MHz B050: 5 MHz B100: 10 MHz B150: 15 MHz B200: 20 MHz
			:param carrierComponent: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Cc')
		"""
		param = Conversions.enum_scalar_to_str(channel_bw, enums.ChannelBandwidth)
		carrierComponent_cmd_val = self._cmd_group.get_repcap_cmd_value(carrierComponent, repcap.CarrierComponent)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:CC{carrierComponent_cmd_val}:CBANdwidth {param}')

	# noinspection PyTypeChecker
	def get(self, carrierComponent=repcap.CarrierComponent.Default) -> enums.ChannelBandwidth:
		"""CONFigure:LTE:MEASurement<Instance>:CC<Nr>:CBANdwidth \n
		Snippet: value: enums.ChannelBandwidth = driver.configure.lteMeas.cc.channelBw.get(carrierComponent = repcap.CarrierComponent.Default) \n
		Selects the channel bandwidth of component carrier CC<no>. Without carrier aggregation, you can omit <no>. For Signal
		Path = Network, use [CONFigure:]SIGNaling:LTE:CELL:RFSettings:UL:BWIDth. \n
			:param carrierComponent: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Cc')
			:return: channel_bw: B014: 1.4 MHz B030: 3 MHz B050: 5 MHz B100: 10 MHz B150: 15 MHz B200: 20 MHz"""
		carrierComponent_cmd_val = self._cmd_group.get_repcap_cmd_value(carrierComponent, repcap.CarrierComponent)
		response = self._core.io.query_str(f'CONFigure:LTE:MEASurement<Instance>:CC{carrierComponent_cmd_val}:CBANdwidth?')
		return Conversions.str_to_scalar_enum(response, enums.ChannelBandwidth)
