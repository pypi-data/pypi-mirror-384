#
# Copyright (C) 2022 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from typing import Dict, Optional

from liblineage.wiki.data_types.base_data import BaseData

class SdcardData(BaseData):
	"""The format required for the sdcard property.

	Attributes:
	- size_max: Maximum size for a sdcard
	- slot: where the sdcard is inserted
	"""
	def __init__(
		self,
		size_max: str,
		slot: Optional[str] = None,
	):
		"""Initialize the sdcard information."""
		super().__init__()

		self.size_max = size_max
		self.slot = slot

	@classmethod
	def from_data(cls, data: Optional[Dict]) -> Optional["SdcardData"]:
		"""Create a sdcard information object from YAML data."""
		if data is None:
			sdcard = None
		elif isinstance(data, dict):
			sdcard = cls.from_dict(data)
		else:
			raise Exception("Invalid sdcard data")

		return sdcard
