#
# Copyright (C) 2022 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from typing import Dict, List, Optional, Sequence

from liblineage.wiki.data_types.base_data import BaseData

class CameraData(BaseData):
	"""The format for the camera property.

	Attributes:
	- info: The camera info (in MP)
	- flash: Flash unit info
	"""
	def __init__(
		self,
		info: str,
		flash: str,
	):
		"""Initialize the camera information."""
		super().__init__()

		self.info = info
		self.flash = flash

	@classmethod
	def from_data(cls, data: Optional[List[Dict]]) -> Optional[Sequence["CameraData"]]:
		"""Create a camera information object from YAML data."""
		if data is None:
			camera = None
		elif isinstance(data, list):
			camera = [cls.from_dict(camera_data) for camera_data in data]
		else:
			raise Exception("Invalid camera data")

		return camera
