from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class NrbCls:
	"""Nrb commands group definition. 3 total commands, 0 Subgroups, 3 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("nrb", core, parent)

	def get_pscch(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:NRB:PSCCh \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.rbAllocation.nrb.get_pscch() \n
		Specifies the number of allocated RBs for the PSCCH in the measured slot. For manual RB allocation definition, for
		sidelink signals. \n
			:return: no_rb: The value is fixed.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:NRB:PSCCh?')
		return Conversions.str_to_int(response)

	def set_pscch(self, no_rb: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:NRB:PSCCh \n
		Snippet: driver.configure.lteMeas.multiEval.rbAllocation.nrb.set_pscch(no_rb = 1) \n
		Specifies the number of allocated RBs for the PSCCH in the measured slot. For manual RB allocation definition, for
		sidelink signals. \n
			:param no_rb: The value is fixed.
		"""
		param = Conversions.decimal_value_to_str(no_rb)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:NRB:PSCCh {param}')

	def get_pssch(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:NRB:PSSCh \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.rbAllocation.nrb.get_pssch() \n
		Specifies the number of allocated RBs for the PSSCH in the measured slot. For manual RB allocation definition, for
		sidelink signals. \n
			:return: no_rb: For the allowed input range, see 'Sidelink resource block allocation'.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:NRB:PSSCh?')
		return Conversions.str_to_int(response)

	def set_pssch(self, no_rb: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:NRB:PSSCh \n
		Snippet: driver.configure.lteMeas.multiEval.rbAllocation.nrb.set_pssch(no_rb = 1) \n
		Specifies the number of allocated RBs for the PSSCH in the measured slot. For manual RB allocation definition, for
		sidelink signals. \n
			:param no_rb: For the allowed input range, see 'Sidelink resource block allocation'.
		"""
		param = Conversions.decimal_value_to_str(no_rb)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:NRB:PSSCh {param}')

	def get_value(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:NRB \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.rbAllocation.nrb.get_value() \n
		Specifies the number of allocated RBs in the measured slot. For manual RB allocation definition, for uplink signals
		without multi-cluster allocation. \n
			:return: no_rb: For the allowed input range, see 'Uplink resource block allocation'.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:NRB?')
		return Conversions.str_to_int(response)

	def set_value(self, no_rb: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:NRB \n
		Snippet: driver.configure.lteMeas.multiEval.rbAllocation.nrb.set_value(no_rb = 1) \n
		Specifies the number of allocated RBs in the measured slot. For manual RB allocation definition, for uplink signals
		without multi-cluster allocation. \n
			:param no_rb: For the allowed input range, see 'Uplink resource block allocation'.
		"""
		param = Conversions.decimal_value_to_str(no_rb)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:NRB {param}')
