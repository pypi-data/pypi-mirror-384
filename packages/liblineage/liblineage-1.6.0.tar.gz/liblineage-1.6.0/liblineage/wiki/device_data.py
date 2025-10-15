#
# Copyright (C) 2022 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from datetime import date
import requests
from typing import Any, Dict, List, Literal, Optional, Sequence, Union
import yaml

from liblineage.constants.infra import GITHUB_ORG, GITHUB_ORG_URL
from liblineage.wiki.data_types.architecture_data import ArchitectureData
from liblineage.wiki.data_types.battery_data import BatteryData
from liblineage.wiki.data_types.bluetooth_data import BluetoothData
from liblineage.wiki.data_types.camera_data import CameraData
from liblineage.wiki.data_types.dimension_data import DimensionData
from liblineage.wiki.data_types.kernel_data import KernelData
from liblineage.wiki.data_types.network_data import NetworkData
from liblineage.wiki.data_types.peripherals_data import PeripheralsData
from liblineage.wiki.data_types.release_data import ReleaseData
from liblineage.wiki.data_types.screen_data import ScreenData
from liblineage.wiki.data_types.sdcard_data import SdcardData

class DeviceData:
	"""LineageOS wiki device data.

	Attributes:
	- architecture: The architecture of the device
	- battery: Battery info
	- bluetooth: Bluetooth support info
	- codename: The codename of the device
	- cpu: CPU name
	- cpu_cores: Number of CPU cores
	- cpu_freq: CPU frequency
	- current_branch: The current branch of the device
	- dimensions: Dimensions of the device
	- gpu: GPU name
	- image: The image of the device
	- install_method: The install method of the device
	- kernel: Kernel info
	- maintainers: The maintainers of the device
	- name: Commercial name of the device
	- network: The network of the device
	- peripherals: Peripherals supported by the device
	- release: The release date of the device
	- screen: Screen info
	- soc: The SoC of the device
	- tree: Device tree repository of the device
	- type: The form factor of the device
	- vendor: Brand name of the device vendor
	- vendor_short: Short name of the device vendor
	- versions: The versions of the device
	- wifi: The supported Wi-Fi bands of the device

	Optional attributes:
	- before_install: The before_install script for the device
	- before_lineage_install: The before_lineage_install script for the device
	- before_recovery_install: The before_recovery_install script for the device
	- cameras: The cameras of the device
	- carrier: The carrier of the device
	- custom_recovery_codename: The custom recovery codename of the device
	- custom_recovery_link: The custom recovery link of the device
	- custom_unlock_cmd: The custom unlock command of the device
	- download_boot: The download boot of the device
	- format_on_upgrade: Whether to format on upgrade
	- has_recovery_partition: Whether the device has a recovery partition
	- is_ab_device: Whether the device is an A/B device
	- is_unlockable: Whether the device is unlockable
	- models: The models of the device
	- recovery_boot: The recovery boot of the device
	- required_bootloader: The required bootloader of the device
	- sdcard: The SD card info of the device
	- uses_twrp: Whether the device uses TWRP
	"""
	def __init__(
		self,
		architecture: Union[str, ArchitectureData],
		battery: Optional[Union[BatteryData, Dict[str, BatteryData]]],
		bluetooth: Optional[BluetoothData],
		codename: str,
		cpu: str,
		cpu_cores: Union[int, str],
		cpu_freq: str,
		current_branch: float,
		dimensions: Optional[Union[DimensionData, Dict[str, DimensionData]]],
		gpu: str,
		image: str,
		install_method: str,
		kernel: Optional[KernelData],
		maintainers: List[str],
		name: str,
		network: Optional[Union[List[str], Dict[str, List[str]]]],
		peripherals: Optional[Union[List[str], Dict[str, List[str]]]],
		release: Union[date, Dict[str, date]],
		screen: Optional[Union[ScreenData, Dict[str, ScreenData]]],
		soc: Optional[Union[str, List[str]]],
		tree: str,
		type: str,
		vendor: str,
		vendor_short: str,
		versions: List[float],
		wifi: str,

		before_install: Optional[str] = None,
		before_lineage_install: Optional[str] = None,
		before_recovery_install: Optional[str] = None,
		cameras: Optional[Sequence[CameraData]] = None,
		carrier: Optional[str] = None,
		custom_recovery_codename: Optional[str] = None,
		custom_recovery_link: Optional[str] = None,
		custom_unlock_cmd: Optional[str] = None,
		download_boot: Optional[str] = None,
		format_on_upgrade: Optional[bool] = None,
		has_recovery_partition: Optional[bool] = None,
		is_ab_device: Optional[bool] = None,
		is_unlockable: Optional[bool] = None,
		models: Optional[List[str]] = None,
		recovery_boot: Optional[str] = None,
		required_bootloader: Optional[List[str]] = None,
		sdcard: Optional[SdcardData] = None,
		uses_twrp: Optional[Literal[True]] = None,
	):
		"""Initialize the device information."""
		self.architecture = architecture
		self.battery = battery
		self.bluetooth = bluetooth
		self.codename = codename
		self.cpu = cpu
		self.cpu_cores = cpu_cores
		self.cpu_freq = cpu_freq
		self.current_branch = current_branch
		self.dimensions = dimensions
		self.gpu = gpu
		self.image = image
		self.install_method = install_method
		self.kernel = kernel
		self.maintainers = maintainers
		self.name = name
		self.network = network
		self.peripherals = peripherals
		self.release = release
		self.screen = screen
		self.soc = soc
		self.tree = tree
		self.type = type
		self.vendor = vendor
		self.vendor_short = vendor_short
		self.versions = versions
		self.wifi = wifi

		self.before_install = before_install
		self.before_lineage_install = before_lineage_install
		self.before_recovery_install = before_recovery_install
		self.cameras = cameras
		self.carrier = carrier
		self.custom_recovery_codename = custom_recovery_codename
		self.custom_recovery_link = custom_recovery_link
		self.custom_unlock_cmd = custom_unlock_cmd
		self.download_boot = download_boot
		self.format_on_upgrade = format_on_upgrade
		self.has_recovery_partition = has_recovery_partition
		self.is_ab_device = is_ab_device
		self.is_unlockable = is_unlockable
		self.models = models
		self.recovery_boot = recovery_boot
		self.required_bootloader = required_bootloader
		self.sdcard = sdcard
		self.uses_twrp = uses_twrp

	@classmethod
	def from_dict(cls, data: Dict[str, Any]):
		"""Create a device data object from a dictionary."""
		return cls(
			architecture = ArchitectureData.from_data(data["architecture"]),
			battery = BatteryData.from_data(data["battery"]),
			bluetooth = BluetoothData.from_data(data["bluetooth"]),
			codename = data["codename"],
			cpu = data["cpu"],
			cpu_cores = data["cpu_cores"],
			cpu_freq = data["cpu_freq"],
			current_branch = data["current_branch"],
			dimensions = DimensionData.from_data(data["dimensions"]),
			gpu = data["gpu"],
			image = data["image"],
			install_method = data["install_method"],
			kernel = KernelData.from_data(data["kernel"]),
			maintainers = data["maintainers"],
			name = data["name"],
			network = NetworkData.from_data(data["network"]),
			peripherals = PeripheralsData.from_data(data["peripherals"]),
			release = ReleaseData.from_data(data["release"]),
			screen = ScreenData.from_data(data["screen"]),
			soc = data["soc"],
			tree = data["tree"],
			type = data["type"],
			vendor = data["vendor"],
			vendor_short = data["vendor_short"],
			versions = data["versions"],
			wifi = data["wifi"],

			before_install = data.get("before_install"),
			before_lineage_install = data.get("before_lineage_install"),
			before_recovery_install = data.get("before_recovery_install"),
			cameras = CameraData.from_data(data.get("cameras")),
			carrier = data.get("carrier"),
			custom_recovery_codename = data.get("custom_recovery_codename"),
			custom_recovery_link = data.get("custom_recovery_link"),
			custom_unlock_cmd = data.get("custom_unlock_cmd"),
			download_boot = data.get("download_boot"),
			format_on_upgrade = data.get("format_on_upgrade"),
			has_recovery_partition = data.get("has_recovery_partition"),
			is_ab_device = data.get("is_ab_device"),
			is_unlockable = data.get("is_unlockable"),
			models = data.get("models"),
			recovery_boot = data.get("recovery_boot"),
			required_bootloader = data.get("required_bootloader"),
			sdcard = SdcardData.from_data(data.get("sdcard")),
			uses_twrp = data.get("uses_twrp"),
		)

	@classmethod
	def get_device_data(cls, device: str) -> "DeviceData":
		url = f"https://raw.githubusercontent.com/{GITHUB_ORG}/lineage_wiki/main/_data/devices/{device}.yml"
		response = requests.get(url=url)
		response.raise_for_status()
		return cls.from_dict(yaml.safe_load(response.text))

	def __str__(self) -> str:
		"""Return a string representation of the device data."""
		infos = {
			"Name": self._print_data(self.name),
			"Codename": self._print_data(self.codename),
			"Architecture": self._print_data(self.architecture),
			"Battery": self._print_data(self.battery),
			"Bluetooth": self._print_data(self.bluetooth),
			"CPU": self._print_data(self.cpu),
			"CPU cores": self._print_data(self.cpu_cores),
			"CPU frequency": self._print_data(self.cpu_freq),
			"Dimensions": self._print_data(self.dimensions),
			"GPU": self._print_data(self.gpu),
			"Kernel": self._print_data(self.kernel),
			"Maintainers": ", ".join(self.maintainers) if self.maintainers else "None (unmaintained)",
			"Peripherals": self._print_data(self.peripherals),
			"Release": self._print_data(self.release),
			"Screen": self._print_data(self.screen),
			"SoC": self._print_data(self.soc),
			"Device tree repository": f'{GITHUB_ORG_URL}/{self.tree}',
			"Type": self._print_data(self.type),
			"Vendor": self._print_data(self.vendor),
			"Vendor (short)": self._print_data(self.vendor_short),
			"Versions": self._print_data(self.versions),
		}

		opt_infos = {
			key: value for key, value in {
				"Cameras": self._print_data(self.cameras),
				"Carrier": self._print_data(self.carrier),
				"Custom recovery codename": self._print_data(self.custom_recovery_codename),
				"Custom recovery link": self._print_data(self.custom_recovery_link),
				"Custom unlock command": self._print_data(self.custom_unlock_cmd),
				"Download boot": self._print_data(self.download_boot),
				"Format on upgrade": self._print_data(self.format_on_upgrade),
				"Has recovery partition": self._print_data(self.has_recovery_partition),
				"Is A/B device": self._print_data(self.is_ab_device),
				"Is unlockable": self._print_data(self.is_unlockable),
				"Models": ", ".join(self.models) if isinstance(self.models, list) else self.models,
				"Network": self._print_data(self.network),
				"Recovery boot": self._print_data(self.recovery_boot),
				"Required bootloader": self._print_data(self.required_bootloader),
				"SD card": self._print_data(self.sdcard),
				"Uses TWRP": self._print_data(self.uses_twrp),
			}.items()
			if value is not None
		}

		return "\n".join([f"{key}: {value}" for key, value in {
			**infos,
			**opt_infos,
		}.items()])

	@staticmethod
	def _print_data(data: Optional[Union[Any, List[Any], List[Dict[str, Any]]]]) -> str:
		"""Return a string representation of the data."""
		if isinstance(data, list):
			if len(data) > 0 and isinstance(data[0], dict):
				return "".join([
					f"\n- {device}: {str(value)}"
					for d in data
					for device, value in d.items()
				])
			elif len(data) > 0 and isinstance(data[0], (complex, float, int, str)):
				return ", ".join([str(value) for value in data])
			else:
				return "".join([f"\n - {value}" for value in data])
		elif isinstance(data, dict):
			return "".join([f"\n - {device}: {str(value)}" for device, value in data.items()])
		else:
			return str(data)
