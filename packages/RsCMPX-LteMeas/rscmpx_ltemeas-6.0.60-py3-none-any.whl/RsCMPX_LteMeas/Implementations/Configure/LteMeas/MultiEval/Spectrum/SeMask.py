from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal import Conversions
from ...... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SeMaskCls:
	"""SeMask commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("seMask", core, parent)

	# noinspection PyTypeChecker
	def get_mfilter(self) -> enums.MeasFilter:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SPECtrum:SEMask:MFILter \n
		Snippet: value: enums.MeasFilter = driver.configure.lteMeas.multiEval.spectrum.seMask.get_mfilter() \n
		Selects the resolution filter type for filter bandwidths of 50 kHz and greater. \n
			:return: meas_filter: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:SPECtrum:SEMask:MFILter?')
		return Conversions.str_to_scalar_enum(response, enums.MeasFilter)

	def set_mfilter(self, meas_filter: enums.MeasFilter) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:SPECtrum:SEMask:MFILter \n
		Snippet: driver.configure.lteMeas.multiEval.spectrum.seMask.set_mfilter(meas_filter = enums.MeasFilter.BANDpass) \n
		Selects the resolution filter type for filter bandwidths of 50 kHz and greater. \n
			:param meas_filter: No help available
		"""
		param = Conversions.enum_scalar_to_str(meas_filter, enums.MeasFilter)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:SPECtrum:SEMask:MFILter {param}')
