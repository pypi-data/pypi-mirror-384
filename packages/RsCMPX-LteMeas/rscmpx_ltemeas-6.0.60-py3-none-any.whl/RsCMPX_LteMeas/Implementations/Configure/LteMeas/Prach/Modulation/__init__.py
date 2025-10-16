from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal import Conversions
from ...... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ModulationCls:
	"""Modulation commands group definition. 7 total commands, 2 Subgroups, 3 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("modulation", core, parent)

	@property
	def sindex(self):
		"""sindex commands group. 0 Sub-classes, 2 commands."""
		if not hasattr(self, '_sindex'):
			from .Sindex import SindexCls
			self._sindex = SindexCls(self._core, self._cmd_group)
		return self._sindex

	@property
	def ewLength(self):
		"""ewLength commands group. 1 Sub-classes, 1 commands."""
		if not hasattr(self, '_ewLength'):
			from .EwLength import EwLengthCls
			self._ewLength = EwLengthCls(self._core, self._cmd_group)
		return self._ewLength

	def get_lrs_index(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:MODulation:LRSindex \n
		Snippet: value: int = driver.configure.lteMeas.prach.modulation.get_lrs_index() \n
		Specifies the logical root sequence index to be used for generation of the preamble sequence. For Signal Path = Network,
		the setting is not configurable. \n
			:return: log_root_seq_index: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:PRACh:MODulation:LRSindex?')
		return Conversions.str_to_int(response)

	def set_lrs_index(self, log_root_seq_index: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:MODulation:LRSindex \n
		Snippet: driver.configure.lteMeas.prach.modulation.set_lrs_index(log_root_seq_index = 1) \n
		Specifies the logical root sequence index to be used for generation of the preamble sequence. For Signal Path = Network,
		the setting is not configurable. \n
			:param log_root_seq_index: No help available
		"""
		param = Conversions.decimal_value_to_str(log_root_seq_index)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:PRACh:MODulation:LRSindex {param}')

	def get_zcz_config(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:MODulation:ZCZConfig \n
		Snippet: value: int = driver.configure.lteMeas.prach.modulation.get_zcz_config() \n
		Specifies the zero correlation zone config, i.e. which NCS value of an NCS set is used for generation of the preamble
		sequence. For Signal Path = Network, the setting is not configurable. \n
			:return: zero_corr_zone_con: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:PRACh:MODulation:ZCZConfig?')
		return Conversions.str_to_int(response)

	def set_zcz_config(self, zero_corr_zone_con: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:MODulation:ZCZConfig \n
		Snippet: driver.configure.lteMeas.prach.modulation.set_zcz_config(zero_corr_zone_con = 1) \n
		Specifies the zero correlation zone config, i.e. which NCS value of an NCS set is used for generation of the preamble
		sequence. For Signal Path = Network, the setting is not configurable. \n
			:param zero_corr_zone_con: No help available
		"""
		param = Conversions.decimal_value_to_str(zero_corr_zone_con)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:PRACh:MODulation:ZCZConfig {param}')

	# noinspection PyTypeChecker
	def get_ew_position(self) -> enums.LowHigh:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:MODulation:EWPosition \n
		Snippet: value: enums.LowHigh = driver.configure.lteMeas.prach.modulation.get_ew_position() \n
		Specifies the position of the EVM window used for calculation of the trace results. \n
			:return: evm_window_pos: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:PRACh:MODulation:EWPosition?')
		return Conversions.str_to_scalar_enum(response, enums.LowHigh)

	def set_ew_position(self, evm_window_pos: enums.LowHigh) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:MODulation:EWPosition \n
		Snippet: driver.configure.lteMeas.prach.modulation.set_ew_position(evm_window_pos = enums.LowHigh.HIGH) \n
		Specifies the position of the EVM window used for calculation of the trace results. \n
			:param evm_window_pos: No help available
		"""
		param = Conversions.enum_scalar_to_str(evm_window_pos, enums.LowHigh)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:PRACh:MODulation:EWPosition {param}')

	def clone(self) -> 'ModulationCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = ModulationCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
