from typing import List

from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class EwLengthCls:
	"""EwLength commands group definition. 2 total commands, 1 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("ewLength", core, parent)

	@property
	def pformat(self):
		"""pformat commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_pformat'):
			from .Pformat import PformatCls
			self._pformat = PformatCls(self._core, self._cmd_group)
		return self._pformat

	def get_value(self) -> List[int]:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:MODulation:EWLength \n
		Snippet: value: List[int] = driver.configure.lteMeas.prach.modulation.ewLength.get_value() \n
		Specifies the EVM window length in samples for all preamble formats. \n
			:return: evm_window_length: No help available
		"""
		response = self._core.io.query_bin_or_ascii_int_list('CONFigure:LTE:MEASurement<Instance>:PRACh:MODulation:EWLength?')
		return response

	def set_value(self, evm_window_length: List[int]) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:PRACh:MODulation:EWLength \n
		Snippet: driver.configure.lteMeas.prach.modulation.ewLength.set_value(evm_window_length = [1, 2, 3]) \n
		Specifies the EVM window length in samples for all preamble formats. \n
			:param evm_window_length: No help available
		"""
		param = Conversions.list_to_csv_str(evm_window_length)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:PRACh:MODulation:EWLength {param}')

	def clone(self) -> 'EwLengthCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = EwLengthCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
