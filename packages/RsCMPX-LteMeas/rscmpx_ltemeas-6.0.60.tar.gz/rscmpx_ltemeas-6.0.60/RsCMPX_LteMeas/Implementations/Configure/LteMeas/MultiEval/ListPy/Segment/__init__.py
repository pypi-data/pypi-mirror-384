from .......Internal.Core import Core
from .......Internal.CommandsGroup import CommandsGroup
from .......Internal.RepeatedCapability import RepeatedCapability
from ....... import repcap


# noinspection PyPep8Naming,PyAttributeOutsideInit,SpellCheckingInspection
class SegmentCls:
	"""Segment commands group definition. 18 total commands, 15 Subgroups, 0 group commands
	Repeated Capability: Segment, default value after init: Segment.Nr1"""

	def __init__(self, core: Core, parent):
		self._core = core
		self._cmd_group = CommandsGroup("segment", core, parent)
		self._cmd_group.rep_cap = RepeatedCapability(self._cmd_group.group_name, 'repcap_segment_get', 'repcap_segment_set', repcap.Segment.Nr1)

	def repcap_segment_set(self, segment: repcap.Segment) -> None:
		"""Repeated Capability default value numeric suffix.
		This value is used, if you do not explicitely set it in the child set/get methods, or if you leave it to Segment.Default.
		Default value after init: Segment.Nr1"""
		self._cmd_group.set_repcap_enum_value(segment)

	def repcap_segment_get(self) -> repcap.Segment:
		"""Returns the current default repeated capability for the child set/get methods"""
		# noinspection PyTypeChecker
		return self._cmd_group.get_repcap_enum_value()

	@property
	def scc(self):
		"""scc commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_scc'):
			from .Scc import SccCls
			self._scc = SccCls(self._core, self._cmd_group)
		return self._scc

	@property
	def cc(self):
		"""cc commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_cc'):
			from .Cc import CcCls
			self._cc = CcCls(self._core, self._cmd_group)
		return self._cc

	@property
	def carrierAggregation(self):
		"""carrierAggregation commands group. 2 Sub-classes, 0 commands."""
		if not hasattr(self, '_carrierAggregation'):
			from .CarrierAggregation import CarrierAggregationCls
			self._carrierAggregation = CarrierAggregationCls(self._core, self._cmd_group)
		return self._carrierAggregation

	@property
	def setup(self):
		"""setup commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_setup'):
			from .Setup import SetupCls
			self._setup = SetupCls(self._core, self._cmd_group)
		return self._setup

	@property
	def tdd(self):
		"""tdd commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_tdd'):
			from .Tdd import TddCls
			self._tdd = TddCls(self._core, self._cmd_group)
		return self._tdd

	@property
	def rbAllocation(self):
		"""rbAllocation commands group. 1 Sub-classes, 1 commands."""
		if not hasattr(self, '_rbAllocation'):
			from .RbAllocation import RbAllocationCls
			self._rbAllocation = RbAllocationCls(self._core, self._cmd_group)
		return self._rbAllocation

	@property
	def modulation(self):
		"""modulation commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_modulation'):
			from .Modulation import ModulationCls
			self._modulation = ModulationCls(self._core, self._cmd_group)
		return self._modulation

	@property
	def seMask(self):
		"""seMask commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_seMask'):
			from .SeMask import SeMaskCls
			self._seMask = SeMaskCls(self._core, self._cmd_group)
		return self._seMask

	@property
	def aclr(self):
		"""aclr commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_aclr'):
			from .Aclr import AclrCls
			self._aclr = AclrCls(self._core, self._cmd_group)
		return self._aclr

	@property
	def pmonitor(self):
		"""pmonitor commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_pmonitor'):
			from .Pmonitor import PmonitorCls
			self._pmonitor = PmonitorCls(self._core, self._cmd_group)
		return self._pmonitor

	@property
	def power(self):
		"""power commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_power'):
			from .Power import PowerCls
			self._power = PowerCls(self._core, self._cmd_group)
		return self._power

	@property
	def emtc(self):
		"""emtc commands group. 1 Sub-classes, 0 commands."""
		if not hasattr(self, '_emtc'):
			from .Emtc import EmtcCls
			self._emtc = EmtcCls(self._core, self._cmd_group)
		return self._emtc

	@property
	def plcId(self):
		"""plcId commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_plcId'):
			from .PlcId import PlcIdCls
			self._plcId = PlcIdCls(self._core, self._cmd_group)
		return self._plcId

	@property
	def singleCmw(self):
		"""singleCmw commands group. 1 Sub-classes, 0 commands."""
		if not hasattr(self, '_singleCmw'):
			from .SingleCmw import SingleCmwCls
			self._singleCmw = SingleCmwCls(self._core, self._cmd_group)
		return self._singleCmw

	@property
	def cidx(self):
		"""cidx commands group. 0 Sub-classes, 1 commands."""
		if not hasattr(self, '_cidx'):
			from .Cidx import CidxCls
			self._cidx = CidxCls(self._core, self._cmd_group)
		return self._cidx

	def clone(self) -> 'SegmentCls':
		"""Clones the group by creating new object from it and its whole existing subgroups
		Also copies all the existing default Repeated Capabilities setting,
		which you can change independently without affecting the original group"""
		new_group = SegmentCls(self._core, self._cmd_group.parent)
		self._cmd_group.synchronize_repcaps(new_group)
		return new_group
