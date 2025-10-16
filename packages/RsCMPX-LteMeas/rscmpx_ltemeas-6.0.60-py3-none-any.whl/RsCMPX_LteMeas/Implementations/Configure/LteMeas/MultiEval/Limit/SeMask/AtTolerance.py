from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal import Conversions
from .......Internal.RepeatedCapability import RepeatedCapability
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class AtToleranceCls:
	"""AtTolerance commands group definition. 1 total commands, 0 Subgroups, 1 group commands
	Repeated Capability: EutraBand, default value after init: EutraBand.Nr30"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("atTolerance", core, parent)
		self._cmd_group.rep_cap = RepeatedCapability(self._cmd_group.group_name, 'repcap_eutraBand_get', 'repcap_eutraBand_set', repcap.EutraBand.Nr30)

	def repcap_eutraBand_set(self, eutraBand: repcap.EutraBand) -> None:
		"""Repeated Capability default value numeric suffix.
		This value is used, if you do not explicitely set it in the child set/get methods, or if you leave it to EutraBand.Default.
		Default value after init: EutraBand.Nr30"""
		self._cmd_group.set_repcap_enum_value(eutraBand)

	def repcap_eutraBand_get(self) -> repcap.EutraBand:
		"""Returns the current default repeated capability for the child set/get methods"""
		# noinspection PyTypeChecker
		return self._cmd_group.get_repcap_enum_value()

	def set(self, add_test_tol: float, eutraBand=repcap.EutraBand.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:ATTolerance<EUTRAband> \n
		Snippet: driver.configure.lteMeas.multiEval.limit.seMask.atTolerance.set(add_test_tol = 1.0, eutraBand = repcap.EutraBand.Default) \n
		Defines additional test tolerances for the emission masks. The tolerance is added to the power values of all general and
		additional spectrum emission masks. A positive tolerance value relaxes the limits. For operating bands below 3 GHz, there
		is no additional test tolerance. You can define different additional test tolerances for bands above 3 GHz and for bands
		above 5 GHz. \n
			:param add_test_tol: Additional test tolerance
			:param eutraBand: optional repeated capability selector. Default value: Nr30 (settable in the interface 'AtTolerance')
		"""
		param = Conversions.decimal_value_to_str(add_test_tol)
		eutraBand_cmd_val = self._cmd_group.get_repcap_cmd_value(eutraBand, repcap.EutraBand)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:ATTolerance{eutraBand_cmd_val} {param}')

	def get(self, eutraBand=repcap.EutraBand.Default) -> float:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:ATTolerance<EUTRAband> \n
		Snippet: value: float = driver.configure.lteMeas.multiEval.limit.seMask.atTolerance.get(eutraBand = repcap.EutraBand.Default) \n
		Defines additional test tolerances for the emission masks. The tolerance is added to the power values of all general and
		additional spectrum emission masks. A positive tolerance value relaxes the limits. For operating bands below 3 GHz, there
		is no additional test tolerance. You can define different additional test tolerances for bands above 3 GHz and for bands
		above 5 GHz. \n
			:param eutraBand: optional repeated capability selector. Default value: Nr30 (settable in the interface 'AtTolerance')
			:return: add_test_tol: Additional test tolerance"""
		eutraBand_cmd_val = self._cmd_group.get_repcap_cmd_value(eutraBand, repcap.EutraBand)
		response = self._core.io.query_str(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIMit:SEMask:ATTolerance{eutraBand_cmd_val}?')
		return Conversions.str_to_float(response)

	def clone(self) -> 'AtToleranceCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = AtToleranceCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
