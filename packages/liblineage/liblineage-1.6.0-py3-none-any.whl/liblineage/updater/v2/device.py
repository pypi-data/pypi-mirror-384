#
# Copyright (C) 2023 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from typing import Any, Dict, List

class Device:
	"""LineageOS device informations.

	Attributes:
	- name (str): The name of the device
	- model (str): The model name of the device
	- oem (str): The OEM name
	- info_url (str): The URL of the device information page
	- versions (list[str]): The LineageOS versions for this device (e.g. 18.1)
	- dependencies (list[str]): The list of repositories used to build this device
	"""
	def __init__(
		self,
		name: str,
		model: str,
		oem: str,
		info_url: str,
		versions: List[str],
		dependencies: List[str],
	) -> None:
		self.name = name
		self.model = model
		self.oem = oem
		self.info_url = info_url
		self.versions = versions
		self.dependencies = dependencies

	@classmethod
	def from_json(cls, json: Dict[str, Any]):
		"""Create an object from a JSON object."""
		return cls(
			json["name"],
			json["model"],
			json["oem"],
			json["info_url"],
			json["versions"],
			json["dependencies"],
		)
