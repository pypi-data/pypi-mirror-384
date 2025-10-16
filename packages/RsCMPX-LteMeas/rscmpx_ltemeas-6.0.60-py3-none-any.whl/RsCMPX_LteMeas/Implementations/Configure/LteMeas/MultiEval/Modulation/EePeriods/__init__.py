from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class EePeriodsCls:
	"""EePeriods commands group definition. 3 total commands, 1 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("eePeriods", core, parent)

	@property
	def pusch(self):
		"""pusch commands group. 0 Sub-classes, 2 commands."""
		if not hasattr(self, '_pusch'):
			from .Pusch import PuschCls
			self._pusch = PuschCls(self._core, self._cmd_group)
		return self._pusch

	def get_pucch(self) -> bool:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:MODulation:EEPeriods:PUCCh \n
		Snippet: value: bool = driver.configure.lteMeas.multiEval.modulation.eePeriods.get_pucch() \n
		Enables or disables EVM exclusion periods for slots with detected channel type 'PUCCH'. If enabled, the first and the
		last SC-FDMA symbol of each slot is excluded from the calculation of EVM, magnitude error and phase error single value
		results. If the last symbol of a slot is already excluded because SRS signals are allowed, the second but last symbol is
		also excluded. \n
			:return: pucch: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:MODulation:EEPeriods:PUCCh?')
		return Conversions.str_to_bool(response)

	def set_pucch(self, pucch: bool) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:MODulation:EEPeriods:PUCCh \n
		Snippet: driver.configure.lteMeas.multiEval.modulation.eePeriods.set_pucch(pucch = False) \n
		Enables or disables EVM exclusion periods for slots with detected channel type 'PUCCH'. If enabled, the first and the
		last SC-FDMA symbol of each slot is excluded from the calculation of EVM, magnitude error and phase error single value
		results. If the last symbol of a slot is already excluded because SRS signals are allowed, the second but last symbol is
		also excluded. \n
			:param pucch: No help available
		"""
		param = Conversions.bool_to_str(pucch)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:MODulation:EEPeriods:PUCCh {param}')

	def clone(self) -> 'EePeriodsCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = EePeriodsCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
