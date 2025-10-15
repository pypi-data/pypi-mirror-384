#
# Copyright (C) 2022 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from typing import Dict, List, Optional

from liblineage.wiki.data_types.base_data import BaseData

class BluetoothData(BaseData):
	"""LineageOS Bluetooth information.

	Attributes:
	- spec: Bluetooth specification
	- profiles: Bluetooth profile
	"""
	def __init__(
		self,
		spec: str,
		profiles: Optional[List[str]] = None,
	):
		"""Initialize the Bluetooth information."""
		super().__init__()

		self.spec = spec
		self.profiles = profiles or []

	@classmethod
	def from_data(cls, data: Optional[Dict]) -> Optional["BluetoothData"]:
		"""Create a Bluetooth information object from YAML data."""
		if data is None:
			bluetooth = None
		elif isinstance(data, dict):
			bluetooth = cls.from_dict(data)
		else:
			raise Exception("Invalid Bluetooth data")

		return bluetooth
