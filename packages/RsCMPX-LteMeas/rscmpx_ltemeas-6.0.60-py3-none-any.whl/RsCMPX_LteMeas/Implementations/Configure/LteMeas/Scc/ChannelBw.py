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

	def set(self, channel_bw: enums.ChannelBandwidth, secondaryCC=repcap.SecondaryCC.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:SCC<Nr>:CBANdwidth \n
		Snippet: driver.configure.lteMeas.scc.channelBw.set(channel_bw = enums.ChannelBandwidth.B014, secondaryCC = repcap.SecondaryCC.Default) \n
		No command help available \n
			:param channel_bw: No help available
			:param secondaryCC: optional repeated capability selector. Default value: CC1 (settable in the interface 'Scc')
		"""
		param = Conversions.enum_scalar_to_str(channel_bw, enums.ChannelBandwidth)
		secondaryCC_cmd_val = self._cmd_group.get_repcap_cmd_value(secondaryCC, repcap.SecondaryCC)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:SCC{secondaryCC_cmd_val}:CBANdwidth {param}')

	# noinspection PyTypeChecker
	def get(self, secondaryCC=repcap.SecondaryCC.Default) -> enums.ChannelBandwidth:
		"""CONFigure:LTE:MEASurement<Instance>:SCC<Nr>:CBANdwidth \n
		Snippet: value: enums.ChannelBandwidth = driver.configure.lteMeas.scc.channelBw.get(secondaryCC = repcap.SecondaryCC.Default) \n
		No command help available \n
			:param secondaryCC: optional repeated capability selector. Default value: CC1 (settable in the interface 'Scc')
			:return: channel_bw: No help available"""
		secondaryCC_cmd_val = self._cmd_group.get_repcap_cmd_value(secondaryCC, repcap.SecondaryCC)
		response = self._core.io.query_str(f'CONFigure:LTE:MEASurement<Instance>:SCC{secondaryCC_cmd_val}:CBANdwidth?')
		return Conversions.str_to_scalar_enum(response, enums.ChannelBandwidth)
