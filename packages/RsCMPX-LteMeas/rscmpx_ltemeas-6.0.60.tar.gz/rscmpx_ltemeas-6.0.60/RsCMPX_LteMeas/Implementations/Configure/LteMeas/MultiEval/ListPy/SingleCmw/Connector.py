from typing import List

from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal import Conversions
from ....... import enums


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ConnectorCls:
	"""Connector commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("connector", core, parent)

	# noinspection PyTypeChecker
	def get_all(self) -> List[enums.CmwsConnector]:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:CMWS:CONNector:ALL \n
		Snippet: value: List[enums.CmwsConnector] = driver.configure.lteMeas.multiEval.listPy.singleCmw.connector.get_all() \n
		No command help available \n
			:return: cmws_connector: No help available
		"""
		response = self._core.io.query_str('CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:CMWS:CONNector:ALL?')
		return Conversions.str_to_list_enum(response, enums.CmwsConnector)

	def set_all(self, cmws_connector: List[enums.CmwsConnector]) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:CMWS:CONNector:ALL \n
		Snippet: driver.configure.lteMeas.multiEval.listPy.singleCmw.connector.set_all(cmws_connector = [CmwsConnector.R11, CmwsConnector.RB8]) \n
		No command help available \n
			:param cmws_connector: No help available
		"""
		param = Conversions.enum_list_to_str(cmws_connector, enums.CmwsConnector)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:CMWS:CONNector:ALL {param}')
