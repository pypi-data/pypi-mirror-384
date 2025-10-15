#
# Copyright (C) 2022-2023 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from typing import Dict, List, Optional, Union

from liblineage.wiki.data_types.base_data import BaseData

class ScreenData(BaseData):
	"""LineageOS screen information.

	Attributes:
	- size: The screen size (inches)
	- resolution: The screen resolution (e.g. 1080x1920)
	- technology: The screen technology (e.g. LCD)
	- refresh_rate: Maximum screen refresh rate (Hz)
	"""
	def __init__(
		self,
		size: str,
		resolution: str,
		technology: str,
		refresh_rate: Optional[int] = None,
	):
		"""Initialize the screen information."""
		super().__init__()

		self.size = size
		self.resolution = resolution
		self.technology = technology
		self.refresh_rate = refresh_rate

	@classmethod
	def from_data(cls, data: Optional[Union[Dict, List, str]]) -> Optional[Union["ScreenData", Dict[str, "ScreenData"]]]:
		"""Create a screen information object from YAML data."""
		if data is None:
			screen = None
		elif isinstance(data, dict):
			screen = cls.from_dict(data)
		elif isinstance(data, list):
			screen = {}
			for scr in data:
				device, screen_data = list(scr.items())[0]
				screen[device] = cls.from_dict(screen_data)
		elif isinstance(data, str) and data == "None":
			screen = None
		else:
			raise Exception("Invalid screen data")

		return screen
