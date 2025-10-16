from .....Internal.Core import Core
from .....Internal.CommandsGroup import CommandsGroup


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class LrStartCls:
	"""LrStart commands group definition. 1 total commands, 0 Subgroups, 1 group commands"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("lrStart", core, parent)

	def set(self) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings:LRSTart \n
		Snippet: driver.configure.lteMeas.rfSettings.lrStart.set() \n
		Starts level adjustment. \n
		"""
		self._core.io.write(f'CONFigure:LTE:MEASurement<Instance>:RFSettings:LRSTart')

	def set_with_opc(self, opc_timeout_ms: int = -1) -> None:
		"""CONFigure:LTE:MEASurement<Instance>:RFSettings:LRSTart \n
		Snippet: driver.configure.lteMeas.rfSettings.lrStart.set_with_opc() \n
		Starts level adjustment. \n
		Same as set, but waits for the operation to complete before continuing further. Use the RsCMPX_LteMeas.utilities.opc_timeout_set() to set the timeout value. \n
			:param opc_timeout_ms: Maximum time to wait in milliseconds, valid only for this call."""
		self._core.io.write_with_opc(f'CONFigure:LTE:MEASurement<Instance>:RFSettings:LRSTart', opc_timeout_ms)
