#
# Copyright (C) 2023 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from typing import Any, Dict

class OemDevice:
	"""LineageOS OEM's device informations.

	Attributes:
	- name (str): The name of the device
	- model (str): The model name of the device
	"""
	def __init__(
		self,
		name: str,
		model: str,
	) -> None:
		self.name = name
		self.model = model

	@classmethod
	def from_json(cls, json: Dict[str, Any]):
		"""Create an object from a JSON object."""
		return cls(
			json["name"],
			json["model"],
		)
