from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SpectrumCls:
	"""Spectrum commands group definition. 2 total commands, 0 Subgroups, 2 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("spectrum", core, parent)

	def get_se_mask(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SCOunt:SPECtrum:SEMask \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.scount.spectrum.get_se_mask() \n
		Specifies the statistic count of the measurement. The statistic count is equal to the number of measurement intervals per
		single shot. Separate statistic counts for ACLR and spectrum emission mask measurements are supported. \n
			:return: statistic_count: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:SCOunt:SPECtrum:SEMask?')
		return Conversions.str_to_int(response)

	def set_se_mask(self, statistic_count: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SCOunt:SPECtrum:SEMask \n
		Snippet: driver.configure.lteMeas.multiEval.scount.spectrum.set_se_mask(statistic_count = 1) \n
		Specifies the statistic count of the measurement. The statistic count is equal to the number of measurement intervals per
		single shot. Separate statistic counts for ACLR and spectrum emission mask measurements are supported. \n
			:param statistic_count: No help available
		"""
		param = Conversions.decimal_value_to_str(statistic_count)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:SCOunt:SPECtrum:SEMask {param}')

	def get_aclr(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SCOunt:SPECtrum:ACLR \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.scount.spectrum.get_aclr() \n
		Specifies the statistic count of the measurement. The statistic count is equal to the number of measurement intervals per
		single shot. Separate statistic counts for ACLR and spectrum emission mask measurements are supported. \n
			:return: statistic_count: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:SCOunt:SPECtrum:ACLR?')
		return Conversions.str_to_int(response)

	def set_aclr(self, statistic_count: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SCOunt:SPECtrum:ACLR \n
		Snippet: driver.configure.lteMeas.multiEval.scount.spectrum.set_aclr(statistic_count = 1) \n
		Specifies the statistic count of the measurement. The statistic count is equal to the number of measurement intervals per
		single shot. Separate statistic counts for ACLR and spectrum emission mask measurements are supported. \n
			:param statistic_count: No help available
		"""
		param = Conversions.decimal_value_to_str(statistic_count)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:SCOunt:SPECtrum:ACLR {param}')
