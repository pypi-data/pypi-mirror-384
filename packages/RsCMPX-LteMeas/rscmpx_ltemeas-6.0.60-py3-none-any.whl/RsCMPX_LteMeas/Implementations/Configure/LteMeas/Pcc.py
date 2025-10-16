from ....Internal.Core import Core
from ....Internal.CommandsGroup import CommandsGroup
from ....Internal import Conversions
from .... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class PccCls:
	"""Pcc commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("pcc", core, parent)

	# noinspection PyTypeChecker
	def get_channel_bw(self) -> enums.ChannelBandwidth:
		"""CONFigure:LTE:MEASurement<Instance>[:PCC]:CBANdwidth \n
		Snippet: value: enums.ChannelBandwidth = driver.configure.lteMeas.pcc.get_channel_bw() \n
		No command help available \n
			:return: channel_bw: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:PCC:CBANdwidth?')
		return Conversions.str_to_scalar_enum(response, enums.ChannelBandwidth)

	def set_channel_bw(self, channel_bw: enums.ChannelBandwidth) -> None:
		"""CONFigure:LTE:MEASurement<Instance>[:PCC]:CBANdwidth \n
		Snippet: driver.configure.lteMeas.pcc.set_channel_bw(channel_bw = enums.ChannelBandwidth.B014) \n
		No command help available \n
			:param channel_bw: No help available
		"""
		param = Conversions.enum_scalar_to_str(channel_bw, enums.ChannelBandwidth)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:PCC:CBANdwidth {param}')
