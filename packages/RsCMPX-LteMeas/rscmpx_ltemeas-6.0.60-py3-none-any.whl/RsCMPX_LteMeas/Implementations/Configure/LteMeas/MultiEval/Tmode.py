from typing import List

from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class TmodeCls:
	"""Tmode commands group definition. 3 total commands, 0 Subgroups, 3 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("tmode", core, parent)

	def get_scount(self) -> List[int]:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:TMODe:SCOunt \n
		Snippet: value: List[int] = driver.configure.lteMeas.multiEval.tmode.get_scount() \n
		Defines the subframe counts for all entries of the TPC Mode list. For the definition of the corresponding expected
		nominal power values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Tmode.envelopePower. \n
			:return: sub_frame_count: Comma-separated list of 16 values, for list entry number 0 to 15
		"""
		response = self._core.io.query_bin_or_ascii_int_list('CONFigure:LTE:MEASurement<Instance>:MEValuation:TMODe:SCOunt?')
		return response

	def set_scount(self, sub_frame_count: List[int]) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:TMODe:SCOunt \n
		Snippet: driver.configure.lteMeas.multiEval.tmode.set_scount(sub_frame_count = [1, 2, 3]) \n
		Defines the subframe counts for all entries of the TPC Mode list. For the definition of the corresponding expected
		nominal power values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Tmode.envelopePower. \n
			:param sub_frame_count: Comma-separated list of 16 values, for list entry number 0 to 15
		"""
		param = Conversions.list_to_csv_str(sub_frame_count)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:TMODe:SCOunt {param}')

	def get_envelope_power(self) -> List[float]:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:TMODe:ENPower \n
		Snippet: value: List[float] = driver.configure.lteMeas.multiEval.tmode.get_envelope_power() \n
		Defines the expected nominal power values for all entries of the TPC Mode list. For the definition of the corresponding
		subframe count values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Tmode.scount. \n
			:return: exp_nom_pow: Comma-separated list of 16 values, for list entry number 0 to 15 The range of the expected nominal power can be calculated as follows: Range (Expected Nominal Power) = Range (Input Power) + External Attenuation - User Margin The input power range is stated in the specifications document.
		"""
		response = self._core.io.query_bin_or_ascii_float_list('CONFigure:LTE:MEASurement<Instance>:MEValuation:TMODe:ENPower?')
		return response

	def set_envelope_power(self, exp_nom_pow: List[float]) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:TMODe:ENPower \n
		Snippet: driver.configure.lteMeas.multiEval.tmode.set_envelope_power(exp_nom_pow = [1.1, 2.2, 3.3]) \n
		Defines the expected nominal power values for all entries of the TPC Mode list. For the definition of the corresponding
		subframe count values, see method RsCMPX_LteMeas.Configure.LteMeas.MultiEval.Tmode.scount. \n
			:param exp_nom_pow: Comma-separated list of 16 values, for list entry number 0 to 15 The range of the expected nominal power can be calculated as follows: Range (Expected Nominal Power) = Range (Input Power) + External Attenuation - User Margin The input power range is stated in the specifications document.
		"""
		param = Conversions.list_to_csv_str(exp_nom_pow)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:TMODe:ENPower {param}')

	def get_rlevel(self) -> List[float]:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:TMODe:RLEVel \n
		Snippet: value: List[float] = driver.configure.lteMeas.multiEval.tmode.get_rlevel() \n
		Queries the reference level for all entries of the TPC Mode list. The reference level is calculated from the expected
		nominal power of each entry and the user margin. \n
			:return: reference_level: Comma-separated list of 16 values, for list entry number 0 to 15 The range of the reference levels can be calculated as follows: Range (Reference Level) = Range (Input Power) + External Attenuation The input power range is stated in the specifications document.
		"""
		response = self._core.io.query_bin_or_ascii_float_list('CONFigure:LTE:MEASurement<Instance>:MEValuation:TMODe:RLEVel?')
		return response
