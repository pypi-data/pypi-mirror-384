from ....Internal.Core import Core
from ....Internal.CommandsGroup import CommandsGroup
from ....Internal import Conversions
from .... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class NetworkCls:
	"""Network commands group definition. 3 total commands, 0 Subgroups, 3 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("network", core, parent)

	# noinspection PyTypeChecker
	def get_rfp_sharing(self) -> enums.NetworkSharing:
		"""CONFigure:LTE:MEASurement<Instance>:NETWork:RFPSharing \n
		Snippet: value: enums.NetworkSharing = driver.configure.lteMeas.network.get_rfp_sharing() \n
		Selects the RF path sharing mode for a measurement with coupling to signaling settings. \n
			:return: sharing: NSHared: not shared (independent connection) OCONnection: only connection shared FSHared: fully shared (only for RF unit)
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:NETWork:RFPSharing?')
		return Conversions.str_to_scalar_enum(response, enums.NetworkSharing)

	def set_rfp_sharing(self, sharing: enums.NetworkSharing) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:NETWork:RFPSharing \n
		Snippet: driver.configure.lteMeas.network.set_rfp_sharing(sharing = enums.NetworkSharing.FSHared) \n
		Selects the RF path sharing mode for a measurement with coupling to signaling settings. \n
			:param sharing: NSHared: not shared (independent connection) OCONnection: only connection shared FSHared: fully shared (only for RF unit)
		"""
		param = Conversions.enum_scalar_to_str(sharing, enums.NetworkSharing)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:NETWork:RFPSharing {param}')

	# noinspection PyTypeChecker
	def get_band(self) -> enums.Band:
		"""CONFigure:LTE:MEASurement<Instance>:NETWork:BAND \n
		Snippet: value: enums.Band = driver.configure.lteMeas.network.get_band() \n
		No command help available \n
			:return: band: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:NETWork:BAND?')
		return Conversions.str_to_scalar_enum(response, enums.Band)

	def set_band(self, band: enums.Band) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:NETWork:BAND \n
		Snippet: driver.configure.lteMeas.network.set_band(band = enums.Band.OB1) \n
		No command help available \n
			:param band: No help available
		"""
		param = Conversions.enum_scalar_to_str(band, enums.Band)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:NETWork:BAND {param}')

	# noinspection PyTypeChecker
	def get_dmode(self) -> enums.Mode:
		"""CONFigure:LTE:MEASurement<Instance>:NETWork:DMODe \n
		Snippet: value: enums.Mode = driver.configure.lteMeas.network.get_dmode() \n
		No command help available \n
			:return: mode: No help available
		"""
		response = self._core.io.query_str_with_opc('CONFigure:LTE:MEASurement<Instance>:NETWork:DMODe?')
		return Conversions.str_to_scalar_enum(response, enums.Mode)

	def set_dmode(self, mode: enums.Mode) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:NETWork:DMODe \n
		Snippet: driver.configure.lteMeas.network.set_dmode(mode = enums.Mode.FDD) \n
		No command help available \n
			:param mode: No help available
		"""
		param = Conversions.enum_scalar_to_str(mode, enums.Mode)
		self._core.io.write_with_opc(f'CONFigure:LTE:MEASurement<Instance>:NETWork:DMODe {param}')
