from ........Internal.Core import Core
from ........Internal.CommandsGroup import CommandsGroup
from ........Internal import Conversions
from ........ import enums
from ........ import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class ConnectorCls:
	"""Connector commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("connector", core, parent)

	def set(self, cmws_connector: enums.CmwsConnector, segment=repcap.Segment.Default) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:CMWS:CONNector \n
		Snippet: driver.configure.lteMeas.multiEval.listPy.segment.singleCmw.connector.set(cmws_connector = enums.CmwsConnector.R11, segment = repcap.Segment.Default) \n
		No command help available \n
			:param cmws_connector: No help available
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
		"""
		param = Conversions.enum_scalar_to_str(cmws_connector, enums.CmwsConnector)
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:CMWS:CONNector {param}')

	# noinspection PyTypeChecker
	def get(self, segment=repcap.Segment.Default) -> enums.CmwsConnector:
		"""CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent<nr>:CMWS:CONNector \n
		Snippet: value: enums.CmwsConnector = driver.configure.lteMeas.multiEval.listPy.segment.singleCmw.connector.get(segment = repcap.Segment.Default) \n
		No command help available \n
			:param segment: optional repeated capability selector. Default value: Nr1 (settable in the interface 'Segment')
			:return: cmws_connector: No help available"""
		segment_cmd_val = self._cmd_group.get_repcap_cmd_value(segment, repcap.Segment)
		response = self._core.io.query_str(f'CONFigure:LTE:MEASurement<Instance>:MEValuation:LIST:SEGMent{segment_cmd_val}:CMWS:CONNector?')
		return Conversions.str_to_scalar_enum(response, enums.CmwsConnector)
