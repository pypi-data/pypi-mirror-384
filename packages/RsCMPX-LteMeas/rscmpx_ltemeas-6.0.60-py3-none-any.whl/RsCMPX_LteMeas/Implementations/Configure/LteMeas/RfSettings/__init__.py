from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup
from .....Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class RfSettingsCls:
	"""RfSettings commands group definition. 10 total commands, 4 Subgroups, 6 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("rfSettings", core, parent)

	@property
	def pcc(self):
		"""pcc commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_pcc'):
			from .Pcc import PccCls
			self._pcc = PccCls(self._core, self._cmd_group)
		return self._pcc

	@property
	def scc(self):
		"""scc commands group. 1 Sub-classes, 0 commands."""
		if not hasattr(self, '_scc'):
			from .Scc import SccCls
			self._scc = SccCls(self._core, self._cmd_group)
		return self._scc

	@property
	def cc(self):
		"""cc commands group. 1 Sub-classes, 0 commands."""
		if not hasattr(self, '_cc'):
			from .Cc import CcCls
			self._cc = CcCls(self._core, self._cmd_group)
		return self._cc

	@property
	def lrStart(self):
		"""lrStart commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_lrStart'):
			from .LrStart import LrStartCls
			self._lrStart = LrStartCls(self._core, self._cmd_group)
		return self._lrStart

	def get_eattenuation(self) -> float:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings:EATTenuation \n
		Snippet: value: float = driver.configure.lteMeas.rfSettings.get_eattenuation() \n
		Defines an external attenuation (or gain, if the value is negative) , to be applied to the input connector. With full RF
		path sharing, this command is not applicable. \n
			:return: rf_input_ext_att: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:RFSettings:EATTenuation?')
		return Conversions.str_to_float(response)

	def set_eattenuation(self, rf_input_ext_att: float) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings:EATTenuation \n
		Snippet: driver.configure.lteMeas.rfSettings.set_eattenuation(rf_input_ext_att = 1.0) \n
		Defines an external attenuation (or gain, if the value is negative) , to be applied to the input connector. With full RF
		path sharing, this command is not applicable. \n
			:param rf_input_ext_att: No help available
		"""
		param = Conversions.decimal_value_to_str(rf_input_ext_att)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:RFSettings:EATTenuation {param}')

	def get_umargin(self) -> float:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings:UMARgin \n
		Snippet: value: float = driver.configure.lteMeas.rfSettings.get_umargin() \n
		Sets the margin that the measurement adds to the expected nominal power to determine the reference power. The reference
		power minus the external input attenuation must be within the power range of the selected input connector. Refer to the
		specifications document. With full RF path sharing, this command is not applicable. \n
			:return: user_margin: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:RFSettings:UMARgin?')
		return Conversions.str_to_float(response)

	def set_umargin(self, user_margin: float) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings:UMARgin \n
		Snippet: driver.configure.lteMeas.rfSettings.set_umargin(user_margin = 1.0) \n
		Sets the margin that the measurement adds to the expected nominal power to determine the reference power. The reference
		power minus the external input attenuation must be within the power range of the selected input connector. Refer to the
		specifications document. With full RF path sharing, this command is not applicable. \n
			:param user_margin: No help available
		"""
		param = Conversions.decimal_value_to_str(user_margin)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:RFSettings:UMARgin {param}')

	def get_envelope_power(self) -> float:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings:ENPower \n
		Snippet: value: float = driver.configure.lteMeas.rfSettings.get_envelope_power() \n
		Sets the expected nominal power of the measured RF signal. With full RF path sharing, use the signaling commands
		controlling the uplink power. \n
			:return: exp_nom_pow: The range of the expected nominal power can be calculated as follows: Range (Expected Nominal Power) = Range (Input Power) + External Attenuation - User Margin The input power range is stated in the specifications document.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:RFSettings:ENPower?')
		return Conversions.str_to_float(response)

	def set_envelope_power(self, exp_nom_pow: float) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings:ENPower \n
		Snippet: driver.configure.lteMeas.rfSettings.set_envelope_power(exp_nom_pow = 1.0) \n
		Sets the expected nominal power of the measured RF signal. With full RF path sharing, use the signaling commands
		controlling the uplink power. \n
			:param exp_nom_pow: The range of the expected nominal power can be calculated as follows: Range (Expected Nominal Power) = Range (Input Power) + External Attenuation - User Margin The input power range is stated in the specifications document.
		"""
		param = Conversions.decimal_value_to_str(exp_nom_pow)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:RFSettings:ENPower {param}')

	def get_foffset(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings:FOFFset \n
		Snippet: value: int = driver.configure.lteMeas.rfSettings.get_foffset() \n
		No command help available \n
			:return: offset: No help available
		"""
		response = self._core.io.query_str_with_opc('CONFigure:LTE:MEASurement<Instance>:RFSettings:FOFFset?')
		return Conversions.str_to_int(response)

	def set_foffset(self, offset: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings:FOFFset \n
		Snippet: driver.configure.lteMeas.rfSettings.set_foffset(offset = 1) \n
		No command help available \n
			:param offset: No help available
		"""
		param = Conversions.decimal_value_to_str(offset)
		self._core.io.write_with_opc(f'CONFigure:LTE:MEASurement<Instance>:RFSettings:FOFFset {param}')

	def get_ml_offset(self) -> float:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings:MLOFfset \n
		Snippet: value: float = driver.configure.lteMeas.rfSettings.get_ml_offset() \n
		No command help available \n
			:return: mix_lev_offset: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:RFSettings:MLOFfset?')
		return Conversions.str_to_float(response)

	def set_ml_offset(self, mix_lev_offset: float) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings:MLOFfset \n
		Snippet: driver.configure.lteMeas.rfSettings.set_ml_offset(mix_lev_offset = 1.0) \n
		No command help available \n
			:param mix_lev_offset: No help available
		"""
		param = Conversions.decimal_value_to_str(mix_lev_offset)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:RFSettings:MLOFfset {param}')

	def get_lr_interval(self) -> float:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings:LRINterval \n
		Snippet: value: float = driver.configure.lteMeas.rfSettings.get_lr_interval() \n
		Defines the measurement interval for level adjustment. \n
			:return: lvl_rang_interval: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:RFSettings:LRINterval?')
		return Conversions.str_to_float(response)

	def set_lr_interval(self, lvl_rang_interval: float) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings:LRINterval \n
		Snippet: driver.configure.lteMeas.rfSettings.set_lr_interval(lvl_rang_interval = 1.0) \n
		Defines the measurement interval for level adjustment. \n
			:param lvl_rang_interval: No help available
		"""
		param = Conversions.decimal_value_to_str(lvl_rang_interval)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:RFSettings:LRINterval {param}')

	def clone(self) -> 'RfSettingsCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = RfSettingsCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
