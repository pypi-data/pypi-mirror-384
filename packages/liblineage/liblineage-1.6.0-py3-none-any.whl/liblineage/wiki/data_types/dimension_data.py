#
# Copyright (C) 2022 The LineageOS Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#

from typing import Dict, List, Optional, Union

from liblineage.wiki.data_types.base_data import BaseData

class DimensionData(BaseData):
	"""LineageOS dimension information.

	Attributes:
	- height: The height
	- width: The width
	- depth: The depth
	"""
	def __init__(
		self,
		height: str,
		width: str,
		depth: str,
	):
		"""Initialize the dimension information."""
		super().__init__()

		self.height = height
		self.width = width
		self.depth = depth

	@classmethod
	def from_data(cls, data: Optional[Union[Dict, List, str]]) -> Optional[Union["DimensionData", Dict[str, "DimensionData"]]]:
		"""Create a dimension information object from YAML data."""
		if data is None:
			dimensions = None
		elif isinstance(data, dict):
			dimensions = cls.from_dict(data)
		elif isinstance(data, list):
			dimensions = {}
			for dim_data in data:
				device, dim = list(dim_data.items())[0]
				dimensions[device] = cls.from_dict(dim)
		elif isinstance(data, str) and data == "None":
			dimensions = None
		else:
			raise Exception("Invalid dimensions data")

		return dimensions
