#
# Copyright (C) 2023 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from liblineage.updater.v2.oem_device import OemDevice
from typing import Any, Dict

class Oem:
	"""LineageOS OEM informations.

	Attributes:
	- name (datetime): The name of the device
	- devices (list[OemDevice]): The list of supported devices from this OEM
	"""
	def __init__(
		self,
		name: str,
		devices: list[OemDevice],
	) -> None:
		self.name = name
		self.devices = devices

	@classmethod
	def from_json(cls, json: Dict[str, Any]):
		"""Create an object from a JSON object."""
		return cls(
			json["name"],
			[OemDevice.from_json(device) for device in json["devices"]],
		)
