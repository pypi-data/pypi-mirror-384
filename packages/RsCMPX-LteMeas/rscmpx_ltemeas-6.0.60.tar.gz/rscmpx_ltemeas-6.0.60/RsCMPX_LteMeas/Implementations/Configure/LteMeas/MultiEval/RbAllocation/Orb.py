from ......Internal.Core import Core
from ......Internal.CommandsGroup import CommandsGroup
from ......Internal import Conversions


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class OrbCls:
	"""Orb commands group definition. 3 total commands, 0 Subgroups, 3 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("orb", core, parent)

	def get_pscch(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:ORB:PSCCh \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.rbAllocation.orb.get_pscch() \n
		Specifies the offset of the first allocated PSCCH resource block for manual RB allocation definition, for sidelink
		signals. \n
			:return: offset_rb: For the maximum number of RBs depending on the channel BW, see 'Uplink resource block allocation'.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:ORB:PSCCh?')
		return Conversions.str_to_int(response)

	def set_pscch(self, offset_rb: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:ORB:PSCCh \n
		Snippet: driver.configure.lteMeas.multiEval.rbAllocation.orb.set_pscch(offset_rb = 1) \n
		Specifies the offset of the first allocated PSCCH resource block for manual RB allocation definition, for sidelink
		signals. \n
			:param offset_rb: For the maximum number of RBs depending on the channel BW, see 'Uplink resource block allocation'.
		"""
		param = Conversions.decimal_value_to_str(offset_rb)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:ORB:PSCCh {param}')

	def get_pssch(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:ORB:PSSCh \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.rbAllocation.orb.get_pssch() \n
		Specifies the offset of the first allocated PSSCH resource block for manual RB allocation definition, for sidelink
		signals. \n
			:return: offset_rb: The range depends on the OffsetRB for the PSCCH, the channel BW and the number of allocated PSSCH RBs, see 'Sidelink resource block allocation'.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:ORB:PSSCh?')
		return Conversions.str_to_int(response)

	def set_pssch(self, offset_rb: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:ORB:PSSCh \n
		Snippet: driver.configure.lteMeas.multiEval.rbAllocation.orb.set_pssch(offset_rb = 1) \n
		Specifies the offset of the first allocated PSSCH resource block for manual RB allocation definition, for sidelink
		signals. \n
			:param offset_rb: The range depends on the OffsetRB for the PSCCH, the channel BW and the number of allocated PSSCH RBs, see 'Sidelink resource block allocation'.
		"""
		param = Conversions.decimal_value_to_str(offset_rb)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:ORB:PSSCh {param}')

	def get_value(self) -> int:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:ORB \n
		Snippet: value: int = driver.configure.lteMeas.multiEval.rbAllocation.orb.get_value() \n
		Specifies the offset of the first allocated resource block for manual RB allocation definition, for uplink signals
		without multi-cluster allocation. \n
			:return: offset_rb: For the maximum number of RBs depending on the channel BW, see 'Uplink resource block allocation'.
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:ORB?')
		return Conversions.str_to_int(response)

	def set_value(self, offset_rb: int) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:ORB \n
		Snippet: driver.configure.lteMeas.multiEval.rbAllocation.orb.set_value(offset_rb = 1) \n
		Specifies the offset of the first allocated resource block for manual RB allocation definition, for uplink signals
		without multi-cluster allocation. \n
			:param offset_rb: For the maximum number of RBs depending on the channel BW, see 'Uplink resource block allocation'.
		"""
		param = Conversions.decimal_value_to_str(offset_rb)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:RBALlocation:ORB {param}')
